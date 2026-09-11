"""
Handler RunPod Serverless pour le scoring déterministe V9 du projet.

Ce fichier est une couche fine au-dessus de scoring.py : il importe
`classify_article` (jamais dupliquée) et l'enveloppe dans le contrat
d'entrée/sortie attendu par RunPod. news_scanner.py n'est PAS
transformé en endpoint et n'est même pas importé ici — c'est
l'orchestrateur du scan complet (fetch RSS/HTML, enrichissement
réseau, génération du site), rien de tout ça n'a sa place dans un
worker serverless qui reçoit des articles déjà construits.

Décision d'architecture : `keywords_used()` (news_scanner.py) est
réimplémentée ici en quelques lignes plutôt qu'importée depuis
news_scanner.py. Ce n'est PAS de la logique de scoring (juste un
aplatissement du dict "signals" déjà produit par classify_article) —
mais importer news_scanner.py entraînerait toute sa chaîne de
dépendances (article_ingestion.py → feedparser/beautifulsoup4/
requests, http_utils.py → requests...), aucune desquelles ce handler
n'utilise réellement puisqu'il ne fait jamais de requête réseau
lui-même. Dupliquer ces ~10 lignes plutôt que d'alourdir l'image pour
elles est le compromis retenu pour un Dockerfile minimal.

Aucun accès réseau, aucune écriture disque : les articles arrivent
déjà construits (titre, résumé, corps, langue...) dans la requête.

Payload attendu (job["input"], ou directement le dict si appelé hors
RunPod) :
    {
        "mode": "score",          # ou "batch"
        "articles": [
            {
                "title": "...",          # requis
                "summary": "...",        # optionnel
                "body": "...",           # optionnel
                "url": "...",            # optionnel
                "source": "...",         # optionnel
                "language": "ru",        # optionnel (voir scoring.py)
                "date": "2026-01-01T00:00:00Z"  # optionnel, ISO
            },
            ...
        ],
        "batch_size": 200,         # optionnel, mode "batch" uniquement
        "push_to_github": {         # optionnel — voir handler()
            "path": "runpod_results/2026-09-11.json",
            "branch": "runpod-results"
        }
    }

Réponse :
    {
        "mode": "score",
        "count": 3,
        "scored": 2,
        "failed": 1,
        "results": [
            {
                "index": 0,
                "title": "...",
                "url": "...",
                "source": "...",
                "score": 92,
                "level": "A",
                "priority": "TRÈS HAUTE",
                "relevant": true,
                "theme": "Activistes / dissidents sous pression",
                "keywords": ["activist", "arrested", ...],
                "reasons": [...],
                "language": "en",
                "sub_scores": {
                    "geography_score": 12, "target_score": 8, ...
                }
            },
            ...
        ],
        "errors": [
            {"index": 1, "error": "champ 'title' manquant ou vide", "url": "..."}
        ]
    }
"""

from __future__ import annotations

import logging
import time
from typing import Any

from github_push import DEFAULT_BRANCH, GitHubPushError, push_json_to_github
from scoring import classify_article

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("rp_handler")

DEFAULT_BATCH_SIZE = 200


def _keywords_used(article: dict[str, Any]) -> list[str]:
    """
    Aplatit les listes de mots-clés du dict "signals" produit par
    classify_article() en une liste plate dédupliquée — voir la note
    d'architecture en tête de fichier sur pourquoi ce n'est pas
    importé depuis news_scanner.keywords_used().
    """
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


