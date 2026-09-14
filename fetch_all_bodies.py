"""
Téléchargeur de corps d'articles en masse, à lancer à la demande.

DEUX MODES, une seule boucle de téléchargement.

--archive (remplissage de l'archive)
    Prend les entrées d'archive.jsonl qui n'ont pas encore de corps,
    télécharge, et écrit le résultat dans l'archive. Le scan quotidien
    fait la même chose mais par tranches d'environ 300 corps par run :
    saturer la part récupérable du corpus lui demande une quinzaine de
    jours, là où ce mode le fait en une passe avec le budget de 4 h du
    job dédié. La reprise est gratuite — les corps sont écrits en cours
    de route, donc un run tué par le timeout garde ce qu'il a récupéré
    et le suivant ne resélectionne pas ces entrées.

mode d'origine (export JSON pour le benchmark RunPod)
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
    # Remplir l'archive (mode principal aujourd'hui) :
    python fetch_all_bodies.py --archive
    python fetch_all_bodies.py --archive --limit 50   # essai rapide

    # Export JSON pour le benchmark RunPod :
    python fetch_all_bodies.py --input articles.csv --output articles_with_body.json
    python fetch_all_bodies.py --input articles.csv --output sample.json --limit 50  # test run

    # Reprendre un run interrompu (timeout du job, etc.) sans
    # re-télécharger ce qui a déjà réussi :
    python fetch_all_bodies.py --input articles.csv --output articles_with_body.json \
        --resume-from previous_articles_with_body.json
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable
from urllib.parse import urlparse

from pathlib import Path

import archive
from article_ingestion import extract_body
from matching import looks_like_section_page
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


# Les URLs news.google.com ne rendent jamais l'article : elles rendent
# la page interstitielle de Google News. Mesuré le 2026-09-13 sur le
# corpus réel — corps extrait de 11 caractères en médiane ("Google
# News") contre 3790 pour les autres sources.
#
# Ce n'est pas un bug à corriger : ces sources (HRW dans ses trois
# langues, ARTICLE 19, TASS, Regnum...) ne sont atteignables QUE par ce
# contournement, parce qu'elles bloquent l'accès direct. Leur corps est
# donc structurellement indisponible.
#
# Les télécharger quand même coûtait très cher : elles représentent un
# tiers du corpus et sont concentrées en tête du CSV (44 % des 100
# premières lignes, 75 % des 1400 premières), d'où les runs affichant
# ~99 % d'échecs dès le premier checkpoint, et quatre runs tués par le
# timeout de 4 h. On les marque au lieu de les tenter : le run va
# beaucoup plus vite, et le résultat distingue "indisponible par
# construction" d'un vrai échec réseau.
BODY_UNAVAILABLE_GOOGLE_NEWS = (
    "corps indisponible : source accessible uniquement via Google News"
)


def _skip_google_news_row(row: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(row)
    enriched["body"] = ""
    enriched["body_unavailable"] = BODY_UNAVAILABLE_GOOGLE_NEWS
    enriched["language"] = SOURCE_LANGUAGE.get(row.get("source", ""), "")
    return enriched


def load_previous_results(path: str) -> dict[str, dict[str, Any]]:
    """
    Charge un articles_with_body.json d'un run précédent (typiquement
    partiel, si ce run a été tué par le timeout du job) et renvoie les
    articles déjà récupérés AVEC SUCCÈS (body non vide, sans
    fetch_error), indexés par url. Décidé le 2026-09-12 après 4 runs
    consécutifs perdus dans leur intégralité au timeout : sur un corpus
    de ~6800 articles qui prend plusieurs heures, il ne faut jamais
    re-télécharger ce qui a déjà été récupéré avec succès.

    Renvoie {} silencieusement si le fichier n'existe pas ou est
    invalide (première tentative, ou artefact introuvable) — ce n'est
    pas une erreur, juste l'absence de progrès à reprendre.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}

    articles = data.get("articles", []) if isinstance(data, dict) else []

    done: dict[str, dict[str, Any]] = {}
    for row in articles:
        if not isinstance(row, dict):
            continue
        url = row.get("url") or ""
        if url and row.get("body") and not row.get("fetch_error"):
            done[url] = row

    return done


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
    checkpoint_path: str | None = None,
    already_done: list[dict[str, Any]] | None = None,
    skip_google_news: bool = True,
    checkpoint_hook: Callable[[list[dict[str, Any]]], None] | None = None,
) -> list[dict[str, Any]]:
    """
    Récupère le corps complet de chaque ligne en parallèle. Ne lève
    jamais pour un article donné : un échec (403, timeout, page
    inattendue...) est noté dans "fetch_error" plutôt que d'interrompre
    le lot — sur plusieurs milliers d'URLs, une partie échouera
    toujours (les mêmes sources déjà bloquées dans le scan normal), ce
    n'est pas une raison de perdre le reste.

    Les URLs news.google.com (environ un tiers du corpus) sont par
    défaut marquées sans être téléchargées : elles ne rendent que la
    page interstitielle de Google News, jamais l'article (voir
    BODY_UNAVAILABLE_GOOGLE_NEWS). `skip_google_news=False` rétablit
    la tentative, utile uniquement pour vérifier que ça n'a pas changé
    côté Google. Quand elles sont tentées, elles passent par un pool de
    threads séparé et dédié, borné à `google_news_concurrency` threads, avec
    `google_news_delay` secondes d'espacement entre deux requêtes d'un
    même thread — le reste du corpus garde la pleine concurrence de
    `workers` dans son propre pool, jamais bloqué par le débit du
    premier. Voir la note au-dessus de GOOGLE_NEWS_HOST (un sémaphore
    partagé par le même pool avait été essayé d'abord et avait
    empiré les choses).

    Si `checkpoint_path` est fourni, le résultat cumulé
    (`already_done` + ce que cet appel a déjà traité) est réécrit sur
    disque à la même cadence que les logs de progression, de façon
    atomique (fichier temporaire + os.replace, jamais de JSON
    tronqué/corrompu). Décidé le 2026-09-12 après 4 runs consécutifs
    tués par le timeout du job GitHub Actions sans qu'aucun résultat ne
    soit jamais écrit sur disque avant la fin — chaque run repartait de
    zéro. Avec ce checkpoint + `--resume-from`/`load_previous_results`,
    un run interrompu laisse un fichier réutilisable par le suivant.
    """
    already_done = already_done or []
    results: list[dict[str, Any]] = []
    done = 0
    failed = 0

    started = time.perf_counter()

    def _write_checkpoint() -> None:
        # Le mode archive écrit dans archive.jsonl et non dans un JSON
        # d'export : le crochet remplace l'écriture, il ne s'y ajoute
        # pas. Le reste de la boucle (cadence, reprise, comptage) est
        # commun aux deux modes et n'est pas dupliqué.
        if checkpoint_hook is not None:
            checkpoint_hook(already_done + results)
            return

        if not checkpoint_path:
            return
        tmp_path = f"{checkpoint_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(
                {"articles": already_done + results},
                handle,
                ensure_ascii=False,
                indent=2,
            )
        os.replace(tmp_path, checkpoint_path)

    google_news_rows = [r for r in rows if _is_google_news_url(r.get("url") or "")]
    other_rows = [r for r in rows if not _is_google_news_url(r.get("url") or "")]

    if skip_google_news and google_news_rows:
        logger.info(
            "%s article(s) Google News marqué(s) sans téléchargement "
            "(corps structurellement indisponible, voir "
            "BODY_UNAVAILABLE_GOOGLE_NEWS)",
            len(google_news_rows),
        )
        results.extend(_skip_google_news_row(row) for row in google_news_rows)
        google_news_rows = []

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

            # extract_body() rend la date de publication trouvée dans la
            # page. Elle était décompressée puis jetée : la passe de
            # remplissage a téléchargé des milliers de pages en
            # abandonnant chaque fois la date qu'elle venait de lire.
            if published_date is not None:
                enriched["published_date"] = published_date

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
                # Diagnostic ajouté le 2026-09-13 : ce cas (pas
                # d'exception, juste un corps vide) peut venir de deux
                # garde-fous différents dans extract_body()
                # (_page_matches_expected_title ou
                # _body_matches_expected_title, article_ingestion.py)
                # qui renvoient tous les deux "" de façon indiscernable
                # — repéré sur un run réel (run #8) au taux d'échec
                # anormalement élevé (~99% dès les 100 premiers
                # articles), pour comprendre si un des deux garde-fous
                # est devenu trop agressif.
                logger.warning(
                    "corps vide sur %s (titre attendu: %r)",
                    row.get("url"), (row.get("title") or "")[:120],
                )

            results.append(enriched)
            done += 1

            if done % 100 == 0 or done == len(rows):
                elapsed = time.perf_counter() - started
                logger.info(
                    "%s/%s articles traités | %s échec(s) | %.0fs écoulées",
                    done, len(rows), failed, elapsed,
                )
                _write_checkpoint()

    _write_checkpoint()

    return results


