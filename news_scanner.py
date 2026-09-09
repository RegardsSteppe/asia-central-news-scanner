from __future__ import annotations

import argparse
import os
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from stop_words import get_stop_words
except ImportError:  # pragma: no cover - library not installed
    get_stop_words = None

from sources import SOURCES
from scoring import classify_article
from html_template import create_web_page

from text_utils import (
    article_date_timestamp,
    clean_title,
)

from http_utils import fetch_url

from article_ingestion import (
    CACHE_TTL,
    HEADERS,
    REQUEST_TIMEOUT,
    build_article,
    diagnose_source_content,
    extract_body,
    extract_links_from_html,
    parse_rss,
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MEMORY_FILE = BASE_DIR / "memory.json"
OUTPUT_FILE = BASE_DIR / "index.html"
CSV_OUTPUT_FILE = BASE_DIR / "articles.csv"

ENRICH_LIMIT = 80
VOCABULARY_LIMIT = 300
FETCH_WORKERS = max(
    1,
    int(os.getenv("SCANNER_FETCH_WORKERS", "6")),
)
ENRICH_WORKERS = max(
    1,
    int(os.getenv("SCANNER_ENRICH_WORKERS", "4")),
)
SKIP_PREVIOUSLY_SEEN = os.getenv(
    "SCANNER_SKIP_PREVIOUSLY_SEEN",
    "1",
).strip().lower() not in {"0", "false", "no"}
MAX_PERSISTED_SEEN_KEYS = max(
    100,
    int(os.getenv("SCANNER_MAX_PERSISTED_SEEN_KEYS", "5000")),
)

# Small, hand-picked list kept as a safety net in case the "stop-words"
# library is not installed or fails to load its corpus for some reason.
_FALLBACK_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "are",
    "has",
    "have",
    "into",
    "about",
    "after",
    "before",
    "their",
    "they",
    "will",
    "you",
    "your",
    "how",
    "why",
    "what",
    "who",
    "что",
    "как",
    "для",
    "это",
    "после",
    "перед",
    "из",
    "в",
    "на",
    "и",
    "с",
    "по",
    "не",
    "к",
    "о",
}

# Terms specific to this project's news-title vocabulary that generic
# stopword corpora don't cover.
_EXTRA_STOPWORDS = {
    "new",
    "central",
    "asia",
}


def _load_stopwords() -> set[str]:
    words: set[str] = set(_FALLBACK_STOPWORDS)

    if get_stop_words is not None:
        for language in ("en", "ru"):
            try:
                words |= set(get_stop_words(language))
            except Exception:
                continue

    return words | _EXTRA_STOPWORDS


STOPWORDS = _load_stopwords()


# ============================================================
# DÉDUPLICATION
# ============================================================

def canonical_article_key(
    article: dict[str, Any],
) -> str:

    url = article.get("url", "")

    if url:
        parsed = urlparse(url)

        return (
            parsed.netloc.lower()
            + parsed.path.rstrip("/").lower()
        )

    title = clean_title(
        article.get("title", "")
    ).lower()

    title = re.sub(
        r"[^\w\s]",
        " ",
        title,
    )

    title = re.sub(
        r"\s+",
        " ",
        title,
    )

    return title.strip()


def deduplicate(
    articles: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    result = []
    seen = set()

    for article in articles:
        key = canonical_article_key(article)

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        result.append(article)

    return result


# ============================================================
# VOCABULAIRE DES TITRES
# ============================================================

def build_title_vocabulary(
    articles: list[dict[str, Any]],
    limit: int = VOCABULARY_LIMIT,
) -> list[dict[str, Any]]:

    counts: dict[str, int] = {}

    for article in articles:
        title = clean_title(
            article.get("title", "")
        ).lower()

        words = re.findall(
            r"[^\W\d_][\w'-]{2,}",
            title,
            flags=re.UNICODE,
        )

        for word in words:
            word = word.strip("-'")

            if not word:
                continue

            if word in STOPWORDS:
                continue

            counts[word] = (
                counts.get(word, 0) + 1
            )

    vocabulary = [
        {
            "word": word,
            "count": count,
        }
        for word, count in counts.items()
    ]

    vocabulary.sort(
        key=lambda item: (
            -item["count"],
            item["word"],
        )
    )

    return vocabulary[:limit]


# ============================================================
# MÉMOIRE OPTIONNELLE
# ============================================================

def safe_load_memory() -> dict[str, Any]:
    if not MEMORY_FILE.exists():
        return {}

    try:
        with MEMORY_FILE.open(
            "r",
            encoding="utf-8",
        ) as handle:
            data = json.load(handle)

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {}


def safe_save_memory(
    memory: dict[str, Any],
) -> None:

    try:
        with MEMORY_FILE.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                memory,
                handle,
                ensure_ascii=False,
                indent=2,
            )

    except Exception:
        pass


