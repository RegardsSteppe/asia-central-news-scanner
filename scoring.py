# scoring.py

import re

from keywords import (
    CENTRAL_ASIA_TERMS,
    CAUCASUS_TERMS,
    HUMAN_RIGHTS_TERMS,
    REPRESSION_TERMS,
    SPECIFIC_RIGHTS_TERMS,
    DOMESTIC_POLITICAL_TERMS,
    MAJOR_GEOPOLITICAL_TERMS,
    ROUTINE_GEO_TERMS,
    REGIONAL_ACTORS,
    HISTORICAL_TERMS,
    NON_NEWS_TERMS,
    NOISE_TERMS,
    LEGAL_REPRESSION_TERMS,
    JOURNALIST_TERMS,
    ACTIVIST_TERMS,
    CENTRAL_ASIA_HR_TERMS,
)


# ============================================================
# OUTILS
# ============================================================

def normalize(text):
    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(text),
    ).strip().lower()


def phrase_present(text, phrase):
    if not text or not phrase:
        return False

    phrase = str(phrase).strip().lower()

    if not phrase:
        return False

    pattern = (
        r"(?<!\w)"
        + re.escape(phrase)
        + r"(?!\w)"
    )

    return bool(
        re.search(
            pattern,
            text,
        )
    )


def find_terms(text, terms):
    found = []

    for term in terms:
        if phrase_present(
            text,
            term,
        ):
            found.append(term)

    return found


