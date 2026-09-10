from __future__ import annotations

from typing import Any

# Petit modèle instruct quantifié (GGUF), multilingue, choisi pour
# tourner en CPU-only sur un runner GitHub Actions standard (pas de GPU)
# en un temps raisonnable. Téléchargé et mis en cache par huggingface_hub
# au premier appel.
MODEL_REPO = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
MODEL_FILENAME = "*q4_k_m.gguf"

MAX_ARTICLES = 15
MAX_SUMMARY_CHARS = 400
MAX_OUTPUT_TOKENS = 400

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


def _build_prompt(articles: list[dict[str, Any]]) -> str:
    lines = []

    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary") or article.get("body", "")
        lines.append(f"- {title} : {summary[:MAX_SUMMARY_CHARS]}")

    articles_block = "\n".join(lines)

    return (
        "Tu es un assistant qui rédige des synthèses factuelles pour une "
        "veille sur les droits humains et la sécurité en Asie centrale et "
        "au Caucase. À partir des articles suivants (les plus critiques "
        "du jour), rédige UNE synthèse en français de 3 à 5 phrases, "
        "factuelle et sans jugement, qui résume les développements "
        "principaux. N'invente aucun fait absent des articles ci-dessous.\n\n"
        f"Articles :\n{articles_block}\n\n"
        "Synthèse :"
    )


def generate_synthesis(
    articles: list[dict[str, Any]],
    max_articles: int = MAX_ARTICLES,
) -> str:
    """
    Génère une synthèse combinée à partir des articles fournis (les
    niveaux A du jour). Ne doit jamais faire échouer le scan : toute
    erreur (modèle indisponible, téléchargement échoué...) est
    journalisée et une chaîne vide est retournée.
    """
    if not articles:
        return ""

    selected = articles[:max_articles]

    try:
        model = _load_model()
        prompt = _build_prompt(selected)

        response = model.create_chat_completion(
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.3,
        )

        text = response["choices"][0]["message"]["content"]
        return (text or "").strip()

    except Exception as exc:
        print(f"WARNING | synthesis | ERROR | {type(exc).__name__}: {exc}")
        return ""