def show_memory() -> dict[str, Any]:
    memory = safe_load_memory()

    if not memory:
        print(
            "MEMORY | vide — ignorée"
        )
    else:
        print(
            f"MEMORY | {len(memory)} éléments"
        )

    return memory


def load_seen_keys(memory: dict[str, Any]) -> set[str]:
    seen = memory.get("seen_article_keys", [])
    if not isinstance(seen, list):
        return set()
    return {
        key
        for key in seen
        if isinstance(key, str) and key
    }


def save_seen_keys(
    memory: dict[str, Any],
    seen_keys: set[str],
) -> None:
    existing = memory.get("seen_article_keys", [])
    if not isinstance(existing, list):
        existing = []

    ordered = [
        key
        for key in existing
        if isinstance(key, str) and key
    ]
    ordered.extend(sorted(seen_keys))
    deduped = list(dict.fromkeys(ordered))
    memory["seen_article_keys"] = deduped[-MAX_PERSISTED_SEEN_KEYS:]
    safe_save_memory(memory)


def timed_call(label: str, func: Any, *args: Any, **kwargs: Any) -> Any:
    started = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - started
    print(f"PERF | {label} | {elapsed:.2f}s")
    return result


# ============================================================
# ENRICHISSEMENT
# ============================================================

def enrich_articles(
    articles: list[dict[str, Any]],
    force_refresh: bool = False,
) -> None:

    ranked = sorted(
        articles,
        key=lambda article: (
            article.get("score", 0),
            article_date_timestamp(article),
        ),
        reverse=True,
    )

    selected = ranked[:ENRICH_LIMIT]

    print(
        f"ENRICH | {len(selected)} articles avec body complet"
    )

    source_by_name = {
        source.get("name"): source
        for source in SOURCES
    }

    def _enrich_article(article: dict[str, Any]) -> str:
        return extract_body(
            article["url"],
            source_by_name.get(article.get("source"), {}),
            force_refresh=force_refresh,
        )

    done = 0
    with ThreadPoolExecutor(
        max_workers=min(ENRICH_WORKERS, len(selected) or 1)
    ) as executor:
        futures = {
            executor.submit(_enrich_article, article): article
            for article in selected
        }

        for future in as_completed(futures):
            article = futures[future]
            try:
                body = future.result()
            except Exception as exc:
                print(
                    f"WARNING | {article.get('source')} | ENRICH ERROR | {exc}"
                )
                body = ""

            if body:
                article["body"] = body

            classify_article(article)

            done += 1
            if done % 10 == 0:
                print(
                    f"ENRICH | {done}/{len(selected)}"
                )


# ============================================================
# STATISTIQUES
# ============================================================

def build_stats(
    articles: list[dict[str, Any]],
    sources_successful: int = 0,
    sources_total: int = 0,
) -> dict[str, Any]:

    scores = [
        float(article.get("score", 0) or 0)
        for article in articles
    ]

    levels = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    }

    relevant = 0

    for article in articles:
        level = article.get(
            "level",
            "D",
        )

        if level in levels:
            levels[level] += 1

        if article.get("relevant"):
            relevant += 1

    average = (
        sum(scores) / len(scores)
        if scores
        else 0
    )

    relevance_rate = (
        (relevant / len(articles)) * 100
        if articles
        else 0
    )

    return {
        "analyzed": len(articles),
        "retained": relevant,
        "avg_score": round(
            average,
            1,
        ),
        "level_a": levels["A"],
        "level_b": levels["B"],
        "level_c": levels["C"],
        "level_d": levels["D"],
        "sources_successful": sources_successful,
        "sources_total": sources_total,
        "relevance_rate": round(
            relevance_rate,
            1,
        ),
    }


