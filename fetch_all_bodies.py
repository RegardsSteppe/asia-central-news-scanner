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
— see requirements.txt), unlike runpod_handler.py's deliberately
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

from article_ingestion import extract_body
from sources import SOURCES

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("fetch_all_bodies")

DEFAULT_WORKERS = 15

SOURCE_LANGUAGE = {
    source.get("name", ""): source.get("language", "")
    for source in SOURCES
}


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
) -> tuple[dict[str, Any], str, Any, Exception | None]:
    url = row.get("url") or ""
    title = row.get("title") or ""

    if not url:
        return row, "", None, ValueError("URL manquante")

    try:
        body, published_date = extract_body(url, expected_title=title)
        return row, body, published_date, None
    except Exception as exc:  # un site qui plante ne doit pas arrêter les autres
        return row, "", None, exc


def fetch_all_bodies(
    rows: list[dict[str, Any]],
    workers: int = DEFAULT_WORKERS,
) -> list[dict[str, Any]]:
    """
    Récupère le corps complet de chaque ligne en parallèle. Ne lève
    jamais pour un article donné : un échec (403, timeout, page
    inattendue...) est noté dans "fetch_error" plutôt que d'interrompre
    le lot — sur plusieurs milliers d'URLs, une partie échouera
    toujours (les mêmes sources déjà bloquées dans le scan normal), ce
    n'est pas une raison de perdre le reste.
    """
    results: list[dict[str, Any]] = []
    done = 0
    failed = 0

    started = time.perf_counter()

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {
            executor.submit(_fetch_one, row): row
            for row in rows
        }

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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    rows = load_rows(args.input, limit=args.limit)
    logger.info("%s article(s) chargé(s) depuis %s", len(rows), args.input)

    results = fetch_all_bodies(rows, workers=args.workers)

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump({"articles": results}, handle, ensure_ascii=False, indent=2)

    succeeded = sum(1 for r in results if r.get("body"))
    logger.info(
        "terminé | %s/%s corps récupérés | écrit dans %s",
        succeeded, len(results), args.output,
    )


if __name__ == "__main__":
    main()
