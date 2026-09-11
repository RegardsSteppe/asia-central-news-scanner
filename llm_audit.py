"""
Audit sémantique par LLM des articles non retenus par le scoring
déterministe (scoring.py) — pour repérer les faux négatifs qu'aucune
liste de mots-clés ne peut attraper (paraphrase, tournure inhabituelle,
langue mal couverte...).

Volontairement indépendant du pipeline GitHub Actions : un LLM même
léger, passé sur l'ensemble du corpus (niveaux D+E, ~95% des articles
d'un run), serait trop lent sur un runner CPU-only (plafonné à 6h) —
conçu à la place pour tourner ailleurs (ex. un pod GPU RunPod) contre
n'importe quel serveur exposant une API compatible OpenAI (vLLM,
text-generation-webui, Ollama, llama.cpp server...). Pas de dépendance
au package "openai" : un simple POST JSON via `requests` suffit et
marche contre n'importe lequel de ces serveurs.

Le score/niveau du site n'est jamais modifié par ce script : il produit
uniquement un rapport de "candidats possiblement loupés" à relire à la
main (et, une fois confirmés, à traduire en ajouts dans keywords.py/
scoring.py — le LLM est un outil d'audit, pas la référence du site).

Usage :
    python llm_audit.py --input articles.csv --output llm_audit_report.csv \\
        --base-url http://localhost:8000/v1 --model qwen2.5-3b-instruct
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from dataclasses import dataclass
from typing import Any

import requests

DEFAULT_BATCH_SIZE = 25
DEFAULT_MAX_SUMMARY_CHARS = 300
DEFAULT_TIMEOUT = 120

_SYSTEM_PROMPT = (
    "Tu es un assistant de veille sur les droits humains en Asie "
    "centrale, dans le Caucase et sur la question ouïghoure. On te "
    "donne une liste de titres d'articles (parfois accompagnés d'un "
    "court extrait), qui ont déjà été classés comme non pertinents par "
    "un système de mots-clés. Ta tâche : repérer ceux qui décrivent en "
    "réalité un cas concret de répression, de violation des droits "
    "humains, ou de pression sur un·e activiste/journaliste/défenseur "
    "des droits — même si la formulation est indirecte ou inhabituelle. "
    "Ignore la géopolitique générale, l'économie, le sport, et les "
    "communiqués institutionnels génériques (rapports, appels à "
    "financement, pages de navigation).\n\n"
    "Réponds UNIQUEMENT avec un objet JSON de cette forme, sans aucun "
    "texte autour :\n"
    '{"flagged": [{"n": <numéro de l\'article>, "reason": '
    '"<raison en une phrase>"}]}\n'
    "Si aucun article ne doit être signalé, réponds "
    '{"flagged": []}.'
)


@dataclass
class AuditArticle:
    index: int
    title: str
    summary: str
    url: str
    source: str
    score: Any
    level: str


def load_articles(
    path: str,
    levels: set[str] | None,
) -> list[AuditArticle]:
    """
    Lit articles.csv (voir build_csv_rows/export_csv dans
    news_scanner.py) et ne garde que les niveaux demandés — par défaut
    D+E, puisque A/B/C sont déjà des cas confiants qu'il est inutile de
    ré-auditer. Passer levels=None pour couvrir 100% du corpus, sans
    aucun filtre de niveau.
    """
    articles: list[AuditArticle] = []

    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)

        for index, row in enumerate(reader):
            level = (row.get("level") or "E").strip()

            if levels is not None and level not in levels:
                continue

            articles.append(
                AuditArticle(
                    index=index,
                    title=(row.get("title") or "").strip(),
                    summary=(row.get("summary") or "").strip(),
                    url=(row.get("url") or "").strip(),
                    source=(row.get("source") or "").strip(),
                    score=row.get("score") or "",
                    level=level,
                )
            )

    return articles


def build_batches(
    articles: list[AuditArticle],
    batch_size: int,
) -> list[list[AuditArticle]]:
    return [
        articles[start:start + batch_size]
        for start in range(0, len(articles), batch_size)
    ]


def build_user_prompt(
    batch: list[AuditArticle],
    max_summary_chars: int,
) -> str:
    lines = []

    for position, article in enumerate(batch, start=1):
        snippet = article.summary[:max_summary_chars]
        line = f"{position}. {article.title}"
        if snippet:
            line += f" — {snippet}"
        lines.append(line)

    return "\n".join(lines)


def call_llm(
    base_url: str,
    api_key: str,
    model: str,
    batch: list[AuditArticle],
    max_summary_chars: int,
    temperature: float,
    timeout: int,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": 800,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(batch, max_summary_chars),
            },
        ],
    }

    response = requests.post(
        url, headers=headers, json=payload, timeout=timeout
    )
    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"] or ""


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_flagged(
    raw_text: str,
    batch: list[AuditArticle],
) -> list[tuple[AuditArticle, str]]:
    """
    Extrait les articles signalés depuis la réponse du modèle. Robuste
    à une réponse enveloppée dans un bloc de code markdown ou précédée
    de texte parasite : on prend le premier bloc "{...}" trouvé plutôt
    que d'exiger que la réponse soit un JSON pur.
    """
    match = _JSON_OBJECT_RE.search(raw_text)
    if not match:
        return []

    try:
        parsed = json.loads(match.group(0))
    except (ValueError, TypeError):
        return []

    flagged_entries = parsed.get("flagged")
    if not isinstance(flagged_entries, list):
        return []

    results: list[tuple[AuditArticle, str]] = []

    for entry in flagged_entries:
        if not isinstance(entry, dict):
            continue

        position = entry.get("n")
        if not isinstance(position, int) or not (1 <= position <= len(batch)):
            continue

        reason = str(entry.get("reason") or "").strip()
        results.append((batch[position - 1], reason))

    return results


def run_audit(
    input_path: str,
    output_path: str,
    levels: set[str] | None,
    batch_size: int,
    base_url: str,
    api_key: str,
    model: str,
    max_summary_chars: int,
    temperature: float,
    timeout: int,
) -> None:
    articles = load_articles(input_path, levels)
    batches = build_batches(articles, batch_size)

    print(
        f"AUDIT | {len(articles)} articles à auditer, "
        f"{len(batches)} lots de {batch_size}"
    )

    flagged_total: list[tuple[AuditArticle, str]] = []
    failed_batches = 0

    started = time.perf_counter()

    for batch_number, batch in enumerate(batches, start=1):
        try:
            raw_text = call_llm(
                base_url=base_url,
                api_key=api_key,
                model=model,
                batch=batch,
                max_summary_chars=max_summary_chars,
                temperature=temperature,
                timeout=timeout,
            )
            flagged = parse_flagged(raw_text, batch)
            flagged_total.extend(flagged)
        except Exception as exc:
            failed_batches += 1
            print(
                f"WARNING | lot {batch_number}/{len(batches)} | "
                f"ERREUR | {type(exc).__name__}: {exc}"
            )
            continue

        if flagged:
            print(
                f"AUDIT | lot {batch_number}/{len(batches)} | "
                f"{len(flagged)} article(s) signalé(s)"
            )

        if batch_number % 10 == 0 or batch_number == len(batches):
            elapsed = time.perf_counter() - started
            print(
                f"AUDIT | {batch_number}/{len(batches)} lots traités | "
                f"{elapsed:.0f}s écoulées | "
                f"{len(flagged_total)} signalé(s) au total"
            )

    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "title", "url", "source", "current_score",
                "current_level", "llm_reason",
            ],
        )
        writer.writeheader()

        for article, reason in flagged_total:
            writer.writerow(
                {
                    "title": article.title,
                    "url": article.url,
                    "source": article.source,
                    "current_score": article.score,
                    "current_level": article.level,
                    "llm_reason": reason,
                }
            )

    total_elapsed = time.perf_counter() - started
    print(
        f"AUDIT | terminé | {len(flagged_total)} candidats signalés | "
        f"{failed_batches} lot(s) en échec | {total_elapsed:.0f}s | "
        f"rapport : {output_path}"
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="articles.csv")
    parser.add_argument("--output", default="llm_audit_report.csv")
    parser.add_argument(
        "--levels",
        default="D,E",
        help='Niveaux à auditer, séparés par des virgules (ex: "D,E"), '
             'ou "ALL" pour couvrir 100% du corpus sans filtre.',
    )
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--model", default="qwen2.5-3b-instruct")
    parser.add_argument(
        "--max-summary-chars", type=int, default=DEFAULT_MAX_SUMMARY_CHARS
    )
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    levels = (
        None
        if args.levels.strip().upper() == "ALL"
        else {level.strip().upper() for level in args.levels.split(",")}
    )

    run_audit(
        input_path=args.input,
        output_path=args.output,
        levels=levels,
        batch_size=args.batch_size,
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
        max_summary_chars=args.max_summary_chars,
        temperature=args.temperature,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    sys.exit(main())