def score_one_article(
    raw_article: Any,
    index: int,
) -> dict[str, Any]:
    """
    Score un seul article. Ne lève jamais : toute erreur (article
    malformé, champ manquant, exception interne au scoring) est
    retournée comme {"index":..., "error":...} plutôt que de
    propager — un lot de plusieurs milliers d'articles ne doit jamais
    s'arrêter à cause d'un seul article invalide.
    """
    if not isinstance(raw_article, dict):
        return {
            "index": index,
            "error": (
                "l'article n'est pas un objet JSON "
                f"(type={type(raw_article).__name__})"
            ),
        }

    title = raw_article.get("title")
    if not title or not isinstance(title, str):
        return {
            "index": index,
            "error": "champ 'title' manquant ou vide",
            "url": raw_article.get("url"),
        }

    article: dict[str, Any] = {
        "title": title,
        "summary": raw_article.get("summary") or "",
        "body": raw_article.get("body") or "",
        "source": raw_article.get("source") or "",
        "url": raw_article.get("url") or "",
        "date": raw_article.get("date"),
        "language": raw_article.get("language") or "",
    }

    try:
        classify_article(article)
    except Exception as exc:  # défense en profondeur : jamais tuer le lot
        return {
            "index": index,
            "error": f"{type(exc).__name__}: {exc}",
            "url": article["url"],
            "title": title,
        }

    signals = article.get("signals") or {}

    return {
        "index": index,
        "title": article["title"],
        "url": article["url"],
        "source": article["source"],
        "score": article.get("score", 0),
        "level": article.get("level", "E"),
        "priority": article.get("priority", ""),
        "relevant": article.get("relevant", False),
        "theme": article.get("theme", ""),
        "keywords": _keywords_used(article),
        "reasons": list(article.get("reasons") or []),
        "language": article.get("language", ""),
        "sub_scores": {
            "geography_score": signals.get("geography_score", 0),
            "target_score": signals.get("target_score", 0),
            "repression_score": signals.get("repression_score", 0),
            "rights_score": signals.get("rights_score", 0),
            "journalism_score": signals.get("journalism_score", 0),
            "geopolitical_score": signals.get("geopolitical_score", 0),
        },
    }


def _score_many(raw_articles: list[Any]) -> tuple[list[dict], list[dict]]:
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for index, raw_article in enumerate(raw_articles):
        outcome = score_one_article(raw_article, index)
        if "error" in outcome:
            errors.append(outcome)
            logger.warning(
                "article %s en erreur: %s", index, outcome["error"]
            )
        else:
            results.append(outcome)

    return results, errors


def _validate_articles(raw_articles: Any) -> list[Any]:
    if raw_articles is None:
        raise ValueError("champ 'articles' manquant")

    if not isinstance(raw_articles, list):
        raise ValueError(
            f"'articles' doit être une liste (reçu: {type(raw_articles).__name__})"
        )

    return raw_articles