def unique_terms(*groups):
    result = []
    seen = set()

    for group in groups:
        for term in group:
            normalized = normalize(term)

            if normalized in seen:
                continue

            seen.add(normalized)
            result.append(term)

    return result


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_article(article):
    """
    Cerveau éditorial.

    Entrée :
        article = {
            "title": ...,
            "summary": ...,
            "body": ...
        }

    Sortie :
        article enrichi avec :
            score
            level
            theme
            reasons
            relevant
            signals
    """

    title = normalize(
        article.get(
            "title",
            "",
        )
    )

    summary = normalize(
        article.get(
            "summary",
            "",
        )
    )

    body = normalize(
        article.get(
            "body",
            "",
        )
    )

    # ========================================================
    # CONTEXTE
    # ========================================================

    # Le titre + résumé restent la base.
    # On limite le résumé pour éviter les pages polluées.
    headline = (
        title
        + " "
        + summary[:3000]
    )

    # Le body sert à confirmer.
    full_text = (
        headline
        + " "
        + body[:12000]
    )

    # ========================================================
    # GÉOGRAPHIE
    # ========================================================

    central_asia = find_terms(
        headline,
        CENTRAL_ASIA_TERMS,
    )

    caucasus = find_terms(
        headline,
        CAUCASUS_TERMS,
    )

    geography = unique_terms(
        central_asia,
        caucasus,
    )

    # ========================================================
    # SIGNAUX PRINCIPAUX
    # ========================================================

    human_rights = find_terms(
        headline,
        HUMAN_RIGHTS_TERMS,
    )

    repression = find_terms(
        headline,
        REPRESSION_TERMS,
    )

    specific_rights = find_terms(
        headline,
        SPECIFIC_RIGHTS_TERMS,
    )

    domestic = find_terms(
        headline,
        DOMESTIC_POLITICAL_TERMS,
    )

    major_geo = find_terms(
        headline,
        MAJOR_GEOPOLITICAL_TERMS,
    )

    routine_geo = find_terms(
        headline,
        ROUTINE_GEO_TERMS,
    )

    actors = find_terms(
        headline,
        REGIONAL_ACTORS,
    )

    historical = find_terms(
        headline,
        HISTORICAL_TERMS,
    )

    non_news = find_terms(
        headline,
        NON_NEWS_TERMS,
    )

    noise = find_terms(
        headline,
        NOISE_TERMS,
    )

    # ========================================================
    # NOUVEAUX SIGNAUX RH
    # ========================================================

    legal_repression = find_terms(
        headline,
        LEGAL_REPRESSION_TERMS,
    )

    journalists = find_terms(
        headline,
        JOURNALIST_TERMS,
    )

    activists = find_terms(
        headline,
        ACTIVIST_TERMS,
    )

    central_asia_hr = find_terms(
        headline,
        CENTRAL_ASIA_HR_TERMS,
    )

    # ========================================================
    # CONFIRMATION PAR LE BODY
    # ========================================================

    body_geography = find_terms(
        body,
        CENTRAL_ASIA_TERMS
        + CAUCASUS_TERMS,
    )

    body_repression = find_terms(
        body,
        REPRESSION_TERMS,
    )

    body_legal_repression = find_terms(
        body,
        LEGAL_REPRESSION_TERMS,
    )

    body_specific_rights = find_terms(
        body,
        SPECIFIC_RIGHTS_TERMS,
    )

    body_human_rights = find_terms(
        body,
        HUMAN_RIGHTS_TERMS,
    )

    body_journalists = find_terms(
        body,
        JOURNALIST_TERMS,
    )

    body_activists = find_terms(
        body,
        ACTIVIST_TERMS,
    )

    body_has_geography = bool(
        body_geography
    )

    confirmed_repression = (
        body_has_geography
        and bool(
            body_repression
            or body_legal_repression
        )
    )

    confirmed_rights = (
        body_has_geography
        and bool(
            body_specific_rights
            or body_human_rights
        )
    )

    # ========================================================
    # PRESSION SUR JOURNALISTES
    # ========================================================

    journalist_pressure = (
        bool(journalists)
        and bool(
            repression
            or legal_repression
            or body_journalists
            or body_repression
            or body_legal_repression
        )
    )

    # ========================================================
    # PRESSION SUR ACTIVISTES / DISSIDENTS
    # ========================================================

    activist_pressure = (
        bool(activists)
        and bool(
            repression
            or legal_repression
            or body_activists
            or body_repression
            or body_legal_repression
        )
    )

    # ========================================================
    # CAS RH CONFIRMÉ PAR LE BODY
    # ========================================================

    confirmed_journalist_pressure = (
        body_has_geography
        and bool(
            body_journalists
        )
        and bool(
            body_repression
            or body_legal_repression
        )
    )

    confirmed_activist_pressure = (
        body_has_geography
        and bool(
            body_activists
        )
        and bool(
            body_repression
            or body_legal_repression
        )
    )

    # ========================================================
    # DROITS SPÉCIFIQUES + RÉPRESSION
    # ========================================================

    serious_specific_rights = (
        bool(specific_rights)
        and bool(
            repression
            or legal_repression
        )
    )

    confirmed_specific_rights = (
        body_has_geography
        and bool(
            body_specific_rights
        )
        and bool(
            body_repression
            or body_legal_repression
        )
    )

    # ========================================================
    # SIGNAL RH CENTRAL ASIA
    # ========================================================

    central_asia_hr_signal = bool(
        central_asia_hr
    )

    # ========================================================
    # SCORE
    # ========================================================

    score = 0
    reasons = []

    # --------------------------------------------------------
    # GÉOGRAPHIE
    # --------------------------------------------------------

    if central_asia:
        score += 2

        reasons.append(
            "Asie centrale: "
            + ", ".join(
                central_asia[:5]
            )
        )

    if caucasus:
        score += 2

        reasons.append(
            "Caucase: "
            + ", ".join(
                caucasus[:5]
            )
        )

    # --------------------------------------------------------
    # DROITS HUMAINS
    # --------------------------------------------------------

    if human_rights:

        generic_people_terms = {
            "journalist",
            "journalists",
            "journaliste",
            "journalistes",
            "activist",
            "activists",
            "activiste",
            "activistes",
        }

        if any(
            normalize(term)
            in generic_people_terms
            for term in human_rights
        ):
            score += 2

        else:
            score += 5

        reasons.append(
            "droits humains: "
            + ", ".join(
                human_rights[:8]
            )
        )

    # --------------------------------------------------------
    # RÉPRESSION
    # --------------------------------------------------------

    if repression:
        score += 12

        reasons.append(
            "répression: "
            + ", ".join(
                repression[:8]
            )
        )

    # --------------------------------------------------------
    # PRESSION JUDICIAIRE / ADMINISTRATIVE
    # --------------------------------------------------------

    if legal_repression:
        score += 6

        reasons.append(
            "pression judiciaire: "
            + ", ".join(
                legal_repression[:8]
            )
        )

    # --------------------------------------------------------
    # JOURNALISTES
    # --------------------------------------------------------

    if journalists:
        score += 1

        reasons.append(
            "journalistes: "
            + ", ".join(
                journalists[:6]
            )
        )

    # --------------------------------------------------------
    # ACTIVISTES / DISSIDENTS
    # --------------------------------------------------------

    if activists:
        score += 1

        reasons.append(
            "activistes / dissidents: "
            + ", ".join(
                activists[:6]
            )
        )

    # --------------------------------------------------------
    # CENTRAL ASIA + DROITS HUMAINS
    # --------------------------------------------------------

    if central_asia_hr_signal:
        score += 3

        reasons.append(
            "signal droits humains Asie centrale: "
            + ", ".join(
                central_asia_hr[:8]
            )
        )

    # --------------------------------------------------------
    # DROITS SPÉCIFIQUES
    # --------------------------------------------------------

    if specific_rights:
        score += 8

        reasons.append(
            "droits spécifiques: "
            + ", ".join(
                specific_rights[:8]
            )
        )

    # --------------------------------------------------------
    # CONFIRMATION PAR LE BODY
    # --------------------------------------------------------

    if confirmed_repression:
        score += 5

        reasons.append(
            "confirmation article: répression"
        )

    elif confirmed_rights:
        score += 3

        reasons.append(
            "confirmation article: droits humains"
        )

    if confirmed_journalist_pressure:
        score += 4

        reasons.append(
            "confirmation article: journaliste sous pression"
        )

    if confirmed_activist_pressure:
        score += 4

        reasons.append(
            "confirmation article: activiste sous pression"
        )

    if confirmed_specific_rights:
        score += 4

        reasons.append(
            "confirmation article: atteinte à un droit spécifique"
        )

    # --------------------------------------------------------
    # POLITIQUE INTÉRIEURE
    # --------------------------------------------------------

    if domestic:
        score += 6

        reasons.append(
            "politique intérieure: "
            + ", ".join(
                domestic[:8]
            )
        )

    # --------------------------------------------------------
    # GÉOPOLITIQUE MAJEURE
    # --------------------------------------------------------

    if major_geo:
        score += 10

        reasons.append(
            "géopolitique majeure: "
            + ", ".join(
                major_geo[:6]
            )
        )

    # --------------------------------------------------------
    # ACTEURS EXTÉRIEURS
    # --------------------------------------------------------

    if actors:
        score += min(
            len(actors),
            2,
        )

        reasons.append(
            "acteur extérieur: "
            + ", ".join(
                actors[:6]
            )
        )

    # --------------------------------------------------------
    # GÉOPOLITIQUE ORDINAIRE
    # --------------------------------------------------------

    if routine_geo:
        score -= 5

        reasons.append(
            "géopolitique ordinaire: "
            + ", ".join(
                routine_geo[:6]
            )
        )

    # --------------------------------------------------------
    # HISTOIRE / CULTURE
    # --------------------------------------------------------

    if historical:
        score -= 8

        reasons.append(
            "histoire/culture: "
            + ", ".join(
                historical[:6]
            )
        )

    # --------------------------------------------------------
    # NON-NEWS
    # --------------------------------------------------------

    if non_news:
        score = min(
            score,
            8,
        )

        reasons.append(
            "contenu non journalistique: "
            + ", ".join(
                non_news[:8]
            )
        )

    # --------------------------------------------------------
    # BRUIT
    # --------------------------------------------------------

    if noise:
        score -= 10

        reasons.append(
            "bruit: "
            + ", ".join(
                noise[:6]
            )
        )

    # ========================================================
    # PRIORITÉ MAXIMALE RH
    # ========================================================

    high_priority_human_rights = (
        journalist_pressure
        or activist_pressure
        or serious_specific_rights
        or confirmed_journalist_pressure
        or confirmed_activist_pressure
        or confirmed_specific_rights
    )

    if high_priority_human_rights:
        score = max(
            score,
            20,
        )

        if journalist_pressure:
            reasons.append(
                "forte pression sur les journalistes"
            )

        if activist_pressure:
            reasons.append(
                "forte pression sur les activistes / dissidents"
            )

        if serious_specific_rights:
            reasons.append(
                "atteinte grave à des droits spécifiques"
            )

    # ========================================================
    # SCO
    # ========================================================

    has_sco = any(
        phrase_present(
            full_text,
            term,
        )
        for term in [
            "sco",
            "shanghai cooperation organization",
            "shanghai cooperation organisation",
            "sco summit",
        ]
    )

    if has_sco:
        score += 8

        reasons.append(
            "Organisation de coopération de Shanghai"
        )

    # ========================================================
    # SCORE FINAL
    # ========================================================

    score = max(
        0,
        min(
            score,
            20,
        ),
    )

    # ========================================================
    # NIVEAU
    # ========================================================

    # A : droits humains / répression
    if (
        geography
        and (
            repression
            or legal_repression
            or serious_specific_rights
            or confirmed_repression
            or journalist_pressure
            or activist_pressure
            or confirmed_journalist_pressure
            or confirmed_activist_pressure
            or confirmed_specific_rights
        )
    ):
        level = "A"

    # C : géopolitique majeure
    elif (
        geography
        and major_geo
    ):
        level = "C"

    # B : politique intérieure
    elif (
        geography
        and domestic
    ):
        level = "B"

    else:
        level = "D"

    # SCO peut transformer une actualité géopolitique
    # pertinente en C, mais jamais en A à lui seul.
    if (
        geography
        and has_sco
        and level == "D"
        and not non_news
    ):
        level = "C"

    # Non-news = toujours D.
    if non_news:
        level = "D"

    # ========================================================
    # THÈME
    # ========================================================

    if level == "A":

        if journalist_pressure:
            theme = (
                "Journalistes sous pression"
            )

        elif activist_pressure:
            theme = (
                "Activistes / dissidents sous pression"
            )

        elif serious_specific_rights:
            theme = (
                "Droits spécifiques / répression"
            )

        else:
            theme = (
                "Droits humains / répression"
            )

    elif level == "B":

        theme = (
            "Politique intérieure"
        )

    elif level == "C":

        theme = (
            "Géopolitique majeure"
        )

    else:

        if historical:

            theme = (
                "Histoire / culture / contexte"
            )

        elif non_news:

            theme = (
                "Contenu institutionnel"
            )

        elif routine_geo:

            theme = (
                "Économie / géopolitique ordinaire"
            )

        else:

            theme = (
                "Faible priorité"
            )

    # ========================================================
    # RETENU
    # ========================================================

    relevant = (
        bool(geography)
        and score >= 10
        and not non_news
        and not noise
        and level in {
            "A",
            "B",
            "C",
        }
    )

    # Un vrai cas RH confirmé reste prioritaire.
    if (
        geography
        and high_priority_human_rights
        and not non_news
        and not noise
    ):
        relevant = True

    # ========================================================
    # SIGNAUX POUR AUDIT / HTML
    # ========================================================

    signals = {
        "central_asia": central_asia,
        "caucasus": caucasus,
        "geography": geography,

        "human_rights": human_rights,
        "repression": repression,
        "legal_repression": legal_repression,

        "specific_rights": specific_rights,

        "journalists": journalists,
        "activists": activists,

        "central_asia_hr": central_asia_hr,

        "domestic": domestic,
        "major_geo": major_geo,
        "routine_geo": routine_geo,
        "actors": actors,

        "historical": historical,
        "non_news": non_news,
        "noise": noise,

        "body_geography": body_geography,
        "body_repression": body_repression,
        "body_legal_repression": body_legal_repression,
        "body_specific_rights": body_specific_rights,
        "body_human_rights": body_human_rights,
        "body_journalists": body_journalists,
        "body_activists": body_activists,

        "confirmed_repression": confirmed_repression,
        "confirmed_rights": confirmed_rights,

        "journalist_pressure": journalist_pressure,
        "activist_pressure": activist_pressure,

        "confirmed_journalist_pressure": (
            confirmed_journalist_pressure
        ),

        "confirmed_activist_pressure": (
            confirmed_activist_pressure
        ),

        "serious_specific_rights": (
            serious_specific_rights
        ),

        "confirmed_specific_rights": (
            confirmed_specific_rights
        ),

        "has_sco": has_sco,
    }

    # ========================================================
    # SORTIE
    # ========================================================

    article["score"] = score
    article["level"] = level
    article["theme"] = theme
    article["reasons"] = reasons
    article["relevant"] = relevant
    article["signals"] = signals

    return article