# ============================================================
# AUDIT
# ============================================================

def build_audit(
    articles: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    audit = []

    for article in articles:
        audit.append(
            {
                "title": article.get(
                    "title",
                    "",
                ),
                "source": article.get(
                    "source",
                    "",
                ),
                "score": article.get(
                    "score",
                    0,
                ),
                "level": article.get(
                    "level",
                    "D",
                ),
                "relevant": article.get(
                    "relevant",
                    False,
                ),
                "signals": article.get(
                    "signals",
                    {},
                ),
            }
        )

    return audit


def keywords_used(article: dict[str, Any]) -> list[str]:
    """Return the distinct keyword matches recorded by the scorer."""
    result: list[str] = []
    seen: set[str] = set()

    for value in (article.get("signals") or {}).values():
        if not isinstance(value, list):
            continue

        for keyword in value:
            if not isinstance(keyword, str) or keyword in seen:
                continue
            seen.add(keyword)
            result.append(keyword)

    return result


def build_csv_rows(
    articles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build flat rows containing article data and scoring details."""
    score_fields = (
        "geography_score",
        "target_score",
        "repression_score",
        "rights_score",
        "journalism_score",
        "geopolitical_score",
        "freshness_score",
    )
    rows = []

    for article in articles:
        date = article.get("date")
        signals = article.get("signals") or {}
        row: dict[str, Any] = {
            "date": date.isoformat() if hasattr(date, "isoformat") else date or "",
            "source": article.get("source", ""),
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "summary": article.get("summary", ""),
            "score": article.get("score", 0),
            "level": article.get("level", "D"),
            "priority": article.get("priority", ""),
            "relevant": article.get("relevant", False),
            "theme": article.get("theme", ""),
            "keywords": "; ".join(keywords_used(article)),
            "reasons": "; ".join(article.get("reasons") or []),
        }
        row.update(
            {
                field: signals.get(field, 0)
                for field in score_fields
            }
        )
        rows.append(row)

    return rows


def export_csv(articles: list[dict[str, Any]]) -> None:
    """Write the complete scan, including scores and matched keywords."""
    rows = build_csv_rows(articles)
    fieldnames = [
        "date",
        "source",
        "title",
        "url",
        "summary",
        "score",
        "level",
        "priority",
        "relevant",
        "theme",
        "keywords",
        "reasons",
        "geography_score",
        "target_score",
        "repression_score",
        "rights_score",
        "journalism_score",
        "geopolitical_score",
        "freshness_score",
    ]

    with CSV_OUTPUT_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV | {CSV_OUTPUT_FILE.name} créé | {len(rows)} articles")


# ============================================================
# SCAN
# ============================================================

def collect_articles(
    force_refresh: bool = False,
    seen_keys: set[str] | None = None,
) -> tuple[list[dict[str, Any]], int, int, int]:
    """
    Parcourt toutes les sources configurées, récupère leur contenu
    et en extrait les articles bruts (non dédupliqués, non scorés).

    Retourne (articles, sources_successful, sources_total).
    """

    sources_total = len(SOURCES)
    preload_seen = seen_keys or set()

    def _collect_one(
        source_index: int,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        name = source.get(
            "name",
            "Unknown",
        )

        url = source.get(
            "url",
            "",
        )

        if not url:
            return {
                "index": source_index,
                "name": name,
                "ok": False,
                "articles": [],
                "error": "URL absente",
                "fetch_time": 0.0,
                "parse_time": 0.0,
                "total_time": 0.0,
            }

        try:
            source_started = time.perf_counter()
            fetch_started = time.perf_counter()
            content = fetch_url(
                url,
                headers=HEADERS,
                request_timeout=REQUEST_TIMEOUT,
                cache_ttl=CACHE_TTL,
                force_refresh=force_refresh,
            )
            fetch_elapsed = time.perf_counter() - fetch_started
            diagnose_source_content(source, content, url)

            source_type = str(
                source.get(
                    "type",
                    "rss",
                )
            ).lower()

            parse_started = time.perf_counter()
            if source_type in {
                "rss",
                "feed",
                "atom",
            }:
                articles = parse_rss(
                    content,
                    source,
                )
            else:
                articles = extract_links_from_html(
                    content,
                    url,
                    source,
                )
            parse_elapsed = time.perf_counter() - parse_started

            return {
                "index": source_index,
                "name": name,
                "ok": True,
                "articles": articles,
                "error": "",
                "fetch_time": fetch_elapsed,
                "parse_time": parse_elapsed,
                "total_time": time.perf_counter() - source_started,
            }

        except Exception as exc:
            return {
                "index": source_index,
                "name": name,
                "ok": False,
                "articles": [],
                "error": str(exc),
                "fetch_time": 0.0,
                "parse_time": 0.0,
                "total_time": 0.0,
            }

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(
        max_workers=min(FETCH_WORKERS, sources_total or 1)
    ) as executor:
        futures = [
            executor.submit(_collect_one, index, source)
            for index, source in enumerate(SOURCES)
        ]

        for future in as_completed(futures):
            results.append(future.result())

    all_articles: list[dict[str, Any]] = []
    sources_successful = 0
    skipped_previously_seen = 0
    run_seen: set[str] = set()
    for result in sorted(results, key=lambda item: item["index"]):
        name = result["name"]
        if not result["ok"]:
            print(
                f"WARNING | {name} | ERROR | {result['error']}"
            )
            continue

        sources_successful += 1
        articles = result["articles"]
        accepted = 0
        for article in articles:
            key = canonical_article_key(article)
            if not key:
                continue
            if key in run_seen:
                continue
            if key in preload_seen:
                skipped_previously_seen += 1
                continue
            run_seen.add(key)
            all_articles.append(article)
            accepted += 1

        print(
            f"SOURCE | {name} | {accepted}/{len(articles)} articles | "
            f"fetch={result['fetch_time']:.2f}s parse={result['parse_time']:.2f}s total={result['total_time']:.2f}s"
        )

    return all_articles, sources_successful, sources_total, skipped_previously_seen


def score_first_pass(
    articles: list[dict[str, Any]],
) -> None:
    """
    Premier passage de scoring sur titre + résumé uniquement
    (avant enrichissement du corps de l'article).
    """

    print(
        "SCORING | première passe title + summary"
    )

    for article in articles:
        article["body"] = ""
        classify_article(article)


def export_html(
    articles: list[dict[str, Any]],
    audit: list[dict[str, Any]],
    stats: dict[str, Any],
    vocabulary: list[dict[str, Any]],
) -> None:
    """
    Génère et écrit index.html. Toute erreur est journalisée puis
    relancée pour que le workflow GitHub ne masque pas le problème.
    """

    print(
        "HTML | génération de index.html"
    )

    try:
        html_output = create_web_page(
            articles=articles,
            audit=audit,
            stats=stats,
            title_words=vocabulary,
        )

        if not isinstance(
            html_output,
            str,
        ):
            raise TypeError(
                "create_web_page() n'a pas retourné une chaîne HTML"
            )

        OUTPUT_FILE.write_text(
            html_output,
            encoding="utf-8",
        )

        if OUTPUT_FILE.exists():
            size = OUTPUT_FILE.stat().st_size

            print(
                f"HTML | index.html créé | {size} octets"
            )
        else:
            print(
                "ERROR | index.html n'a pas été créé"
            )

    except Exception as exc:
        print(
            f"ERROR | HTML | {type(exc).__name__}: {exc}"
        )

        raise


def run_scan(
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    started_total = time.perf_counter()
    memory = show_memory()
    seen_keys = (
        load_seen_keys(memory)
        if SKIP_PREVIOUSLY_SEEN
        else set()
    )

    print(
        f"SOURCES | {len(SOURCES)} sources actives"
    )
    print(
        f"PERF | CONFIG | fetch_workers={FETCH_WORKERS} enrich_workers={ENRICH_WORKERS} timeout={REQUEST_TIMEOUT}s retries={os.getenv('SCANNER_HTTP_MAX_ATTEMPTS', '3')}"
    )

    all_articles, sources_successful, sources_total, skipped_previously_seen = timed_call(
        "fetch+parse",
        collect_articles,
        force_refresh=force_refresh,
        seen_keys=seen_keys,
    )

    print(
        f"COLLECT | {len(all_articles)} articles avant déduplication"
    )
    if skipped_previously_seen:
        print(
            f"DEDUP | {skipped_previously_seen} articles déjà traités ignorés"
        )

    all_articles = timed_call(
        "deduplicate",
        deduplicate,
        all_articles
    )

    print(
        f"COLLECT | {len(all_articles)} articles récupérés"
    )

    print(
        f"DEDUP | {len(all_articles)} articles uniques"
    )

    # --------------------------------------------------------
    # Première passe : titre + résumé uniquement
    # --------------------------------------------------------

    timed_call(
        "score-first-pass",
        score_first_pass,
        all_articles,
    )

    # --------------------------------------------------------
    # Vocabulaire
    # --------------------------------------------------------

    vocabulary = timed_call(
        "vocabulary",
        build_title_vocabulary,
        all_articles,
    )

    print(
        f"VOCABULARY | {len(vocabulary)} mots de titres"
    )

    # --------------------------------------------------------
    # Deuxième passe : body sur les meilleurs
    # --------------------------------------------------------

    timed_call(
        "enrichment",
        enrich_articles,
        all_articles,
        force_refresh=force_refresh,
    )

    # --------------------------------------------------------
    # Tri final
    # --------------------------------------------------------

    timed_call(
        "sort-final",
        all_articles.sort,
        key=lambda article: (
            bool(article.get("relevant")),
            article.get("score", 0),
            article_date_timestamp(article),
        ),
        reverse=True,
    )

    # --------------------------------------------------------
    # Stats
    # --------------------------------------------------------

    stats = timed_call(
        "build-stats",
        build_stats,
        all_articles,
        sources_successful=sources_successful,
        sources_total=sources_total,
    )

    audit = timed_call(
        "build-audit",
        build_audit,
        all_articles
    )

    print(
        "STATS | "
        f"analyzed={stats['analyzed']} | "
        f"retained={stats['retained']} | "
        f"avg={stats['avg_score']}/100"
    )

    print(
        "LEVELS | "
        f"A={stats['level_a']} "
        f"B={stats['level_b']} "
        f"C={stats['level_c']} "
        f"D={stats['level_d']}"
    )

    # --------------------------------------------------------
    # Génération HTML
    # --------------------------------------------------------

    timed_call(
        "export-html",
        export_html,
        all_articles,
        audit,
        stats,
        vocabulary,
    )
    timed_call(
        "export-csv",
        export_csv,
        all_articles,
    )

    if SKIP_PREVIOUSLY_SEEN:
        save_seen_keys(
            memory,
            {
                canonical_article_key(article)
                for article in all_articles
                if canonical_article_key(article)
            },
        )
        print("MEMORY | seen_article_keys mis à jour")

    print(
        f"PERF | total-runtime | {time.perf_counter() - started_total:.2f}s"
    )

    return all_articles


# ============================================================
# CLI
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Central Asia News Scanner"
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help="Force une nouvelle récupération des sources.",
    )

    args = parser.parse_args()

    try:
        articles = run_scan(
            force_refresh=args.scan
        )

        selected = [
            article
            for article in articles
            if article.get("relevant")
        ]

        print(
            f"SCAN | terminé | "
            f"{len(selected)} articles sélectionnés"
        )

    except Exception as exc:
        print(
            f"SCAN | erreur fatale | "
            f"{type(exc).__name__}: {exc}"
        )

        raise


if __name__ == "__main__":
    main()
