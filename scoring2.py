from __future__ import annotations

import re

from keywords2 import (
    CENTRAL_ASIA_TERMS,
    DIPLOMACY_TERMS,
    DIPLOMACY_WEIGHTS,
    ENERGY_CONNECTIVITY_TERMS,
    ENERGY_WEIGHTS,
    GREAT_POWER_TERMS,
    GREAT_POWER_WEIGHTS,
    LOW_SIGNAL_TERMS,
    NOISE_TERMS,
    SECURITY_TERMS,
    SECURITY_WEIGHTS,
)


def normalize(text: object) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def phrase_present(text: str, phrase: str) -> bool:
    if not text or not phrase:
        return False
    return bool(
        re.search(r"(?<!\w)" + re.escape(normalize(phrase)) + r"(?!\w)", text)
    )


def find_terms(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if phrase_present(text, term)]


def weighted_score(terms: list[str], weights: dict[str, int], maximum: int) -> int:
    score = sum(weights.get(normalize(term), 2) for term in terms)
    return min(score, maximum)


def classify_article(article: dict[str, object]) -> dict[str, object]:
    title = normalize(article.get("title", ""))
    summary = normalize(article.get("summary", ""))
    body = normalize(article.get("body", ""))
    url = normalize(article.get("url", ""))

    headline = f"{title} {summary}".strip()
    full_text = f"{headline} {body}".strip()

    geography_terms = find_terms(full_text, CENTRAL_ASIA_TERMS)
    security_terms = find_terms(full_text, SECURITY_TERMS)
    energy_terms = find_terms(full_text, ENERGY_CONNECTIVITY_TERMS)
    diplomacy_terms = find_terms(full_text, DIPLOMACY_TERMS)
    power_terms = find_terms(full_text, GREAT_POWER_TERMS)
    low_signal_terms = find_terms(full_text, LOW_SIGNAL_TERMS)
    noise_terms = find_terms(full_text, NOISE_TERMS)

    reasons: list[str] = []

    geography_score = 0
    if geography_terms:
        geography_score = min(25, 10 + len(geography_terms) * 3)
        reasons.append("Ancrage régional: " + ", ".join(geography_terms[:4]))
    elif "/central-asia/" in url:
        geography_score = 12
        reasons.append("Section Hudson Institute Central Asia")

    security_score = weighted_score(security_terms, SECURITY_WEIGHTS, 25)
    energy_score = weighted_score(energy_terms, ENERGY_WEIGHTS, 20)
    diplomacy_score = weighted_score(diplomacy_terms, DIPLOMACY_WEIGHTS, 20)
    power_score = weighted_score(power_terms, GREAT_POWER_WEIGHTS, 15)
    framing_score = min(8, len(low_signal_terms) * 2)

    if security_terms:
        reasons.append("Sécurité / stratégie")
    if energy_terms:
        reasons.append("Énergie / connectivité")
    if diplomacy_terms:
        reasons.append("Diplomatie / institutions")
    if power_terms:
        reasons.append("Compétition entre puissances")

    score = (
        geography_score
        + security_score
        + energy_score
        + diplomacy_score
        + power_score
        + framing_score
    )

    penalties = 0
    if noise_terms:
        penalties += 20
        reasons.append("Format non prioritaire")

    if geography_score == 0:
        penalties += 15
        reasons.append("Pas d'ancrage clair Asie centrale")

    score = max(0, min(100, round(score - penalties)))

    if score >= 75:
        level = "A"
        priority = "TRÈS HAUTE"
    elif score >= 55:
        level = "B"
        priority = "HAUTE"
    elif score >= 35:
        level = "C"
        priority = "MOYENNE"
    else:
        level = "D"
        priority = "FAIBLE"

    theme_scores = {
        "Sécurité régionale": security_score,
        "Énergie et connectivité": energy_score,
        "Diplomatie et institutions": diplomacy_score,
        "Compétition géopolitique": power_score,
    }
    theme = max(theme_scores, key=theme_scores.get)
    if all(value == 0 for value in theme_scores.values()):
        theme = "Veille Hudson Institute"

    relevant = bool(score >= 35 and geography_score > 0)

    article["score"] = score
    article["level"] = level
    article["priority"] = priority
    article["theme"] = theme
    article["relevant"] = relevant
    article["reasons"] = reasons
    article["signals"] = {
        "central_asia": geography_terms,
        "security_terms": security_terms,
        "energy_terms": energy_terms,
        "diplomacy_terms": diplomacy_terms,
        "power_terms": power_terms,
        "low_signal_terms": low_signal_terms,
        "noise_terms": noise_terms,
        "geography_score": geography_score,
        "target_score": security_score,
        "repression_score": 0,
        "rights_score": 0,
        "journalism_score": diplomacy_score,
        "geopolitical_score": power_score + energy_score,
        "freshness_score": 0,
        "penalties": penalties,
    }
    return article