# ============================================================
# MODE ARCHIVE — remplir archive.jsonl au lieu d'un export JSON
# ============================================================
#
# Le scan quotidien enrichit ~600 articles par run et n'en conserve
# qu'une partie : au rythme constaté le 2026-09-14, saturer la part
# récupérable du corpus demande une quinzaine de runs. Ce mode fait le
# même travail en une passe, avec le budget de 4 h du job dédié.
#
# Il écrit directement dans l'archive, contrairement au mode d'origine
# qui produit un artefact pour le benchmark RunPod. Les deux partagent
# exactement la même boucle de téléchargement.


def _manque_quelque_chose(entry: dict[str, Any]) -> bool:
    if not (entry.get("body") or ""):
        return True

    if entry.get("date"):
        return False

    # Une page de rubrique n'a pas de date de publication à trouver :
    # la resélectionner à chaque run ne ferait que gâcher du budget.
    return not looks_like_section_page(
        entry.get("url") or "", entry.get("title") or ""
    )


def rows_from_archive(
    entries: dict[str, dict[str, Any]],
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Entrées d'archive à télécharger, au format attendu par
    fetch_all_bodies() — celles qui n'ont pas encore de corps.

    Une entrée est candidate si son corps OU sa date manque : la même
    page porte les deux, et une date extraite ne coûte rien de plus
    une fois la page téléchargée.

    C'est aussi ce qui rend la reprise gratuite : un run interrompu par
    le timeout a déjà écrit ses corps dans l'archive (voir le crochet
    de checkpoint), donc le run suivant ne les resélectionne pas. Pas
    de --resume-from à manipuler, pas d'artefact à retrouver.

    Limite assumée : une page qui n'affiche réellement aucune date
    restera candidate d'un run à l'autre. Marquer les tentatives
    infructueuses demanderait un champ de plus dans l'archive pour un
    outil lancé à la main quelques fois — le coût ne le justifie pas
    aujourd'hui.
    """
    rows = [
        {
            "key": key,
            "url": entry.get("url") or "",
            "title": entry.get("title") or "",
            "source": entry.get("source") or "",
        }
        for key, entry in entries.items()
        if (entry.get("url") or "") and _manque_quelque_chose(entry)
    ]

    if limit is not None:
        rows = rows[:limit]

    return rows


def apply_to_archive(
    results: list[dict[str, Any]],
    archive_path: Path | None = None,
) -> int:
    """
    Écrit les corps récupérés dans l'archive. Renvoie le nombre
    d'entrées mises à jour.

    Passe par archive.backfill_bodies pour hériter de ses garanties
    plutôt que d'écrire les lignes à la main : jamais de corps
    remplacé par un plus court, troncature à BODY_MAX_CHARS, niveaux
    respectés.
    """
    scanned = [
        # backfill_bodies filtre sur le niveau ; ces articles viennent
        # de l'archive et n'en portent pas, on déclare donc le niveau
        # le plus permissif présent dans la configuration.
        (
            row.get("key") or "",
            {
                "level": _niveau_permissif(),
                "body": row.get("body") or "",
                "date": row.get("published_date"),
            },
        )
        for row in results
        if row.get("body") or row.get("published_date")
    ]

    if not scanned:
        return 0

    entries = archive.load_archive(archive_path)
    corps = archive.backfill_bodies(entries, scanned)
    dates = archive.backfill_dates(entries, scanned)

    if corps or dates:
        archive.rewrite_archive(entries.values(), archive_path)

    return corps + dates


def _niveau_permissif() -> str:
    """Un niveau que BODY_KEEP_LEVELS accepte, quel que soit son réglage."""
    for niveau in ("E", "D", "C", "B", "A"):
        if niveau in archive.BODY_KEEP_LEVELS:
            return niveau
    return ""


def run_archive_mode(args: argparse.Namespace) -> None:
    entries = archive.load_archive()
    rows = rows_from_archive(entries, limit=args.limit)

    logger.info(
        "%s entrée(s) dans l'archive | %s sans corps à traiter",
        len(entries), len(rows),
    )

    if not rows:
        logger.info("terminé | rien à télécharger")
        return

    def _checkpoint(cumul: list[dict[str, Any]]) -> None:
        # Écrire en cours de route, pas seulement à la fin : quatre runs
        # consécutifs ont été perdus au timeout en 2026-09 faute de
        # checkpoint. Ici le checkpoint EST le résultat final, donc un
        # run tué à 90 % garde ses 90 %.
        mis_a_jour = apply_to_archive(cumul)
        if mis_a_jour:
            logger.info("checkpoint | %s corps écrits dans l'archive", mis_a_jour)

    results = fetch_all_bodies(
        rows,
        workers=args.workers,
        google_news_concurrency=args.google_news_concurrency,
        google_news_delay=args.google_news_delay,
        skip_google_news=not args.tenter_google_news,
        checkpoint_hook=_checkpoint,
    )

    apply_to_archive(results)

    final = archive.load_archive()
    avec_corps = sum(1 for e in final.values() if e.get("body"))

    logger.info(
        "terminé | %s/%s entrées de l'archive ont un corps",
        avec_corps, len(final),
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="articles.csv")
    parser.add_argument("--output", default="articles_with_body.json")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument(
        "--tenter-google-news",
        action="store_true",
        help=(
            "Tente quand même de télécharger les URLs news.google.com. "
            "Elles ne rendent que la page interstitielle (corps médian "
            "de 11 caractères sur le corpus réel), donc c'est inutile "
            "en pratique — à n'utiliser que pour vérifier que ça n'a "
            "pas changé côté Google."
        ),
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help=(
            "Remplit archive.jsonl au lieu de produire un export JSON : "
            "télécharge le corps des entrées qui n'en ont pas encore et "
            "l'écrit dans l'archive. Reprise automatique — un run "
            "interrompu a déjà écrit ce qu'il avait récupéré."
        ),
    )
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
    parser.add_argument(
        "--resume-from",
        default=None,
        help=(
            "articles_with_body.json d'un run précédent (même "
            "partiel/interrompu par un timeout) : les articles déjà "
            "récupérés avec succès (body non vide, sans fetch_error) "
            "sont réutilisés tels quels, sans être re-téléchargés."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.archive:
        run_archive_mode(args)
        return

    rows = load_rows(args.input, limit=args.limit)
    logger.info("%s article(s) chargé(s) depuis %s", len(rows), args.input)

    previous_done: dict[str, dict[str, Any]] = {}
    if args.resume_from:
        previous_done = load_previous_results(args.resume_from)
        logger.info(
            "%s article(s) déjà récupéré(s) avec succès dans %s, ignoré(s)",
            len(previous_done), args.resume_from,
        )

    remaining_rows = [
        row for row in rows if (row.get("url") or "") not in previous_done
    ]

    results = fetch_all_bodies(
        remaining_rows,
        workers=args.workers,
        google_news_concurrency=args.google_news_concurrency,
        google_news_delay=args.google_news_delay,
        checkpoint_path=args.output,
        already_done=list(previous_done.values()),
        skip_google_news=not args.tenter_google_news,
    )

    combined = list(previous_done.values()) + results

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump({"articles": combined}, handle, ensure_ascii=False, indent=2)

    succeeded = sum(1 for r in combined if r.get("body"))
    logger.info(
        "terminé | %s/%s corps récupérés | écrit dans %s",
        succeeded, len(combined), args.output,
    )


if __name__ == "__main__":
    main()
