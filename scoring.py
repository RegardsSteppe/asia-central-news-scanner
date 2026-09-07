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
)


def normalize(text):
    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(text),
    ).strip().lower()


def phrase_present(
    text,
    phrase,
):
    if not text or not phrase:
        return False

    pattern = (
        r"(?<!\w)"
        + re.escape(
            phrase.lower()
        )
        + r"(?!\w)"
    )

    return bool(
        re.search(
            pattern,
            text,
        )
    )


def find_terms(
    text,
    terms,
):
    return [
        term
        for term in terms
        if phrase_present(
            text,
            term,
        )
    ]


def classify_article(
    article,
):
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

    # --------------------------------------------------------
    # IMPORTANT
    #
    # Le titre + résumé sont prioritaires.
    #
    # Le body sert surtout à confirmer un article.
    # Cela évite qu'une page contenant une liste
    # d'articles contamine tous les résultats.
    # --------------------------------------------------------

    headline = (
        title
        + " "
        + summary[:3000]
    )

    full_text = (
        headline
        + " "
        + body[:12000]
    )

    # --------------------------------------------------------
    # GÉOGRAPHIE
    # --------------------------------------------------------

    central_asia = find_terms(
        headline,
        CENTRAL_ASIA_TERMS,
    )

    caucasus = find_terms(
        headline,
        CAUCASUS_TERMS,
    )

    geography = (
        central_asia
        + caucasus
    )

    # --------------------------------------------------------
    # SIGNAUX
    # --------------------------------------------------------

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
    # CONFIRMATION PAR LE CORPS
    # ========================================================

    body_repression = find_terms(
        body,
        REPRESSION_TERMS,
    )

    body_specific_rights = find_terms(
        body,
        SPECIFIC_RIGHTS_TERMS,
    )

    body_human_rights = find_terms(
        body,
        HUMAN_RIGHTS_TERMS,
    )

    # On ne considère le body comme confirmation
    # que s'il contient aussi une géographie.
    body_has_geography = bool(
        find_terms(
            body,
            CENTRAL_ASIA_TERMS
            + CAUCASUS_TERMS,
        )
    )

    confirmed_repression = (
        body_has_geography
        and bool(
            body_repression
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
    # DROITS HUMAINS GÉNÉRAUX
    #
    # Un simple "journalist" ne vaut que +2.
    # Il faut un contexte de répression pour faire
    # exploser le score.
    # --------------------------------------------------------

    if human_rights:

        if (
            "journalist" in human_rights
            or "journalists" in human_rights
            or "activist" in human_rights
            or "activists" in human_rights
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
    # CONFIRMATION PAR L'ARTICLE
    # --------------------------------------------------------

    if confirmed_repression:

        score += 5

        reasons.append(
            "confirmation article: "
            "répression"
        )

    elif confirmed_rights:

        score += 3

        reasons.append(
            "confirmation article: "
            "droits humains"
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
    # CONTENU NON JOURNALISTIQUE
    # --------------------------------------------------------

    if non_news:

        # On garde l'article dans l'audit,
        # mais il ne peut pas être présenté
        # comme une actualité importante.
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
    # CAS SPÉCIAUX
    # ========================================================

    # --------------------------------------------------------
    # ARTICLE JOURNALISTES + RÉPRESSION
    #
    # Criminal Cases, Travel Bans...
    # doit arriver à 20/20.
    # --------------------------------------------------------

    journalist_pressure = (
        (
            "journalist" in repression
            or "journalists" in repression
        )
        and bool(
            repression
        )
    )

    if journalist_pressure:
        score = max(
            score,
            20,
        )

        reasons.append(
            "forte pression sur les journalistes"
        )

    # --------------------------------------------------------
    # FEMMES / LGBT / MINORITÉS
    #
    # Un article traitant concrètement d'une
    # condamnation, arrestation ou répression
    # doit devenir prioritaire.
    # --------------------------------------------------------

    serious_specific_rights = (
        bool(
            specific_rights
        )
        and bool(
            repression
        )
    )

    if serious_specific_rights:

        score = max(
            score,
            20,
        )

        reasons.append(
            "atteinte grave à des droits spécifiques"
        )

    # ========================================================
    # LIMITATION
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

    # A = droits humains / répression
    if (
        geography
        and (
            repression
            or serious_specific_rights
            or confirmed_repression
        )
    ):

        level = "A"

    # C = géopolitique majeure
    elif (
        geography
        and major_geo
    ):

        level = "C"

    # B = politique intérieure
    elif (
        geography
        and domestic
    ):

        level = "B"

    else:

        level = "D"

    # Les contenus non journalistiques
    # restent toujours D.
    if non_news:
        level = "D"

    # ========================================================
    # THÈME
    # ========================================================

    if level == "A":
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
        bool(
            geography
        )
        and score >= 10
        and not non_news
        and not noise
    )

    article["score"] = score
    article["level"] = level
    article["theme"] = theme
    article["reasons"] = reasons
    article["relevant"] = relevant

    return article
