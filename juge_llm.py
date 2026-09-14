"""
juge_llm.py — un SECOND AVIS sur la pertinence d'un article, pas une
vérité.

Le nom compte, parce que la confusion coûterait cher. Un LLM qui juge
6800 articles produit une opinion avec ses propres biais : il est
généreux sur tout ce qui ressemble à des droits humains, faible sur la
géographie (il confond volontiers Asie centrale et Moyen-Orient), et
sensible à la langue de l'article. Si on calait scoring.py dessus, on
optimiserait vers ses erreurs, et on en sortirait avec un scanner qui
imite un modèle au lieu de faire le travail.

Ce à quoi il sert vraiment : trouver les DÉSACCORDS. Étiqueter 6800
articles à la main est hors de portée ; arbitrer les ~200 cas où le
scoring déterministe et ce juge divergent tient en une soirée. Ces
arbitrages-là, eux, sont une vérité terrain — voir verite_terrain.py.

Le modèle est appelé exactement comme dans synthesis.py (import
paresseux de llama_cpp, modèle GGUF quantifié), pour que le projet
n'ait qu'une seule façon de faire tourner un LLM.
"""

from __future__ import annotations

import json
import re
from typing import Any

# Même famille que synthesis.py. Le juge lit des articles en 4 langues
# (anglais, russe, français, farsi) : un modèle multilingue n'est pas
# optionnel ici.
MODEL_REPO = "Qwen/Qwen2.5-3B-Instruct-GGUF"
MODEL_FILENAME = "*q4_k_m.gguf"

MAX_TEXT_CHARS = 2400
MAX_OUTPUT_TOKENS = 200

CONFIANCES = ("haute", "moyenne", "basse")

# Le périmètre est décrit en toutes lettres plutôt que renvoyé à
# regles_editoriales.py : le juge doit rester un avis INDÉPENDANT. S'il
# appliquait les mêmes règles que le scanner, il ne pourrait plus le
# contredire, et l'exercice n'aurait aucun intérêt.
_SYSTEM_PROMPT = (
    "Tu es documentaliste pour une veille sur les droits humains en Asie "
    "centrale (Kazakhstan, Ouzbékistan, Kirghizistan, Tadjikistan, "
    "Turkménistan), dans le Caucase (Azerbaïdjan, Arménie, Géorgie, "
    "Caucase du Nord) et sur la question ouïghoure au Xinjiang.\n\n"
    "On te donne un article. Tu réponds à une seule question : cette "
    "veille doit-elle le retenir ?\n\n"
    "Retiens un article qui documente, dans cette région, une atteinte "
    "aux droits humains ou une pression sur la société civile : "
    "arrestation, détention, condamnation, torture, disparition, "
    "censure, pression sur des journalistes, des avocats, des "
    "défenseurs des droits, des opposants, des minorités ou des "
    "croyants, travail forcé, répression transnationale.\n\n"
    "Écarte le reste : sport, culture, météo, économie ordinaire, "
    "diplomatie de routine, faits divers sans dimension politique, "
    "pages de navigation sans contenu. Écarte aussi ce qui concerne une "
    "autre région, même s'il s'agit de droits humains.\n\n"
    "Réponds UNIQUEMENT par un objet JSON, sans texte autour :\n"
    '{"pertinent": true|false, "raison": "<une phrase courte>", '
    '"confiance": "haute"|"moyenne"|"basse"}\n\n'
    "Mets \"basse\" si le titre est ambigu ou si le texte fourni ne "
    "suffit pas à trancher."
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
        # -1 = toutes les couches déchargées sur le GPU. Sans ce
        # paramètre, un binaire compilé avec le support CUDA (voir
        # Dockerfile.juge) tourne quand même entièrement sur CPU — la
        # compilation active la capacité, ce paramètre l'utilise.
        # Inoffensif sur un environnement sans GPU : llama.cpp retombe
        # alors sur le CPU de lui-même.
        n_gpu_layers=-1,
        verbose=False,
    )

    return _model


def construire_invite(article: dict[str, Any]) -> list[dict[str, str]]:
    """Messages envoyés au modèle pour un article."""
    titre = (article.get("title") or "").strip()
    texte = (article.get("summary") or "").strip()

    if not texte:
        texte = (article.get("body") or "").strip()

    source = (article.get("source") or "").strip()

    bloc = f"Titre : {titre}"
    if source:
        bloc += f"\nSource : {source}"
    if texte:
        bloc += f"\nTexte : {texte[:MAX_TEXT_CHARS]}"

    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": bloc},
    ]


def analyser_reponse(texte: str) -> dict[str, Any]:
    """
    Extrait le verdict d'une réponse de modèle.

    Un petit modèle quantifié encadre régulièrement son JSON de prose ou
    de balises Markdown : on cherche donc le premier objet JSON plutôt
    que d'exiger une réponse parfaite. Un verdict illisible devient une
    erreur explicite, jamais un "non pertinent" par défaut — ça
    fausserait silencieusement toute la comparaison.
    """
    if not texte:
        return {"erreur": "réponse vide"}

    trouve = re.search(r"\{.*?\}", texte, re.S)
    if not trouve:
        return {"erreur": f"aucun JSON dans la réponse: {texte[:120]}"}

    try:
        brut = json.loads(trouve.group(0))
    except Exception as exc:
        return {"erreur": f"JSON invalide ({exc}): {trouve.group(0)[:120]}"}

    if not isinstance(brut, dict) or "pertinent" not in brut:
        return {"erreur": f"champ 'pertinent' absent: {trouve.group(0)[:120]}"}

    pertinent = brut.get("pertinent")
    if not isinstance(pertinent, bool):
        return {"erreur": f"'pertinent' n'est pas un booléen: {pertinent!r}"}

    confiance = str(brut.get("confiance", "")).strip().lower()
    if confiance not in CONFIANCES:
        confiance = "moyenne"

    return {
        "pertinent": pertinent,
        "raison": str(brut.get("raison", "")).strip()[:300],
        "confiance": confiance,
    }


def juger_article(article: dict[str, Any]) -> dict[str, Any]:
    """
    Verdict du juge pour un article. Ne lève jamais : une panne du
    modèle sur un article ne doit pas interrompre un lot de milliers.
    """
    try:
        modele = _load_model()
        reponse = modele.create_chat_completion(
            messages=construire_invite(article),
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.0,
        )
        texte = reponse["choices"][0]["message"]["content"]
    except Exception as exc:
        return {"erreur": f"{type(exc).__name__}: {exc}"}

    return analyser_reponse(texte)


def juger_lot(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Juge une liste d'articles. Chaque verdict porte la clé de l'article
    pour pouvoir être recroisé avec le scoring déterministe.
    """
    verdicts = []

    for index, article in enumerate(articles):
        verdict = juger_article(article)
        verdict["index"] = index
        verdict["cle"] = article.get("key") or article.get("url") or ""
        verdicts.append(verdict)

    return verdicts
