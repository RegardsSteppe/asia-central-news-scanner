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

    phrase = normalize(phrase)

    if not phrase:
        return False

    pattern = (
        r"(?<!\w)"
        + re.escape(phrase)
        + r"(?!\w)"
    )

    return bool(re.search(pattern, text))


def find_terms(text, terms):
    return [
        term
        for term in terms
        if phrase_present(text, term)
    ]


def unique_terms(*groups):
    result = []
    seen = set()

    for group in groups:
        for term in group:
            key = normalize(term)

            if key in seen:
                continue

            seen.add(key)
            result.append(term)

    return result


def capped_add(current, value, maximum):
    return min(
        current + value,
        maximum,
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_article(article):
    """
    Classe un article pour une veille :
        ASIE CENTRALE
        ACTIVISTES
        DROITS HUMAINS
        RÉPRESSION

    Score global : 0-100.

    Sous-scores :
        geography_score       /20
        activist_score        /25
        repression_score      /25
        rights_score          /15
        journalism_score      /10
        confirmation_score    /5

    Sortie :
        score
        level
        priority
        theme
        reasons
        relevant
        signals
    """

    title = normalize(
        article.get("title", "")
    )

    summary = normalize(
        article.get("summary", "")
    )

    body = normalize(
        article.get("body", "")
    )

    # --------------------------------------------------------
    # TEXTE
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

    # ========================================================
    # DÉTECTION DES SIGNAUX
    # ========================================================

    central_asia = find_terms(
        headline,
        CENTRAL_ASIA_TERMS,
    )

    caucasus = find_terms(
        headline,
        CAUCASUS_TERMS,
    )

    human_rights = find_terms(
        headline,
        HUMAN_RIGHTS_TERMS,
    )

    repression = find_terms(
        headline,
        REPRESSION_TERMS,
    )

    legal_repression = find_terms(
        headline,
        LEGAL_REPRESSION_TERMS,
    )

    specific_rights = find_terms(
        headline,
        SPECIFIC_RIGHTS_TERMS,
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
    # BODY — CONFIRMATION
    # ========================================================

    body_geography = find_terms(
        body,
        CENTRAL_ASIA_TERMS + CAUCASUS_TERMS,
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

    # ========================================================
    # RELATIONS IMPORTANTES
    # ========================================================

    has_repression = bool(
        repression
        or legal_repression
        or body_repression
        or body_legal_repression
    )

    has_activist = bool(
        activists
        or body_activists
    )

    has_journalist = bool(
        journalists
        or body_journalists
    )

    has_specific_rights = bool(
        specific_rights
        or body_specific_rights
    )

    has_human_rights = bool(
        human_rights
        or body_human_rights
    )

    confirmed_repression = (
        body_has_geography
        and has_repression
    )

    confirmed_rights = (
        body_has_geography
        and has_human_rights
    )

    # Activiste + répression
    activist_pressure = (
        has_activist
        and has_repression
    )

    # Journaliste + répression
    journalist_pressure = (
        has_journalist
        and has_repression
    )

    confirmed_activist_pressure = (
        body_has_geography
        and bool(body_activists)
        and bool(
            body_repression
            or body_legal_repression
        )
    )

    confirmed_journalist_pressure = (
        body_has_geography
        and bool(body_journalists)
        and bool(
            body_repression
            or body_legal_repression
        )
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

    # ========================================================
    # SOUS-SCORE 1 — GÉOGRAPHIE /20
    # ========================================================

    geography_score = 0
    reasons = []

    if central_asia:

        geography_score = 15

        reasons.append(
            "Asie centrale: "
            + ", ".join(
                central_asia[:6]
            )
        )

    elif caucasus:

        # Le Caucase est conservé mais moins prioritaire.
        geography_score = 5

        reasons.append(
            "Caucase: "
            + ", ".join(
                caucasus[:6]
            )
        )

    if central_asia and body_has_geography:

        geography_score = capped_add(
            geography_score,
            5,
            20,
        )

        reasons.append(
            "géographie confirmée dans le corps"
        )

    # ========================================================
    # SOUS-SCORE 2 — ACTIVISTES /25
    # ========================================================

    activist_score = 0

    if has_activist:

        if activist_pressure:
            activist_score = 20

        elif len(activists) >= 2:
            activist_score = 14

        else:
            activist_score = 10

        reasons.append(
            "activistes / dissidents: "
            + ", ".join(
                (activists or body_activists)[:8]
            )
        )

    # Société civile sans activiste individuel
    elif any(
        phrase_present(
            headline,
            term,
        )
        for term in [
            "civil society",
            "civil society organization",
            "civil society organizations",
            "ngo",
            "ngos",
        ]
    ):
        activist_score = 7

        reasons.append(
            "société civile / ONG"
        )

    if confirmed_activist_pressure:

        activist_score = capped_add(
            activist_score,
            5,
            25,
        )

        reasons.append(
            "activiste + répression confirmés"
        )

    # ========================================================
    # SOUS-SCORE 3 — RÉPRESSION /25
    # ========================================================

    repression_score = 0

    if repression:

        # Très grave
        severe_terms = {
            "torture",
            "tortured",
            "enforced disappearance",
            "forced disappearance",
            "forcibly disappeared",
            "political prisoner",
            "political prisoners",
            "political repression",
            "political crackdown",
            "opposition crackdown",
        }

        if any(
            normalize(term) in severe_terms
            for term in repression
        ):
            repression_score = 25

        # Arrestation / détention / prison
        elif any(
            word in normalize(term)
            for term in repression
            for word in [
                "arrest",
                "detain",
                "imprison",
                "jail",
                "prison",
                "convict",
            ]
        ):
            repression_score = 20

        # Autres formes sérieuses
        else:
            repression_score = 14

        reasons.append(
            "répression: "
            + ", ".join(
                repression[:8]
            )
        )

    elif legal_repression:

        repression_score = 14

        reasons.append(
            "répression juridique: "
            + ", ".join(
                legal_repression[:8]
            )
        )

    # Confirmation body
    if confirmed_repression:

        repression_score = capped_add(
            repression_score,
            5,
            25,
        )

        reasons.append(
            "répression confirmée dans le corps"
        )

    # ========================================================
    # SOUS-SCORE 4 — DROITS SPÉCIFIQUES /15
    # ========================================================

    rights_score = 0

    if specific_rights:

        normalized_rights = [
            normalize(term)
            for term in specific_rights
        ]

        if any(
            term in normalized_rights
            for term in [
                "lgbt",
                "lgbti",
                "lgbtq",
                "lgbt rights",
                "lgbti rights",
                "gay rights",
            ]
        ):
            rights_score = 15

        elif any(
            "violence against" in term
            or "sexual violence" in term
            or "forced labor" in term
            or "forced labour" in term
            for term in normalized_rights
        ):
            rights_score = 13

        elif any(
            "minority" in term
            or "discrimination" in term
            for term in normalized_rights
        ):
            rights_score = 11

        elif any(
            "women" in term
            or "gender" in term
            or "feminist" in term
            for term in normalized_rights
        ):
            rights_score = 10

        else:
            rights_score = 8

        reasons.append(
            "droits spécifiques: "
            + ", ".join(
                specific_rights[:8]
            )
        )

    elif has_human_rights:

        rights_score = 5

        reasons.append(
            "droits humains"
        )

    if confirmed_rights:

        rights_score = capped_add(
            rights_score,
            3,
            15,
        )

        reasons.append(
            "droits humains confirmés dans le corps"
        )

    # ========================================================
    # SOUS-SCORE 5 — IMPORTANCE JOURNALISTIQUE /10
    # ========================================================

    journalism_score = 0

    # Cas le plus intéressant :
    # activiste sous pression
    if activist_pressure:

        journalism_score = 10

    elif journalist_pressure:

        journalism_score = 9

    elif major_geo:

        journalism_score = 8

    elif domestic:

        journalism_score = 5

    elif has_human_rights:

        journalism_score = 5

    elif routine_geo:

        journalism_score = 2

    if major_geo:

        reasons.append(
            "géopolitique majeure: "
            + ", ".join(
                major_geo[:6]
            )
        )

    if domestic:

        reasons.append(
            "politique intérieure: "
            + ", ".join(
                domestic[:8]
            )
        )

    # ========================================================
    # SOUS-SCORE 6 — CONFIRMATION /5
    # ========================================================

    confirmation_score = 0

    if confirmed_activist_pressure:

        confirmation_score = 5

    elif confirmed_journalist_pressure:

        confirmation_score = 5

    elif confirmed_repression:

        confirmation_score = 4

    elif confirmed_rights:

        confirmation_score = 3

    elif body_has_geography:

        confirmation_score = 2

    # ========================================================
    # SCORE BRUT
    # ========================================================

    score = (
        geography_score
        + activist_score
        + repression_score
        + rights_score
        + journalism_score
        + confirmation_score
    )

    # ========================================================
    # PÉNALITÉS
    # ========================================================

    penalties = 0

    # Économie / géopolitique ordinaire
    if routine_geo and not (
        activist_pressure
        or journalist_pressure
        or has_specific_rights
    ):
        penalties += 8

        reasons.append(
            "géopolitique/économie ordinaire"
        )

    # Histoire / culture
    if historical and not (
        activist_pressure
        or journalist_pressure
        or confirmed_repression
    ):
        penalties += 12

        reasons.append(
            "histoire/culture"
        )

    # Acteur extérieur seul : faible valeur
    # Pas de pénalité directe, car il peut être pertinent.

    # ========================================================
    # NON-NEWS
    # ========================================================

    if non_news:

        score = min(
            score,
            5,
        )

        reasons.append(
            "contenu non journalistique: "
            + ", ".join(
                non_news[:8]
            )
        )

    # ========================================================
    # BRUIT
    # ========================================================

    if noise:

        score = 0

        reasons.append(
            "bruit: "
            + ", ".join(
                noise[:8]
            )
        )

    else:

        score -= penalties

    # ========================================================
    # BONUS ASIE CENTRALE + ACTIVISTE + RÉPRESSION
    # ========================================================

    # Cas cible de la veille.
    target_case = (
        bool(central_asia)
        and has_activist
        and has_repression
    )

    if target_case:

        # On s'assure que ce cas reste dans le haut
        # sans dépasser 100.
        score = max(
            score,
            80,
        )

        reasons.append(
            "cas prioritaire: Asie centrale + activiste + répression"
        )

    # ========================================================
    # BONUS SIGNAL SPÉCIFIQUE ASIE CENTRALE
    # ========================================================

    central_asia_hr_signal = bool(
        central_asia_hr
    )

    if central_asia_hr_signal:

        score += 5

        reasons.append(
            "signal spécifique Asie centrale: "
            + ", ".join(
                central_asia_hr[:8]
            )
        )

    # ========================================================
    # SCO — BONUS LIMITÉ
    # ========================================================

    if has_sco:

        score += 5

        reasons.append(
            "Organisation de coopération de Shanghai"
        )

    # ========================================================
    # BORNE 0-100
    # ========================================================

    score = max(
        0,
        min(
            score,
            100,
        ),
    )

    # ========================================================
    # NIVEAU ÉDITORIAL
    # ========================================================

    if (
        central_asia
        and activist_pressure
    ):
        level = "A"

    elif (
        central_asia
        and (
            confirmed_repression
            or confirmed_rights
            or journalist_pressure
            or has_specific_rights
        )
    ):
        level = "A"

    elif (
        central_asia
        and major_geo
    ):
        level = "C"

    elif (
        central_asia
        and domestic
    ):
        level = "B"

    else:
        level = "D"

    # Non-news toujours D
    if non_news:
        level = "D"

    # ========================================================
    # PRIORITÉ
    # ========================================================

    if score >= 90:

        priority = "ABSOLUE"

    elif score >= 75:

        priority = "TRÈS HAUTE"

    elif score >= 60:

        priority = "HAUTE"

    elif score >= 40:

        priority = "MOYENNE"

    elif score >= 20:

        priority = "FAIBLE"

    else:

        priority = "BRUIT"

    # ========================================================
    # THÈME
    # ========================================================

    if activist_pressure:

        theme = (
            "Activistes / dissidents sous pression"
        )

    elif journalist_pressure:

        theme = (
            "Journalistes sous pression"
        )

    elif confirmed_repression:

        theme = (
            "Répression / droits humains"
        )

    elif has_specific_rights:

        theme = (
            "Droits spécifiques"
        )

    elif domestic:

        theme = (
            "Politique intérieure"
        )

    elif major_geo:

        theme = (
            "Géopolitique majeure"
        )

    elif historical:

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
    # PERTINENCE
    # ========================================================

    relevant = (
        bool(central_asia)
        and score >= 40
        and not non_news
        and not noise
    )

    # Cas cible : toujours retenu
    if (
        target_case
        and not non_news
        and not noise
    ):
        relevant = True

    # ========================================================
    # SIGNALS — AUDIT
    # ========================================================

    signals = {

        # Géographie
        "central_asia": central_asia,
        "caucasus": caucasus,
        "body_geography": body_geography,

        # Activistes
        "activists": activists,
        "body_activists": body_activists,

        # Droits
        "human_rights": human_rights,
        "body_human_rights": body_human_rights,
        "specific_rights": specific_rights,
        "body_specific_rights": body_specific_rights,

        # Répression
        "repression": repression,
        "legal_repression": legal_repression,
        "body_repression": body_repression,
        "body_legal_repression": body_legal_repression,

        # Journalistes
        "journalists": journalists,
        "body_journalists": body_journalists,

        # Politique / géopolitique
        "domestic": domestic,
        "major_geo": major_geo,
        "routine_geo": routine_geo,
        "actors": actors,

        # Contexte
        "central_asia_hr": central_asia_hr,
        "historical": historical,
        "non_news": non_news,
        "noise": noise,

        # Relations
        "has_activist": has_activist,
        "has_journalist": has_journalist,
        "has_repression": has_repression,
        "has_specific_rights": has_specific_rights,
        "has_human_rights": has_human_rights,

        "confirmed_repression": confirmed_repression,
        "confirmed_rights": confirmed_rights,

        "activist_pressure": activist_pressure,
        "journalist_pressure": journalist_pressure,

        "confirmed_activist_pressure": (
            confirmed_activist_pressure
        ),

        "confirmed_journalist_pressure": (
            confirmed_journalist_pressure
        ),

        "target_case": target_case,

        "has_sco": has_sco,

        # Scores
        "geography_score": geography_score,
        "activist_score": activist_score,
        "repression_score": repression_score,
        "rights_score": rights_score,
        "journalism_score": journalism_score,
        "confirmation_score": confirmation_score,

        "penalties": penalties,
    }

    # ========================================================
    # SORTIE
    # ========================================================

    article["score"] = score
    article["level"] = level
    article["priority"] = priority
    article["theme"] = theme
    article["reasons"] = reasons
    article["relevant"] = relevant
    article["signals"] = signals

    return article
