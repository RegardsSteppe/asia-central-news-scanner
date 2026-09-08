from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

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

ENRICH_LIMIT = 80
VOCABULARY_LIMIT = 300


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

    stopwords = {
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
        "new",
        "central",
        "asia",
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

            if word in stopwords:
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

    for index, article in enumerate(
        selected,
        1,
    ):
        try:
            body = extract_body(
                article["url"],
                next(
                    (
                        source
                        for source in SOURCES
                        if source.get("name")
                        == article.get("source")
                    ),
                    {},
                ),
                force_refresh=force_refresh,
            )
        except Exception as exc:
            print(
                f"WARNING | {article.get('source')} | ENRICH ERROR | {exc}"
            )
            body = ""

        if body:
            article["body"] = body

        # Re-score après enrichissement.
        classify_article(article)

        if index % 10 == 0:
            print(
                f"ENRICH | {index}/{len(selected)}"
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


# ============================================================
# SCAN
# ============================================================

def collect_articles(
    force_refresh: bool = False,
) -> tuple[list[dict[str, Any]], int, int]:
    """
    Parcourt toutes les sources configurées, récupère leur contenu
    et en extrait les articles bruts (non dédupliqués, non scorés).

    Retourne (articles, sources_successful, sources_total).
    """

    all_articles: list[dict[str, Any]] = []

    sources_successful = 0
    sources_total = len(SOURCES)

    for source in SOURCES:
        name = source.get(
            "name",
            "Unknown",
        )

        url = source.get(
            "url",
            "",
        )

        if not url:
            print(
                f"WARNING | {name} | URL absente"
            )
            continue

        try:
            content = fetch_url(
                url,
                headers=HEADERS,
                request_timeout=REQUEST_TIMEOUT,
                cache_ttl=CACHE_TTL,
                force_refresh=force_refresh,
            )
            diagnose_source_content(source, content, url)

            source_type = str(
                source.get(
                    "type",
                    "rss",
                )
            ).lower()

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

            print(
                f"SOURCE | {name} | "
                f"{len(articles)} articles"
            )

            sources_successful += 1

            all_articles.extend(articles)

        except Exception as exc:
            print(
                f"WARNING | {name} | ERROR | {exc}"
            )

    return all_articles, sources_successful, sources_total


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

    show_memory()

    print(
        f"SOURCES | {len(SOURCES)} sources actives"
    )

    all_articles, sources_successful, sources_total = collect_articles(
        force_refresh=force_refresh
    )

    print(
        f"COLLECT | {len(all_articles)} articles avant déduplication"
    )

    all_articles = deduplicate(
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

    score_first_pass(all_articles)

    # --------------------------------------------------------
    # Vocabulaire
    # --------------------------------------------------------

    vocabulary = build_title_vocabulary(
        all_articles
    )

    print(
        f"VOCABULARY | {len(vocabulary)} mots de titres"
    )

    # --------------------------------------------------------
    # Deuxième passe : body sur les meilleurs
    # --------------------------------------------------------

    enrich_articles(
        all_articles,
        force_refresh=force_refresh,
    )

    # --------------------------------------------------------
    # Tri final
    # --------------------------------------------------------

    all_articles.sort(
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

    stats = build_stats(
        all_articles,
        sources_successful=sources_successful,
        sources_total=sources_total,
    )

    audit = build_audit(
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

    export_html(
        all_articles,
        audit,
        stats,
        vocabulary,
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