def score_articles(job_input: dict[str, Any]) -> dict[str, Any]:
    """mode="score" : tous les articles en un seul passage."""
    raw_articles = _validate_articles(job_input.get("articles"))

    logger.info("mode=score | %s article(s) reçu(s)", len(raw_articles))

    results, errors = _score_many(raw_articles)

    return {
        "mode": "score",
        "count": len(raw_articles),
        "scored": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


def batch_score_articles(job_input: dict[str, Any]) -> dict[str, Any]:
    """
    mode="batch" : même résultat que "score", mais en traitant les
    articles par lots de `batch_size` (200 par défaut) avec des logs
    de progression réguliers — pensé pour de gros volumes (plusieurs
    milliers d'articles) et pour rester le point d'extension naturel
    le jour où une étape plus coûteuse (appel LLM) s'ajoute par lot.
    """
    raw_articles = _validate_articles(job_input.get("articles"))

    batch_size = job_input.get("batch_size", DEFAULT_BATCH_SIZE)
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("'batch_size' doit être un entier positif")

    logger.info(
        "mode=batch | %s article(s) reçu(s) | lots de %s",
        len(raw_articles), batch_size,
    )

    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for start in range(0, len(raw_articles), batch_size):
        chunk = raw_articles[start:start + batch_size]
        chunk_offset = start

        chunk_results, chunk_errors = _score_many(chunk)

        for outcome in chunk_results:
            outcome["index"] += chunk_offset
        for outcome in chunk_errors:
            outcome["index"] += chunk_offset

        results.extend(chunk_results)
        errors.extend(chunk_errors)

        logger.info(
            "mode=batch | lot %s-%s/%s traité | %s réussis, %s en erreur",
            start, start + len(chunk), len(raw_articles),
            len(chunk_results), len(chunk_errors),
        )

    return {
        "mode": "batch",
        "count": len(raw_articles),
        "scored": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


_MODES = {
    "score": score_articles,
    "batch": batch_score_articles,
}


def _push_result_to_github(
    result: dict[str, Any],
    push_config: Any,
) -> dict[str, Any]:
    """
    Commits `result` to GitHub per `push_config` (see handler()'s
    docstring for the payload shape). Never raises: a push failure
    (missing token, network error, GitHub API error) is reported as
    {"error": ...} rather than failing the whole job — the scoring
    results in the response are still valid even if persisting them
    to GitHub didn't work.
    """
    if push_config is True:
        push_config = {}

    if not isinstance(push_config, dict):
        return {
            "error": (
                "'push_to_github' doit être un objet ou true "
                f"(reçu: {type(push_config).__name__})"
            )
        }

    path = push_config.get("path") or f"runpod_results/result_{int(time.time())}.json"
    branch = push_config.get("branch") or DEFAULT_BRANCH
    message = push_config.get("message") or "RunPod scoring results"
    repo = push_config.get("repo") or ""

    try:
        return push_json_to_github(
            result, path=path, branch=branch, message=message, repo=repo
        )
    except GitHubPushError as exc:
        logger.warning("push GitHub échoué: %s", exc)
        return {"error": str(exc)}


def handler(event: Any) -> dict[str, Any]:
    """
    Point d'entrée RunPod Serverless. Accepte aussi bien le format
    RunPod réel (event["input"] = le payload envoyé par l'appelant)
    que le payload nu directement (pratique pour les tests locaux et
    l'appel direct hors RunPod).

    Champ optionnel "push_to_github" dans le payload : quand présent
    (objet, ou `true` pour les valeurs par défaut), les résultats de ce
    job sont aussi commités sur GitHub via github_push.py, sur une
    branche dédiée (par défaut "runpod-results", créée depuis la
    branche par défaut du repo si besoin) plutôt que de rester
    uniquement dans la réponse HTTP :
        "push_to_github": {
            "path": "runpod_results/2026-09-11.json",  # optionnel
            "branch": "runpod-results",                # optionnel
            "message": "RunPod scoring run",            # optionnel
            "repo": "owner/repo"                         # optionnel
        }
    Le résultat du push (ou son erreur) est ajouté sous
    result["github_push"]. Nécessite GITHUB_TOKEN en variable
    d'environnement (secret RunPod) — jamais dans le payload.
    """
    if not isinstance(event, dict):
        return {"error": f"requête invalide (type={type(event).__name__})"}

    job_input = event.get("input")
    if job_input is None:
        job_input = event
    elif not isinstance(job_input, dict):
        return {
            "error": f"'input' doit être un objet JSON (reçu: {type(job_input).__name__})"
        }

    mode = job_input.get("mode", "score")

    mode_handler = _MODES.get(mode)
    if mode_handler is None:
        return {
            "error": (
                f"mode inconnu: {mode!r} "
                f"(supportés: {', '.join(sorted(_MODES))})"
            )
        }

    try:
        result = mode_handler(job_input)
    except ValueError as exc:
        return {"error": str(exc)}
    except Exception as exc:  # jamais laisser le worker planter sur une requête
        logger.exception("erreur inattendue dans le handler")
        return {"error": f"{type(exc).__name__}: {exc}"}

    push_config = job_input.get("push_to_github")
    if push_config:
        result["github_push"] = _push_result_to_github(result, push_config)

    return result


if __name__ == "__main__":
    import runpod

    runpod.serverless.start({"handler": handler})
