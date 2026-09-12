"""
Standalone, one-off full-body fetcher for the RunPod LLM-vs-deterministic
benchmark.

Reads articles.csv (news_scanner.py's export_csv output: title, summary,
url, source, score, level... for every article from a run) and fetches
each article's full body via extract_body() (reused as-is from
article_ingestion.py — the exact same extraction logic the daily scan
uses for its ~600 enriched articles, never duplicated), writing a JSON
export that also carries "body" and each source's declared "language"
(from sources.py) for every article, not just the usual enrichment
subset.

Decoupled from the daily scan on purpose:
- Doesn't touch memory.json's body_cache (bounded to
  BODY_CACHE_MAX_ENTRIES=500 entries, meant for incremental reuse
  across daily runs — a full-corpus one-off dump doesn't belong there).
- Not run by the GitHub Actions cron. Meant to be run once (or
  occasionally), locally or via a dedicated workflow_dispatch, whenever
  the benchmark needs full article text instead of just title+summary
  — e.g. to check whether the deterministic scanner is missing
  articles that only become clearly relevant once you read past the
  headline.

Needs the full project dependencies (feedparser/beautifulsoup4/requests
— see requirements.txt), unlike rp_handler.py's deliberately
minimal requirements-runpod.txt: this script is not part of the RunPod
image, it's what produces the JSON you'd feed to it.

Usage:
    python fetch_all_bodies.py --input articles.csv --output articles_with_body.json
    python fetch_all_bodies.py --input articles.csv --output sample.json --limit 50  # test run
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib.parse import urlparse

from article_ingestion import extract_body
from sources import SOURCES

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("fetch_all_bodies")

DEFAULT_WORKERS = 15

SOURCE_LANGUAGE = {
    source.get("name", ""): source.get("language", "")
    for source in SOURCES
}

# Repéré en conditions réelles le 2026-09-11 : à l'échelle de tout le
# corpus (~6800 URLs, dont environ un tiers passe par le contournement
# Google News), lancer autant de requêtes news.google.com en parallèle
# que le reste (15-20 workers) déclenche du rate-limiting de Google
# (503 Service Unavailable en rafale) — chaque échec brûle jusqu'à ~90s
# en retries (voir http_utils.MAX_ATTEMPTS) et un run de 6800 articles
# a été tué par son timeout de 3h à seulement 38% (2600/6725), la
# quasi-totalité des échecs pointant vers news.google.com.
#
# Un premier correctif (2026-09-11, un simple threading.Semaphore
# partagé par le même pool de `workers` threads) a empiré les choses :
# un tiers du corpus (2220/6725, vérifié) est du Google News, donc dès
# qu'un nombre de threads du pool dépassant google_news_concurrency
# récupère une URL Google News, ces threads restent bloqués sur
# semaphore.acquire() — indisponibles pour traiter les 2/3 d'articles
# restants. Un deuxième run a fini plus lent que le premier (2100/6725
# en 180 min, débit passant de ~39/min à ~5.6/min de façon monotone à
# mesure que de plus en plus de threads du pool se retrouvaient
# bloqués). Le pool Google News est donc désormais un
# ThreadPoolExecutor séparé et dédié (borné à google_news_concurrency
# threads) : ses requêtes ne consomment jamais un slot du pool
# principal, qui garde sa pleine capacité pour le reste du corpus.
#
# Le scan quotidien n'a jamais ce problème (il n'enrichit qu'environ
# 600 articles), donc ce throttle reste local à ce script plutôt que
# de toucher http_utils.py (partagé avec le pipeline principal).
GOOGLE_NEWS_HOST = "news.google.com"
DEFAULT_GOOGLE_NEWS_CONCURRENCY = 2
DEFAULT_GOOGLE_NEWS_DELAY = 1.0  # secondes, appliqué après chaque requête


def _is_google_news_url(url: str) -> bool:
    try:
        return urlparse(url).netloc == GOOGLE_NEWS_HOST
    except ValueError:
        return False


def load_rows(
    path: str,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if limit is not None:
        rows = rows[:limit]

    return rows


def _fetch_one(
    row: dict[str, Any],
    google_news_delay: float,
) -> tuple[dict[str, Any], str, Any, Exception | None]:
    url = row.get("url") or ""
    title = row.get("title") or ""

    if not url:
        return row, "", None, ValueError("URL manquante")

    is_google_news = _is_google_news_url(url)

    try:
        body, published_date = extract_body(url, expected_title=title)
        return row, body, published_date, None
    except Exception as exc:  # un site qui plante ne doit pas arrêter les autres
        return row, "", None, exc
    finally:
        if is_google_news:
            # Espace les requêtes successives d'un même thread du pool
            # Google News dédié (voir fetch_all_bodies) : la limite de
            # concurrence vient du nombre de threads de ce pool, ce
            # délai évite juste qu'un seul thread ne re-déclenche le
            # rate-limiting en enchaînant les requêtes sans pause.
            time.sleep(google_news_delay)


def fetch_all_bodies(
    rows: list[dict[str, Any]],
    workers: int = DEFAULT_WORKERS,
    google_news_concurrency: int = DEFAULT_GOOGLE_NEWS_CONCURRENCY,
    google_news_delay: float = DEFAULT_GOOGLE_NEWS_DELAY,
) -> list[dict[str, Any]]:
    """
    Récupère le corps complet de chaque ligne en parallèle. Ne lève
    jamais pour un article donné : un échec (403, timeout, page
    inattendue...) est noté dans "fetch_error" plutôt que d'interrompre
    le lot — sur plusieurs milliers d'URLs, une partie échouera
    toujours (les mêmes sources déjà bloquées dans le scan normal), ce
    n'est pas une raison de perdre le reste.

    Les URLs news.google.com (contournement Google News, environ un
    tiers du corpus) sont traitées par un pool de threads séparé et
    dédié, borné à `google_news_concurrency` threads, avec
    `google_news_delay` secondes d'espacement entre deux requêtes d'un
    même thread — le reste du corpus garde la pleine concurrence de
    `workers` dans son propre pool, jamais bloqué par le débit du
    premier. Voir la note au-dessus de GOOGLE_NEWS_HOST (un sémaphore
    partagé par le même pool avait été essayé d'abord et avait
    empiré les choses).
    """
    results: list[dict[str, Any]] = []
    done = 0
    failed = 0

    started = time.perf_counter()

    google_news_rows = [r for r in rows if _is_google_news_url(r.get("url") or "")]
    other_rows = [r for r in rows if not _is_google_news_url(r.get("url") or "")]

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor, ThreadPoolExecutor(
        max_workers=max(1, google_news_concurrency)
    ) as google_news_executor:
        futures = {
            executor.submit(_fetch_one, row, google_news_delay): row
            for row in other_rows
        }
        futures.update(
            {
                google_news_executor.submit(_fetch_one, row, google_news_delay): row
                for row in google_news_rows
            }
        )

        for future in as_completed(futures):
            row, body, published_date, error = future.result()

            enriched = dict(row)
            enriched["body"] = body
            enriched["language"] = SOURCE_LANGUAGE.get(row.get("source", ""), "")

            if error is not None:
                enriched["fetch_error"] = f"{type(error).__name__}: {error}"
                failed += 1
                logger.warning(
                    "échec sur %s: %s", row.get("url"), enriched["fetch_error"]
                )
            elif not body:
                enriched["fetch_error"] = (
                    "corps vide (page inattendue, redirection, ou URL manquante)"
                )
                failed += 1

            results.append(enriched)
            done += 1

            if done % 100 == 0 or done == len(rows):
                elapsed = time.perf_counter() - started
                logger.info(
                    "%s/%s articles traités | %s échec(s) | %.0fs écoulées",
                    done, len(rows), failed, elapsed,
                )

    return results


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="articles.csv")
    parser.add_argument("--output", default="articles_with_body.json")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Ne traiter que les N premières lignes (pour un essai rapide).",
    )
    parser.add_argument(
        "--google-news-concurrency",
        type=int,
        default=DEFAULT_GOOGLE_NEWS_CONCURRENCY,
        help="Requêtes news.google.com simultanées max (throttle anti rate-limiting).",
    )
    parser.add_argument(
        "--google-news-delay",
        type=float,
        default=DEFAULT_GOOGLE_NEWS_DELAY,
        help="Délai (s) après chaque requête news.google.com avant de relâcher le créneau.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    rows = load_rows(args.input, limit=args.limit)
    logger.info("%s article(s) chargé(s) depuis %s", len(rows), args.input)

    results = fetch_all_bodies(
        rows,
        workers=args.workers,
        google_news_concurrency=args.google_news_concurrency,
        google_news_delay=args.google_news_delay,
    )

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump({"articles": results}, handle, ensure_ascii=False, indent=2)

    succeeded = sum(1 for r in results if r.get("body"))
    logger.info(
        "terminé | %s/%s corps récupérés | écrit dans %s",
        succeeded, len(results), args.output,
    )


if __name__ == "__main__":
    main()
