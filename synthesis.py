from __future__ import annotations

import re
from typing import Any

# Petit modèle instruct quantifié (GGUF), multilingue, choisi pour
# tourner en CPU-only sur un runner GitHub Actions standard (pas de GPU)
# en un temps raisonnable. Téléchargé et mis en cache par huggingface_hub
# au premier appel.
#
# Passé de 1.5B à 3B après un premier test réel : le 1.5B, avec des
# instructions un peu chargées (plusieurs négations : "ne pas juger",
# "ne pas inventer"...) et des articles sans résumé (fréquent — voir
# _build_messages), a répondu par un refus/méta-commentaire au lieu
# d'une synthèse. Le 3B reste léger mais suit mieux les instructions.
MODEL_REPO = "Qwen/Qwen2.5-3B-Instruct-GGUF"
MODEL_FILENAME = "*q4_k_m.gguf"

MAX_ARTICLES = 15
MAX_SUMMARY_CHARS = 400
MAX_OUTPUT_TOKENS = 400

_SYSTEM_PROMPT = (
    "Tu rédiges un court briefing factuel pour une veille sur les droits "
    "humains et la sécurité en Asie centrale et au Caucase. Tu reçois une "
    "liste de titres d'articles, parfois accompagnés d'un court extrait. "
    "Rédige toujours une synthèse en français de 3 à 5 phrases, même si "
    "les extraits sont courts ou absents : dans ce cas, base-toi "
    "uniquement sur les titres. Ne refuse jamais la tâche, ne commente "
    "jamais la qualité des articles fournis, et ne produis que la "
    "synthèse elle-même, sans préambule ni conclusion générique."
)

# Un seul exemple suffit à ancrer le format attendu pour un petit
# modèle — ça réduit nettement le risque de réponse hors-sujet/refus.
_EXAMPLE_USER = (
    "Articles :\n"
    "- Journalist sentenced to 5 years — A court in Bishkek sentenced the "
    "journalist over reporting critical of the government.\n"
    "- Activist detained in Almaty"
)
_EXAMPLE_ASSISTANT = (
    "Un journaliste a été condamné à cinq ans de prison à Bichkek pour "
    "des articles critiques envers le gouvernement, tandis qu'un "
    "activiste a été arrêté à Almaty. Ces deux cas illustrent la "
    "pression continue exercée sur les voix critiques en Asie centrale."
)

# Signaux d'un refus/méta-commentaire plutôt qu'une vraie synthèse —
# filet de sécurité si le prompt ne suffit pas à l'éviter.
_REFUSAL_PATTERNS = (
    "je ne peux pas",
    "je suis désolé",
    "i cannot",
    "i'm sorry",
    "in am unable",
    "je ne suis pas en mesure",
)

_model = None


def _load_model() -> Any:
    global _model

    if _model is not None:
        return _model

    from llama_cpp import Llama

    _model = Llama.from_pretrained(
        repo_id=MODEL_REPO,
        filename=MODEL_FILENAME,
        n_ctx=4096,
        verbose=False,
    )

    return _model


def _build_messages(articles: list[dict[str, Any]]) -> list[dict[str, str]]:
    lines = []

    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary") or article.get("body", "")

        if summary:
            lines.append(f"- {title} — {summary[:MAX_SUMMARY_CHARS]}")
        else:
            lines.append(f"- {title}")

    articles_block = "\n".join(lines)

    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _EXAMPLE_USER},
        {"role": "assistant", "content": _EXAMPLE_ASSISTANT},
        {"role": "user", "content": f"Articles :\n{articles_block}"},
    ]


def _looks_like_refusal(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in _REFUSAL_PATTERNS)


def generate_synthesis(
    articles: list[dict[str, Any]],
    max_articles: int = MAX_ARTICLES,
) -> str:
    """
    Génère une synthèse combinée à partir des articles fournis (les
    niveaux A du jour). Ne doit jamais faire échouer le scan : toute
    erreur (modèle indisponible, téléchargement échoué...) ou réponse
    qui ressemble à un refus est journalisée et une chaîne vide est
    retournée plutôt que de publier un méta-commentaire du modèle.
    """
    if not articles:
        return ""

    selected = articles[:max_articles]

    try:
        model = _load_model()
        messages = _build_messages(selected)

        response = model.create_chat_completion(
            messages=messages,
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.3,
        )

        text = (response["choices"][0]["message"]["content"] or "").strip()

        if _looks_like_refusal(text):
            print(
                "WARNING | synthesis | le modèle a renvoyé un refus/"
                "méta-commentaire, synthèse ignorée"
            )
            return ""

        return text

    except Exception as exc:
        print(f"WARNING | synthesis | ERROR | {type(exc).__name__}: {exc}")
        return ""
