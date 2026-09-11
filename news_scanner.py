from __future__ import annotations

import argparse
import os
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from stop_words import get_stop_words
except ImportError:  # pragma: no cover - library not installed
    get_stop_words = None

from sources import SOURCES, PROFILE_GROUPS
from scoring import classify_article
from html_template import create_web_page
from synthesis import generate_synthesis

from text_utils import (
    article_date_timestamp,
    clean_title,
    parse_date,
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

# Sources sur ces profils sont le cœur éditorial du projet (droits
# humains, liberté de la presse, investigation, médias internationaux
# indépendants dédiés à la région comme Al Jazeera/AP par pays) : on
# leur garantit des créneaux d'enrichissement dédiés par SOURCE,
# indépendants du classement par score-titre général. Sans ça, un
# article régional précis (ex : une condamnation nommément visée, ou
# une page Al Jazeera par pays qui ne produit que quelques articles/
# run) peut se faire noyer — soit par le volume d'une source
# généraliste hors de ce groupe, soit même par une AUTRE source de ce
# même groupe (ex : HRW déverse des centaines d'articles/run via son
# contournement Google News et écraserait un pool partagé) — et ne
# jamais recevoir son corps complet, donc rester sans date/plafonné à
# un score titre-seul pour toujours. La garantie est donc par source,
# pas par un pool commun au groupe.
PRIORITY_ENRICH_PROFILES = {
    "human_rights",
    "press_freedom",
    "investigative",
    "international_independent",
}
ENRICH_PER_SOURCE_LIMIT = max(
    0,
    int(os.getenv("SCANNER_ENRICH_PER_SOURCE_LIMIT", "15")),
)
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

# Nom de source -> catégorie d'affichage (voir PROFILE_GROUPS dans
# sources.py). Sert uniquement à regrouper la table d'audit dans le
# HTML — n'influence jamais le scoring.
SOURCE_NAME_TO_GROUP = {
    source["name"]: PROFILE_GROUPS.get(source["profile"], "Autres")
    for source in SOURCES
}

# Durée pendant laquelle une source scannée avec succès n'est pas
# re-scannée (mémoire par source, persistée dans memory.json). 2h par défaut.
SOURCE_MIN_INTERVAL_SECONDS = max(
    0,
    int(os.getenv("SCANNER_SOURCE_MIN_INTERVAL", str(2 * 3600))),
)

# Nombre maximal d'articles conservés par source dans le cache mémoire
# (pour ne pas faire grossir memory.json indéfiniment).
MAX_CACHED_ARTICLES_PER_SOURCE = max(
    10,
    int(os.getenv("SCANNER_MAX_CACHED_ARTICLES_PER_SOURCE", "250")),
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
    "les",
    "des",
    "une",
    "un",
    "le",
    "la",
    "du",
    "de",
    "et",
    "que",
    "qui",
    "pour",
    "dans",
    "sur",
    "avec",
    "pas",
    "plus",
    "son",
    "sa",
    "ses",
    "par",
    "au",
    "aux",
    "ce",
    "cette",
    "ces",
}

# Terms specific to this project's news-title vocabulary that generic
# stopword corpora don't cover.
_EXTRA_STOPWORDS = {
    "new",
    "central",
    "asia",
    "utc",

    # Mois russes : très fréquents dans les titres ("15 сентября"...)
    # mais sans aucun signal thématique.
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",

    # Farsi : quelques mots-outils/verbes fréquents absents du corpus
    # "persian" de la librairie stop-words (variantes d'écriture de
    # میشود/است, ou verbes auxiliaires très courants).
    "می‌شود", "میشود", "شود", "می‌کند", "کرد", "کند", "بود", "ادعای",
}


def _load_stopwords() -> set[str]:
    words: set[str] = set(_FALLBACK_STOPWORDS)

    if get_stop_words is not None:
        for language in ("en", "ru", "fa", "fr"):
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

        key = (
            parsed.netloc.lower()
            + parsed.path.rstrip("/").lower()
        )

        # La query string est conservée (après nettoyage des paramètres
        # de tracking par normalize_url en amont) : certains sites
        # identifient l'article uniquement via un paramètre (?id=123),
        # et l'ignorer ferait passer des articles différents pour des
        # doublons.
        if parsed.query:
            key += "?" + parsed.query

        return key

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


def update_seen_keys(
    memory: dict[str, Any],
    seen_keys: set[str],
) -> None:
    """Met à jour memory['seen_article_keys'] en mémoire (pas d'I/O)."""
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


# ============================================================
# MÉMOIRE PAR SOURCE (éviter de re-scanner une source trop souvent)
# ============================================================

def _serialize_cached_article(
    article: dict[str, Any],
) -> dict[str, Any]:
    """Version compacte et JSON-sérialisable d'un article, pour le cache
    par source. On ne garde jamais le corps complet (trop volumineux)."""
    date = article.get("date")
    return {
        "source": article.get("source", ""),
        "source_label": article.get("source_label", ""),
        "title": article.get("title", ""),
        "summary": article.get("summary", ""),
        "url": article.get("url", ""),
        "date": date.isoformat() if hasattr(date, "isoformat") else date,
    }


def _deserialize_cached_article(
    cached: dict[str, Any],
) -> dict[str, Any]:
    article = dict(cached)
    article["date"] = parse_date(article.get("date"))
    article["body"] = ""
    return article


def load_source_cache(
    memory: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    sources = memory.get("sources")
    return sources if isinstance(sources, dict) else {}


def get_fresh_cached_articles(
    source_cache: dict[str, dict[str, Any]],
    name: str,
    now: float,
) -> list[dict[str, Any]] | None:
    """
    Retourne les articles en cache pour une source si elle a été
    scannée avec succès il y a moins de SOURCE_MIN_INTERVAL_SECONDS,
    sinon None (il faut re-scanner).
    """
    entry = source_cache.get(name)
    if not isinstance(entry, dict) or not entry.get("ok"):
        return None

    scanned_at = parse_date(entry.get("last_scanned_at"))
    if not scanned_at:
        return None

    if now - scanned_at.timestamp() >= SOURCE_MIN_INTERVAL_SECONDS:
        return None

    cached_articles = entry.get("articles", [])
    if not isinstance(cached_articles, list):
        return []

    return [
        _deserialize_cached_article(item)
        for item in cached_articles
        if isinstance(item, dict)
    ]


def update_source_cache(
    memory: dict[str, Any],
    name: str,
    ok: bool,
    articles: list[dict[str, Any]],
) -> None:
    sources = memory.get("sources")
    if not isinstance(sources, dict):
        sources = {}
        memory["sources"] = sources

    sources[name] = {
        "last_scanned_at": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "articles": [
            _serialize_cached_article(article)
            for article in articles[:MAX_CACHED_ARTICLES_PER_SOURCE]
        ],
    }


def compute_seen_keys(
    memory: dict[str, Any],
    force_refresh: bool,
) -> set[str]:
    """
    Détermine les clés d'articles à traiter comme "déjà vues" pour ce
    run. force_refresh (--scan) signifie repartir de zéro : le filtre
    seen_article_keys est alors désactivé, sinon un "re-scan forcé"
    continuerait à écarter silencieusement tout ce qui a déjà été
    traité lors d'un run précédent.
    """
    if not SKIP_PREVIOUSLY_SEEN or force_refresh:
        return set()
    return load_seen_keys(memory)


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

    source_by_name = {
        source.get("name"): source
        for source in SOURCES
    }

    # Créneaux garantis, PAR SOURCE, pour les profils prioritaires (voir
    # PRIORITY_ENRICH_PROFILES) : une garantie par groupe de profil ne
    # suffit pas, une source à fort volume (ex : HRW via son
    # contournement Google News) pourrait à elle seule remplir un pool
    # partagé et écraser des sources sœurs plus modestes (Al Jazeera
    # par pays, HRF...). Chaque source garde donc ses propres créneaux.
    priority_by_source: dict[str, list[dict[str, Any]]] = {}
    for article in ranked:
        profile = source_by_name.get(article.get("source"), {}).get("profile")
        if profile not in PRIORITY_ENRICH_PROFILES:
            continue
        priority_by_source.setdefault(article.get("source"), []).append(article)

    priority_selected = [
        article
        for group in priority_by_source.values()
        for article in group[:ENRICH_PER_SOURCE_LIMIT]
    ]

    selected_ids = set()
    selected: list[dict[str, Any]] = []

    for article in priority_selected + ranked[:ENRICH_LIMIT]:
        if id(article) in selected_ids:
            continue
        selected_ids.add(id(article))
        selected.append(article)

    print(
        f"ENRICH | {len(selected)} articles avec body complet"
    )

    def _enrich_article(article: dict[str, Any]) -> tuple[str, Any]:
        return extract_body(
            article["url"],
            source_by_name.get(article.get("source"), {}),
            force_refresh=force_refresh,
            expected_title=article.get("title", ""),
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
                body, published_date = future.result()
            except Exception as exc:
                print(
                    f"WARNING | {article.get('source')} | ENRICH ERROR | {exc}"
                )
                body, published_date = "", None

            if body:
                article["body"] = body

            # La date de l'article (page de listing / flux RSS) fait parfois
            # défaut : on la complète avec celle trouvée sur la page elle-même.
            if not article.get("date") and published_date:
                article["date"] = published_date

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
        source = article.get(
            "source",
            "",
        )
        audit.append(
            {
                "title": article.get(
                    "title",
                    "",
                ),
                "source": source,
                "category": SOURCE_NAME_TO_GROUP.get(
                    source,
                    "Autres",
                ),
                "url": article.get(
                    "url",
                    "",
                ),
                "date": article.get(
                    "date",
                ),
                "theme": article.get(
                    "theme",
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
        source = article.get("source", "")
        row: dict[str, Any] = {
            "date": date.isoformat() if hasattr(date, "isoformat") else date or "",
            "source": source,
            "category": SOURCE_NAME_TO_GROUP.get(source, "Autres"),
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
        "category",
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
    memory: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], int, int, int]:
    """
    Parcourt toutes les sources configurées, récupère leur contenu
    et en extrait les articles bruts (non dédupliqués, non scorés).

    Une source scannée avec succès il y a moins de
    SOURCE_MIN_INTERVAL_SECONDS n'est pas re-téléchargée : ses derniers
    articles connus (mémorisés dans memory.json) sont réutilisés tels quels.

    Retourne (articles, sources_successful, sources_total, skipped_previously_seen).
    """

    sources_total = len(SOURCES)
    preload_seen = seen_keys or set()
    source_cache = load_source_cache(memory) if memory is not None else {}
    now = time.time()

    def _fetch_and_parse(
        url: str,
        source: dict[str, Any],
        as_rss: bool,
    ) -> tuple[list[dict[str, Any]], float, float]:
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

        parse_started = time.perf_counter()
        if as_rss:
            articles = parse_rss(content, source, feed_url=url)
        else:
            articles = extract_links_from_html(content, url, source)
        parse_elapsed = time.perf_counter() - parse_started

        return articles, fetch_elapsed, parse_elapsed

    def _collect_one(
        source_index: int,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        name = source.get(
            "name",
            "Unknown",
        )

        if not force_refresh:
            cached_articles = get_fresh_cached_articles(
                source_cache,
                name,
                now,
            )
            if cached_articles is not None:
                return {
                    "index": source_index,
                    "name": name,
                    "ok": True,
                    "articles": cached_articles,
                    "error": "",
                    "fetch_time": 0.0,
                    "parse_time": 0.0,
                    "total_time": 0.0,
                    "from_cache": True,
                }

        source_type = str(
            source.get(
                "type",
                "rss",
            )
        ).lower()
        is_rss = source_type in {"rss", "feed", "atom"}

        feeds = [feed for feed in (source.get("feeds") or []) if feed]
        primary_url = source.get("url", "")
        fallback_urls = [
            fallback for fallback in (source.get("fallbacks") or []) if fallback
        ]

        source_started = time.perf_counter()
        articles: list[dict[str, Any]] = []
        fetch_elapsed_total = 0.0
        parse_elapsed_total = 0.0
        errors: list[str] = []
        fetched_ok = 0

        if is_rss and feeds:
            # Une source RSS peut être répartie sur plusieurs flux
            # thématiques : on les agrège tous plutôt que de n'en
            # garder qu'un seul.
            for feed_url in feeds:
                try:
                    feed_articles, fetch_elapsed, parse_elapsed = _fetch_and_parse(
                        feed_url, source, as_rss=True
                    )
                    articles.extend(feed_articles)
                    fetch_elapsed_total += fetch_elapsed
                    parse_elapsed_total += parse_elapsed
                    fetched_ok += 1
                except Exception as exc:
                    errors.append(f"{feed_url}: {exc}")

            if fetched_ok == 0:
                # Tous les flux ont échoué : dernier recours sur l'URL
                # principale / les fallbacks, traités comme une page HTML.
                for candidate in ([primary_url] if primary_url else []) + fallback_urls:
                    try:
                        candidate_articles, fetch_elapsed, parse_elapsed = _fetch_and_parse(
                            candidate, source, as_rss=False
                        )
                        articles.extend(candidate_articles)
                        fetch_elapsed_total += fetch_elapsed
                        parse_elapsed_total += parse_elapsed
                        fetched_ok += 1
                        break
                    except Exception as exc:
                        errors.append(f"{candidate}: {exc}")
        else:
            candidates = ([primary_url] if primary_url else []) + fallback_urls

            if not candidates:
                return {
                    "index": source_index,
                    "name": name,
                    "ok": False,
                    "articles": [],
                    "error": "URL absente",
                    "fetch_time": 0.0,
                    "parse_time": 0.0,
                    "total_time": 0.0,
                    "from_cache": False,
                }

            for candidate in candidates:
                try:
                    candidate_articles, fetch_elapsed, parse_elapsed = _fetch_and_parse(
                        candidate, source, as_rss=is_rss
                    )
                    articles.extend(candidate_articles)
                    fetch_elapsed_total += fetch_elapsed
                    parse_elapsed_total += parse_elapsed
                    fetched_ok += 1
                    break
                except Exception as exc:
                    errors.append(f"{candidate}: {exc}")

        if fetched_ok == 0:
            return {
                "index": source_index,
                "name": name,
                "ok": False,
                "articles": [],
                "error": "; ".join(errors) or "erreur inconnue",
                "fetch_time": 0.0,
                "parse_time": 0.0,
                "total_time": 0.0,
                "from_cache": False,
            }

        return {
            "index": source_index,
            "name": name,
            "ok": True,
            "articles": articles,
            "error": "; ".join(errors),
            "fetch_time": fetch_elapsed_total,
            "parse_time": parse_elapsed_total,
            "total_time": time.perf_counter() - source_started,
            "from_cache": False,
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
    sources_from_cache = 0
    skipped_previously_seen = 0
    run_seen: set[str] = set()
    for result in sorted(results, key=lambda item: item["index"]):
        name = result["name"]
        from_cache = result.get("from_cache", False)

        if not result["ok"]:
            print(
                f"WARNING | {name} | ERROR | {result['error']}"
            )
            if memory is not None:
                update_source_cache(memory, name, ok=False, articles=[])
            continue

        if result["error"]:
            # Succès partiel (ex. certains flux RSS ont échoué) : on
            # continue avec ce qui a pu être récupéré, mais on le signale.
            print(
                f"WARNING | {name} | PARTIEL | {result['error']}"
            )

        sources_successful += 1
        if from_cache:
            sources_from_cache += 1

        articles = result["articles"]
        accepted = 0
        for article in articles:
            key = canonical_article_key(article)
            if not key:
                continue
            if key in run_seen:
                continue
            # Les articles servis depuis le cache par-source ne sont PAS
            # filtrés par seen_article_keys : ce cache existe pour éviter
            # de re-télécharger une source, pas pour l'exclure du rapport
            # du jour — sinon une source "fraîche" (< SOURCE_MIN_INTERVAL)
            # ne contribuerait jamais rien, puisque ses articles ont par
            # définition déjà été vus lors du scan qui a rempli le cache.
            if not from_cache and key in preload_seen:
                skipped_previously_seen += 1
                continue
            run_seen.add(key)
            all_articles.append(article)
            accepted += 1

        if not from_cache and memory is not None:
            update_source_cache(memory, name, ok=True, articles=articles)

        cache_note = " (cache, pas re-scannée)" if from_cache else ""
        print(
            f"SOURCE | {name} | {accepted}/{len(articles)} articles{cache_note} | "
            f"fetch={result['fetch_time']:.2f}s parse={result['parse_time']:.2f}s total={result['total_time']:.2f}s"
        )

    if sources_from_cache:
        print(
            f"CACHE | {sources_from_cache} source(s) non re-scannée(s) "
            f"(< {SOURCE_MIN_INTERVAL_SECONDS // 60} min)"
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
    synthesis: str = "",
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
            synthesis=synthesis,
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
    seen_keys = compute_seen_keys(memory, force_refresh)

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
        memory=memory,
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
    # Synthèse (LLM local, niveau A uniquement)
    # --------------------------------------------------------

    level_a_articles = [
        article
        for article in all_articles
        if article.get("level") == "A"
    ]

    synthesis_text = timed_call(
        "synthesis",
        generate_synthesis,
        level_a_articles,
    )

    print(
        "SYNTHESIS | "
        + (
            f"{len(synthesis_text)} caractères générés"
            if synthesis_text
            else "vide (aucun article A ou échec de génération)"
        )
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
        synthesis_text,
    )
    timed_call(
        "export-csv",
        export_csv,
        all_articles,
    )

    if SKIP_PREVIOUSLY_SEEN:
        update_seen_keys(
            memory,
            {
                canonical_article_key(article)
                for article in all_articles
                if canonical_article_key(article)
            },
        )
        print("MEMORY | seen_article_keys mis à jour")

    # Toujours persisté, y compris quand SKIP_PREVIOUSLY_SEEN est
    # désactivé : le cache par source (fraîcheur des sources) en dépend.
    safe_save_memory(memory)
    print("MEMORY | memory.json sauvegardée")

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
