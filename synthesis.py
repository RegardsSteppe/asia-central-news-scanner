from __future__ import annotations

import re
from datetime import datetime, timezone
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
MAX_SUMMARY_CHARS = 600
MAX_OUTPUT_TOKENS = 900

# La synthèse quotidienne doit couvrir l'actualité récente, pas un
# vieux rapport qui refait surface (ex. republié via le contournement
# Google News sur un site bloqué) : le score/niveau reste volontairement
# indifférent à l'âge (voir scoring.py), donc ce filtre est le seul
# endroit où la fraîcheur compte. Décidé avec l'utilisateur le
# 2026-09-11.
MAX_ARTICLE_AGE_DAYS = 14

_SYSTEM_PROMPT = (
    "Tu rédiges le briefing quotidien d'une veille sur les droits humains "
    "et la sécurité en Asie centrale, au Caucase et sur la question "
    "ouïghoure, dans le style factuel et précis d'une brève de Reporters "
    "sans frontières. Tu reçois une liste de titres d'articles, parfois "
    "accompagnés d'un court extrait. Traite en détail (2 à 4 phrases "
    "chacun) les cas les plus significatifs : nomme la personne, "
    "l'organisation ou le média concerné si l'information est "
    "disponible, le pays, ce qui s'est passé précisément (arrestation, "
    "condamnation, blocage, disparition...) et le contexte légal ou "
    "politique quand il est connu. Les cas moins centraux peuvent être "
    "regroupés plus brièvement en une phrase. Termine toujours par un "
    "court paragraphe d'analyse qui relie les cas du jour entre eux : "
    "tendance commune, pays le plus touché, ou signal à surveiller. "
    "Rédige toujours en français (même si les articles sont dans une "
    "autre langue), vise 200 à 350 mots, même si les extraits sont "
    "courts ou absents — dans ce cas, base-toi uniquement sur les "
    "titres. Ne refuse jamais la tâche, ne commente jamais la qualité "
    "des articles fournis, et ne produis que le briefing lui-même, sans "
    "préambule ni conclusion générique."
)

# Un seul exemple suffit à ancrer le format attendu pour un petit
# modèle — ça réduit nettement le risque de réponse hors-sujet/refus.
_EXAMPLE_USER = (
    "Articles :\n"
    "- Journalist sentenced to 5 years — A court in Bishkek sentenced the "
    "journalist over reporting critical of the government, following a "
    "trial his lawyers called politically motivated.\n"
    "- Activist detained in Almaty — Police detained the human rights "
    "activist after a peaceful rally, without disclosing formal charges.\n"
    "- Website blocked in Turkmenistan"
)
_EXAMPLE_ASSISTANT = (
    "Au Kirghizistan, un journaliste a été condamné à cinq ans de prison "
    "par un tribunal de Bichkek en raison d'articles critiques envers le "
    "gouvernement, à l'issue d'un procès que ses avocats qualifient de "
    "politiquement motivé. À Almaty, au Kazakhstan, un activiste des "
    "droits humains a été arrêté par la police à l'issue d'un "
    "rassemblement pacifique, sans qu'aucune charge précise n'ait été "
    "communiquée. Au Turkménistan, un site d'information a par ailleurs "
    "été bloqué, dans la continuité de la censure numérique pratiquée "
    "par les autorités.\n\n"
    "Ces trois cas, survenus dans des pays voisins, illustrent une "
    "pression continue sur les voix critiques en Asie centrale : la "
    "justice est utilisée pour museler la presse, la police pour "
    "dissuader la mobilisation citoyenne, et la censure numérique pour "
    "limiter l'accès à l'information indépendante. Cette convergence "
    "mérite d'être suivie dans les prochains jours."
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
        n_ctx=8192,
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


def _article_age_days(article: dict[str, Any], now: datetime) -> float | None:
    """
    Âge d'un article en jours, ou None si sa date est absente/invalide
    (dans ce cas on ne l'exclut pas de la synthèse : mieux vaut couvrir
    un article dont l'âge est inconnu que d'en écarter un qui serait en
    fait récent).
    """
    date = article.get("date")

    if not isinstance(date, datetime):
        return None

    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    return (now - date).total_seconds() / 86400


def generate_synthesis(
    articles: list[dict[str, Any]],
    max_articles: int = MAX_ARTICLES,
    max_age_days: float = MAX_ARTICLE_AGE_DAYS,
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

    now = datetime.now(timezone.utc)

    recent = []
    for article in articles:
        age_days = _article_age_days(article, now)
        if age_days is None or age_days <= max_age_days:
            recent.append(article)

    if not recent:
        return ""

    # Les cas les plus sévères passent en premier (et sont ceux
    # gardés si plus de max_articles niveau A récents dans la
    # journée) : le briefing doit couvrir en priorité les affaires les
    # plus graves, parmi celles qui sont réellement de l'actualité.
    ranked = sorted(
        recent, key=lambda article: article.get("score", 0), reverse=True
    )
    selected = ranked[:max_articles]

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
