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
    SEVERE_REPRESSION_TERMS,
    ACTIVIST_REPRESSION_PATTERNS,
    JOURNALIST_REPRESSION_PATTERNS,
    ACTIVIST_REPRESSION_RU_PATTERNS,
    JOURNALIST_REPRESSION_RU_PATTERNS,
    REPRESSION_WEIGHTS,
    SPECIFIC_RIGHTS_WEIGHTS,
    LEGAL_CONTEXT_TERMS,
    LOW_SIGNAL_CONTEXT_TERMS,
    HUMAN_RIGHTS_DEFENDER_TERMS,
    FORCED_LABOR_TERMS
)


# Signaux V7 volontairement courts et forts : utilisés pour déterminer
# si les droits humains constituent réellement le sujet principal.
REPRESSION_TERMS_V7 = [
    "torture", "tortured", "political prisoner", "political repression",
    "political crackdown", "under pressure", "under threat", "persecution",
    "pressure on journalists", "imprisoned", "imprisonment", "jailed",
    "behind bars", "prison sentence", "sentenced to prison", "sentenced",
    "arrested", "detained", "convicted", "convicts", "criminal prosecution",
    "censorship", "press freedom",
    "пытки", "пыточные условия", "шизо", "карцер", "политический заключенный",
    "политические репрессии", "преследование", "преследуют", "давление на журналистов",
    "за решеткой", "арестован", "задержан", "осужден", "осуждён", "приговорен",
    "заключен", "цензура", "содержится в шизо",
]

SPECIFIC_RIGHTS_TERMS_V7 = [
    "human rights violation", "human rights violations", "rights violation",
    "freedom of expression", "freedom of speech", "freedom of assembly",
    "press freedom", "media freedom", "women's rights", "gender discrimination",
    "gender-based violence", "violence against women", "forced marriage",
    "child marriage", "lgbt rights", "lgbti rights", "lgbt", "ethnic discrimination",
    "religious discrimination", "academic freedom", "academic censorship",
    "forced labor", "forced labour", "child labor", "child labour",
    "silent suffering", "violence against daughters-in-law",
    "права человека", "нарушение прав человека", "свобода слова", "свобода прессы",
    "права женщин", "гендерная дискриминация", "насилие в отношении женщин",
    "лgbt", "академическая свобода", "принудительный труд", "детский труд",
]

JOURNALIST_TERMS_V7 = [
    "journalist", "journalists", "reporter", "reporters", "журналист", "журналисты",
]

ACADEMIC_HR_TERMS_V7 = [
    "academic freedom", "academic censorship", "academic repression",
    "academic freedom at risk", "professor arrested", "professor detained",
    "scholar arrested", "scholar detained", "академическая свобода",
    "преследование ученых", "арест профессора", "задержание профессора",
]

GENERIC_REFORM_TERMS_V7 = [
    "democratic reform", "democratic reforms", "political reform", "political reforms",
    "development programs", "social stability", "constitutional reform",
    "political development", "political traditions",
]

NON_HR_TOPIC_TERMS_V7 = [
    "diaspora", "hidden economy", "travelogue", "night train", "dombra",
    "metallica", "k-pop", "hip-hop", "classical repertoire", "album",
    "music", "culture", "cultural", "tourism", "economic", "economy",
    "data center", "investors", "bonds", "gold reserves", "strategic partnership",
    "state visit", "sco summit", "nomad games",
]


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


def capped_add(current, value, maximum):
    return min(
        current + value,
        maximum,
    )


def contains_pattern(text, patterns):
    for pattern in patterns:
        if re.search(pattern, text):
            return True

    return False


def weighted_score(terms, weights, maximum):
    """
    Calcule un score pondéré sans double compter
    plusieurs occurrences du même signal.
    """
    score = 0

    for term in terms:
        normalized = normalize(term)

        value = weights.get(
            normalized,
            2,
        )

        score += value

    return min(
        score,
        maximum,
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_article(article):

    """
    Classification V7.

    Score global : 0-100

    Dimensions :

        geography_score       /15
        target_score          /20
        repression_score      /30
        rights_score          /10
        journalism_score      /10
        geopolitical_score    /10
        freshness_score       /5

        TOTAL                  /100
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

    # Source / URL: certains flux ont un titre sans pays,
    # mais le média est lui-même géographiquement spécialisé.
    source_text = normalize(
        article.get("source", "")
    )
    link_text = normalize(
        article.get("link", article.get("url", ""))
    )
    source_context = source_text + " " + link_text

    # --------------------------------------------------------
    # HEADLINE
    # --------------------------------------------------------

    headline = (
        title
        + " "
        + summary[:3000]
    ).strip()

    # --------------------------------------------------------
    # FULL TEXT
    # --------------------------------------------------------

    full_text = (
        headline
        + " "
        + body[:12000]
    ).strip()

    # V7 additional human-rights signals
    has_hr_defender = any(normalize(term) in full_text for term in HUMAN_RIGHTS_DEFENDER_TERMS)
    forced_labor_detected = any(normalize(term) in full_text for term in FORCED_LABOR_TERMS)
    has_detention = any(normalize(term) in full_text for term in [
        "detained", "detention", "arrested", "arrest", "задержан", "задержание", "арестован", "арест",
        "заключен", "заключена", "в заключении",
    ])
    has_imprisonment = any(normalize(term) in full_text for term in [
        "imprisoned", "imprisonment", "prison sentence", "sentenced to",
        "осужден", "осуждена", "приговорен", "приговорена", "лишения свободы",
    ])
    has_restriction = any(normalize(term) in full_text for term in [
        "restriction", "restrictions", "restricted access", "access restriction",
        "ограничение", "ограничения", "ограничен доступ", "запретили доступ",
    ])
    has_censorship = any(normalize(term) in full_text for term in [
        "censorship", "censored", "цензура", "цензур",
    ])
    has_government_involvement = any(normalize(term) in full_text for term in [
        "government", "authorities", "state", "government-backed", "ilo", "мот",
        "правительство", "власти", "государство", "государственный", "государственные",
    ])

    reasons = []

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

    # Signaux de géographie provenant de la source / URL.
    # Ils ne donnent pas de points à eux seuls : ils servent uniquement
    # à confirmer le contexte régional quand le titre ne nomme pas le pays.
    central_asia_source_terms = [
        "turkmen.news",
        "turkmen news",
        "the times of central asia",
        "times of central asia",
        "eurasianet",
        "eurasianet.org",
        "uzdaily",
        "kabar",
        "akipress",
        "gazeta.uz",
        "kun.uz",
        "fergana.agency",
        "fergana",
        "ozodlik",
        "radio free europe/ radio liberty",
        "radio free europe",
        "current time",
        "ca-news",
    ]
    central_asia_source = find_terms(
        source_context,
        central_asia_source_terms,
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

    legal_context = find_terms(
        headline,
        LEGAL_CONTEXT_TERMS,
    )

    low_signal_context = find_terms(
        headline,
        LOW_SIGNAL_CONTEXT_TERMS,
    )

    # ========================================================
    # BODY
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

    body_legal_context = find_terms(
        body,
        LEGAL_CONTEXT_TERMS,
    )

    body_geo_count = len(
        body_geography
    )

    body_has_geography = (
        body_geo_count >= 1
    )

    strong_body_geography = (
        body_geo_count >= 2
    )

    # ========================================================
    # RELATIONS
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

    has_legal_context = bool(
        legal_context
        or body_legal_context
    )

    # --------------------------------------------------------
    # Relation explicite activiste -> répression
    # --------------------------------------------------------

    activist_relation = (
        contains_pattern(
            headline,
            ACTIVIST_REPRESSION_PATTERNS,
        )
        or contains_pattern(
            body[:12000],
            ACTIVIST_REPRESSION_PATTERNS,
        )
        or contains_pattern(
            headline,
            ACTIVIST_REPRESSION_RU_PATTERNS,
        )
        or contains_pattern(
            body[:12000],
            ACTIVIST_REPRESSION_RU_PATTERNS,
        )
    )

    # --------------------------------------------------------
    # Relation explicite journaliste -> répression
    # --------------------------------------------------------

    journalist_relation = (
        contains_pattern(
            headline,
            JOURNALIST_REPRESSION_PATTERNS,
        )
        or contains_pattern(
            body[:12000],
            JOURNALIST_REPRESSION_PATTERNS,
        )
        or contains_pattern(
            headline,
            JOURNALIST_REPRESSION_RU_PATTERNS,
        )
        or contains_pattern(
            body[:12000],
            JOURNALIST_REPRESSION_RU_PATTERNS,
        )
    )

    # ========================================================
    # CONTEXTE RÉGIONAL
    # ========================================================
    # Doit être défini AVANT les confirmations qui l'utilisent.
    regional_context = bool(
        central_asia
        or body_has_geography
        or caucasus
        or central_asia_source
    )

    # ========================================================
    # SIGNALS GRAVES / MORPHOLOGIE RUSSE
    # ========================================================
    severe_morphology = bool(
        re.search(
            r"(?:пыточн(?:ые|ых|ом|ыми|ых)\s+услов(?:ия|иях|иям|иями)|\bшизо\b|\bкарцер\b|\bодиночн(?:ое|ом|ую)\s+заключен(?:ие|ии|ием)|произвольн(?:ое|ого|ому)\s+задержан(?:ие|ия|ием))",
            full_text,
            re.IGNORECASE,
        )
    )

    prison_sentence_signal = bool(
        re.search(
            r"(?:\b(?:8|9|10|11|12|13|14|15|16|17|18|19|20)\s*(?:лет|года|год|years?)\b.{0,80}\b(?:тюрьм|заключ|лишен|лишени)|\b(?:приговорен|осужден|осуждён)\b.{0,80}\b(?:лет|года|год)\b)",
            full_text,
            re.IGNORECASE,
        )
    )

    # ========================================================
    # CONFIRMATIONS
    # ========================================================

    confirmed_repression = (
        regional_context
        and bool(
            repression
            or legal_repression
            or body_repression
            or body_legal_repression
        )
    )

    confirmed_rights = (
        regional_context
        and bool(
            human_rights
            or specific_rights
            or body_human_rights
            or body_specific_rights
        )
    )

    confirmed_activist_pressure = (
        regional_context
        and activist_relation
    )

    confirmed_journalist_pressure = (
        regional_context
        and journalist_relation
    )

    # ========================================================
    # SOUS-SCORE 1 — GÉOGRAPHIE /15
    # ========================================================

    geography_score = 0

    if central_asia:

        geography_score = 12

        reasons.append(
            "Asie centrale: "
            + ", ".join(
                central_asia[:6]
            )
        )

    elif caucasus:

        geography_score = 3

        reasons.append(
            "Caucase: "
            + ", ".join(
                caucasus[:6]
            )
        )

    if central_asia and body_has_geography:

        geography_score = capped_add(
            geography_score,
            3,
            15,
        )

        reasons.append(
            "géographie confirmée dans le corps"
        )
    elif central_asia_source and not central_asia:
        geography_score = 10
        reasons.append(
            "source spécialisée Asie centrale: "
            + ", ".join(central_asia_source[:4])
        )

    # Caucase seul : plafond
    caucasus_only = (
        bool(caucasus)
        and not bool(central_asia)
    )

    # ========================================================
    # SOUS-SCORE 2 — CIBLE /20
    # ========================================================

    target_score = 0

    if confirmed_activist_pressure:

        target_score = 20

        reasons.append(
            "activiste / défenseur des droits ciblé"
        )

    elif confirmed_journalist_pressure:

        target_score = 18

        reasons.append(
            "journaliste / média ciblé"
        )

    elif activist_relation and central_asia:

        target_score = 16

        reasons.append(
            "relation activiste / répression détectée"
        )

    elif journalist_relation and central_asia:

        target_score = 15

        reasons.append(
            "relation journaliste / répression détectée"
        )

    elif has_activist:

        target_score = 10

        reasons.append(
            "activistes / dissidents: "
            + ", ".join(
                (activists or body_activists)[:6]
            )
        )

    elif has_journalist:

        target_score = 7

        reasons.append(
            "journaliste / média"
        )

    elif (
        "civil society" in headline
        or "ngo" in headline
        or "ngos" in headline
    ):

        target_score = 5

        reasons.append(
            "société civile / ONG"
        )

    # ========================================================
    # SOUS-SCORE 3 — RÉPRESSION /30
    # ========================================================

    repression_score = 0

    repression_terms_all = list(
        dict.fromkeys(
            repression
            + legal_repression
            + body_repression
            + body_legal_repression
        )
    )

    if repression_terms_all:

        repression_score = weighted_score(
            repression_terms_all,
            REPRESSION_WEIGHTS,
            25,
        )

        reasons.append(
            "répression: "
            + ", ".join(
                repression_terms_all[:8]
            )
        )

    # Répression juridique sans terme fort
    if (
        legal_repression
        and repression_score < 10
    ):

        repression_score = max(
            repression_score,
            8,
        )

    # Contexte juridique (cour, procureur, police...) : bonus
    # modéré, uniquement si un signal de répression existe déjà.
    # Seul, ce contexte ne doit rien apporter au score.
    if (
        has_legal_context
        and repression_terms_all
    ):

        repression_score = capped_add(
            repression_score,
            min(3, len(legal_context or body_legal_context)),
            30,
        )

        reasons.append(
            "contexte judiciaire: "
            + ", ".join(
                (legal_context or body_legal_context)[:6]
            )
        )

    # Confirmation dans le body
    if confirmed_repression:

        repression_score = capped_add(
            repression_score,
            5,
            30,
        )

        reasons.append(
            "répression confirmée dans le corps"
        )

    # Relation explicite victime -> répression
    if (
        confirmed_activist_pressure
        or confirmed_journalist_pressure
    ):

        repression_score = capped_add(
            repression_score,
            5,
            30,
        )

    # ========================================================
    # SOUS-SCORE 4 — DROITS SPÉCIFIQUES /10
    # ========================================================

    rights_score = 0

    rights_terms_all = list(
        dict.fromkeys(
            specific_rights
            + body_specific_rights
        )
    )

    if rights_terms_all:

        rights_score = weighted_score(
            rights_terms_all,
            SPECIFIC_RIGHTS_WEIGHTS,
            8,
        )

        reasons.append(
            "droits spécifiques: "
            + ", ".join(
                rights_terms_all[:8]
            )
        )

    elif has_human_rights:

        rights_score = 4

        reasons.append(
            "droits humains"
        )

    if confirmed_rights:

        rights_score = capped_add(
            rights_score,
            2,
            10,
        )

        reasons.append(
            "droits humains confirmés dans le corps"
        )

    # ========================================================
    # SOUS-SCORE 5 — IMPORTANCE JOURNALISTIQUE /10
    # ========================================================

    journalism_score = 0

    # Article original avec événement concret
    if (
        confirmed_activist_pressure
        or confirmed_journalist_pressure
    ):

        journalism_score = 7

    elif (
        activist_relation
        or journalist_relation
    ) and central_asia:

        journalism_score = 6

    elif confirmed_repression:

        journalism_score = 6

    elif major_geo:

        journalism_score = 5

    elif domestic and (
        has_human_rights
        or has_repression
        or has_specific_rights
    ):

        journalism_score = 4

    elif has_human_rights:

        journalism_score = 3

    elif domestic:

        journalism_score = 2

    # ========================================================
    # SOUS-SCORE 6 — GÉOPOLITIQUE /10
    # ========================================================

    geopolitical_score = 0

    if major_geo:

        geopolitical_score = 7

        reasons.append(
            "géopolitique majeure: "
            + ", ".join(
                major_geo[:6]
            )
        )

    elif routine_geo:

        geopolitical_score = 2

    # SCO seul : signal contextuel faible
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

    if (
        has_sco
        and major_geo
    ):

        geopolitical_score = capped_add(
            geopolitical_score,
            3,
            10,
        )

        reasons.append(
            "Organisation de coopération de Shanghai"
        )

    # ========================================================
    # SOUS-SCORE 7 — FRAÎCHEUR /5
    # ========================================================

    freshness_score = 0

    # Si ton scraper fournit déjà un âge en jours,
    # on l'utilise.
    age_days = article.get(
        "age_days"
    )

    if age_days is not None:

        try:
            age_days = float(
                age_days
            )

            if age_days <= 1:
                freshness_score = 5

            elif age_days <= 3:
                freshness_score = 4

            elif age_days <= 7:
                freshness_score = 3

            elif age_days <= 14:
                freshness_score = 2

            elif age_days <= 30:
                freshness_score = 1

        except (
            TypeError,
            ValueError,
        ):
            freshness_score = 0

    # ========================================================
    # SCORE BRUT
    # ========================================================

    score = (
        geography_score
        + target_score
        + repression_score
        + rights_score
        + journalism_score
        + geopolitical_score
        + freshness_score
    )

    # ========================================================
    # PÉNALITÉS
    # ========================================================

    penalties = 0

    # --------------------------------------------------------
    # Économie / géopolitique ordinaire
    # --------------------------------------------------------

    if (
        routine_geo
        and not (
            has_activist
            or has_journalist
            or has_specific_rights
            or has_repression
            or has_human_rights
        )
    ):

        penalties += 10

        reasons.append(
            "géopolitique / économie ordinaire"
        )

    # --------------------------------------------------------
    # Histoire / culture
    # --------------------------------------------------------

    if (
        historical
        and not (
            has_activist
            or has_journalist
            or has_repression
            or has_specific_rights
            or has_human_rights
        )
    ):

        penalties += 12

        reasons.append(
            "histoire / culture"
        )

    # --------------------------------------------------------
    # Acteur extérieur seul
    # --------------------------------------------------------

    if (
        actors
        and not (
            central_asia
            and (
                has_activist
                or has_journalist
                or has_repression
                or has_specific_rights
                or domestic
                or major_geo
            )
        )
    ):

        penalties += 5

        reasons.append(
            "acteur extérieur sans enjeu régional clair"
        )

    # --------------------------------------------------------
    # Caucase seul
    # --------------------------------------------------------

    if caucasus_only:

        penalties += 10

        reasons.append(
            "Caucase uniquement"
        )

    # --------------------------------------------------------
    # Non-news
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Bruit
    # --------------------------------------------------------

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
    # BONUS SIGNAL SPÉCIFIQUE ASIE CENTRALE
    # ========================================================

    if central_asia_hr:

        # Bonus limité.
        # Le signal ne peut pas à lui seul transformer
        # un article banal en article prioritaire.
        bonus = min(
            4,
            len(central_asia_hr) * 2,
        )

        score += bonus

        reasons.append(
            "signal spécifique Asie centrale: "
            + ", ".join(
                central_asia_hr[:8]
            )
        )

    # ========================================================
    # BONUS RELATION FORTE
    # ========================================================

    if confirmed_activist_pressure:

        score += 8

        reasons.append(
            "relation confirmée: activiste + répression"
        )

    elif confirmed_journalist_pressure:

        score += 7

        reasons.append(
            "relation confirmée: journaliste + répression"
        )

    elif activist_relation and central_asia:

        score += 4

        reasons.append(
            "relation détectée: activiste + répression"
        )

    elif journalist_relation and central_asia:

        score += 4

        reasons.append(
            "relation détectée: journaliste + répression"
        )

    # ========================================================
    # V7 — ANCRAGE HR PRINCIPAL
    # ========================================================
    # Les mentions HR lointaines dans le corps ne doivent pas
    # transformer un article économique/culturel en priorité A.
    # Un signal fort doit apparaître dans le titre/résumé court.
    primary_hr_text = (title + " " + summary[:1200]).strip()

    primary_repression = any(
        phrase_present(primary_hr_text, term)
        for term in REPRESSION_TERMS_V7
    ) or bool(re.search(
        r"(?:\bconvicts?\b|\bconvicted\b|\bsentenced\b|\bunder pressure\b|\bunder threat\b|\bpressure on journalists\b|\bbehind bars\b|\bза решеткой\b|\bпреследует\b|\bпреследование\b)",
        primary_hr_text,
        re.IGNORECASE,
    ))
    primary_hr_defender = any(
        phrase_present(primary_hr_text, term)
        for term in HUMAN_RIGHTS_DEFENDER_TERMS
    )
    primary_forced_labor = any(
        phrase_present(primary_hr_text, term)
        for term in FORCED_LABOR_TERMS
    )
    # V8: seuls les droits explicitement menacés/violés constituent
    # un ancrage HR fort. Les mentions génériques (women's rights,
    # democratic reforms, politics, etc.) ne suffisent pas.
    STRONG_PRIMARY_RIGHTS_V8 = [
        "human rights violation", "human rights violations",
        "rights violation", "lgbt rights", "lgbti rights",
        "gender-based violence", "violence against women",
        "forced marriage", "child marriage",
        "ethnic discrimination", "religious discrimination",
        "forced labor", "forced labour", "child labor", "child labour",
        "принудительный труд", "детский труд",
        "нарушение прав человека", "нарушения прав человека",
        "насилие в отношении женщин", "гендерная дискриминация",
        "свобода прессы", "свобода слова",
    ]
    primary_specific_right = any(
        phrase_present(primary_hr_text, term)
        for term in STRONG_PRIMARY_RIGHTS_V8
    )
    primary_lgbt_pressure = (
        any(phrase_present(primary_hr_text, term) for term in ["lgbt", "lgbti", "lgbt rights", "lgbti rights", "queer"])
        and (primary_repression or "under pressure" in primary_hr_text or "under threat" in primary_hr_text)
    )
    primary_journalist_pressure = (
        any(phrase_present(primary_hr_text, term) for term in JOURNALIST_TERMS_V7)
        and (primary_repression or any(phrase_present(primary_hr_text, term) for term in [
            "censorship", "censored", "press freedom", "media freedom",
            "restricted access", "access restriction", "pressure on journalists",
            "запретили доступ", "давление на журналистов",
            "цензура", "цензур"
        ]))
    )
    primary_academic_case = (
        any(phrase_present(primary_hr_text, term) for term in ACADEMIC_HR_TERMS_V7)
        and (has_detention or has_imprisonment or primary_repression)
    )

    primary_defender_case = (
        primary_hr_defender
        and (
            primary_repression
            or prison_sentence_signal
            or has_detention
            or has_imprisonment
            or severe_morphology
        )
    )

    primary_hr_anchor = bool(
        primary_repression
        or primary_defender_case
        or primary_forced_labor
        or primary_specific_right
        or primary_lgbt_pressure
        or primary_journalist_pressure
        or primary_academic_case
    )

    # ========================================================
    # BONUS GRAVE
    # ========================================================

    severe_detected = (
        severe_morphology
        or any(
            normalize(term)
            in {
                normalize(x)
                for x in SEVERE_REPRESSION_TERMS
            }
            for term in (repression + body_repression)
        )
    )

    if (
        severe_detected
        and (
            confirmed_repression
            or confirmed_activist_pressure
            or confirmed_journalist_pressure
        )
    ):

        score += 5

        reasons.append(
            "signal de répression grave confirmé"
        )

    # ========================================================
    # BONUS V4 — CAS HR CRITIQUE
    # ========================================================
    # Combinaison très spécifique : ancrage régional + activiste/
    # défenseur + condamnation/détention + mauvais traitement grave.
    # Ce bonus corrige les faux négatifs où les mots sont répartis
    # entre titre et corps et où aucun mot isolé n'est suffisamment fort.
    critical_hr_case = bool(
        regional_context
        and (has_activist or has_hr_defender)
        and (primary_repression or primary_defender_case or primary_forced_labor or primary_journalist_pressure or primary_academic_case)
        and (
            confirmed_repression
            or primary_repression
            or severe_detected
        )
        and (
            prison_sentence_signal
            or has_repression
        )
    )

    if critical_hr_case:
        score += 25
        reasons.append(
            "CAS HR CRITIQUE: activiste + condamnation/détention + signal grave"
        )

        if has_activist and primary_repression and primary_specific_right:
            score += 15
            reasons.append("cible militante + condamnation + droit spécifique")

    elif (
        regional_context
        and severe_detected
        and has_repression
    ):
        score += 15
        reasons.append(
            "bonus répression grave confirmée"
        )

    if prison_sentence_signal and regional_context and has_activist:
        score += 8
        reasons.append(
            "peine de prison liée à un activiste"
        )

    # ========================================================
    # PORTE DE CONTEXTE RÉGIONAL
    # ========================================================
    #
    # Un article ne peut pas obtenir un score élevé s'il n'a
    # aucun ancrage géographique en Asie centrale (ni même dans
    # le Caucase). Ceci évite qu'un article de géopolitique /
    # droits humains globale, sans lien régional réel, ne soit
    # classé comme prioritaire.

    if not regional_context:

        score = min(
            score,
            20,
        )

        reasons.append(
            "porte de contexte régional: aucun ancrage Asie centrale / Caucase"
        )

    # ========================================================
    # V7 — SIGNAUX HR À FORTE VALEUR COMBINATOIRE
    # ========================================================
    # Bonus mutuellement contrôlés : on évite l'empilement
    # défenseur + journaliste + détention + répression + rights
    # qui produisait des faux 90-100 sur des articles généraux.

    v7_combo_bonus = 0

    if regional_context and primary_forced_labor:
        v7_combo_bonus += 37
        reasons.append("travail forcé au cœur du sujet")
        if has_government_involvement:
            v7_combo_bonus += 8
            reasons.append("travail forcé impliquant les autorités ou l'État")

    elif regional_context and primary_defender_case and (confirmed_repression or severe_detected):
        v7_combo_bonus += 16
        reasons.append("défenseur des droits confronté à une répression")
        if prison_sentence_signal or has_detention or has_imprisonment:
            v7_combo_bonus += 8
            reasons.append("défenseur des droits arrêté, détenu ou condamné")

    elif regional_context and primary_defender_case and has_journalist:
        v7_combo_bonus += 25
        reasons.append("défenseur des droits et journaliste au cœur du sujet")

    elif regional_context and primary_hr_defender and has_journalist:
        v7_combo_bonus += 12
        reasons.append("défenseur des droits et journaliste")

    elif regional_context and primary_journalist_pressure:
        v7_combo_bonus += 35
        reasons.append("journaliste confronté à restriction, censure ou répression")

    elif regional_context and primary_academic_case:
        v7_combo_bonus += 26
        reasons.append("liberté académique menacée avec arrestation/détention")

    elif regional_context and primary_lgbt_pressure:
        v7_combo_bonus += 45
        reasons.append("personnes LGBT/queer confrontées à une pression ou répression")

    elif regional_context and primary_specific_right:
        v7_combo_bonus += 8
        reasons.append("atteinte à un droit spécifique au cœur du sujet")

    score += min(v7_combo_bonus, 45)

    # V8 — cas militant explicitement condamné/visé : la combinaison
    # titre/résumé suffit à confirmer une affaire HR forte, même si le
    # scraper ne retrouve pas de terme juridique dans le body.
    if regional_context and has_activist and primary_repression and primary_specific_right:
        score += 20
        reasons.append("militant + répression + droit spécifique dans le sujet principal")

    # V8 — pression ciblant directement les personnes LGBT/queer.
    if regional_context and primary_lgbt_pressure:
        score += 15
        reasons.append("pression ciblant les personnes LGBT/queer")

    # --------------------------------------------------------
    # V7 — PLAFOND ANTI-FAUX-POSITIFS
    # --------------------------------------------------------
    # Si aucun signal HR fort n'est présent dans le titre/résumé,
    # le corps seul ne peut pas faire passer un article général
    # en haute priorité.
    if regional_context and not primary_hr_anchor:
        if primary_hr_defender:
            score = min(score, 50)
            reasons.append("plafond V8: défenseur cité sans acte répressif principal")
        elif any(phrase_present(primary_hr_text, term) for term in GENERIC_REFORM_TERMS_V7):
            score = min(score, 35)
            reasons.append("plafond V8: réforme/politique générale sans atteinte HR explicite")
        elif any(phrase_present(primary_hr_text, term) for term in NON_HR_TOPIC_TERMS_V7):
            score = min(score, 28)
            reasons.append("plafond V8: sujet culturel/économique/général sans signal HR principal")
        else:
            score = min(score, 35)
            reasons.append("plafond V8: aucun événement HR principal dans titre/résumé")

    # ========================================================
    # V8 — PLAFONDS ÉDITORIAUX FINAUX
    # ========================================================
    # Les scores élevés exigent désormais un événement HR identifiable
    # dans le titre/résumé, et non simplement des mots HR dans le body.
    if regional_context:
        if primary_forced_labor:
            # Travail forcé : priorité élevée, sans empiler artificiellement
            # tous les signaux du body.
            score = min(score, 82 if has_government_involvement else 76)
        elif primary_academic_case:
            score = min(score, 82)
        elif primary_journalist_pressure:
            score = min(score, 85)
        elif primary_defender_case or critical_hr_case:
            score = min(score, 100)
        elif primary_lgbt_pressure:
            score = min(score, 85)
        elif primary_repression:
            score = min(score, 78)
        elif primary_specific_right:
            score = min(score, 65)

    # Les droits des femmes/politique/réformes sans violence, contrainte,
    # condamnation ou répression explicite restent des sujets secondaires.
    if regional_context and not (
        primary_defender_case
        or primary_forced_labor
        or primary_journalist_pressure
        or primary_academic_case
        or primary_lgbt_pressure
        or primary_repression
    ):
        if any(phrase_present(primary_hr_text, term) for term in [
            "women's rights", "prawa kobiet", "права женщин",
            "democratic reform", "democratic reforms",
            "political reform", "political reforms",
            "more women in", "social stability"
        ]):
            score = min(score, 48)
            reasons.append("plafond V8: sujet droits/politique sans événement répressif")

    # ========================================================
    # BORNE
    # ========================================================

    score = max(
        0,
        min(
            round(score),
            100,
        ),
    )

    # ========================================================
    # NIVEAU ÉDITORIAL
    # ========================================================

    if (
        not regional_context
        or caucasus_only
        or non_news
        or noise
    ):

        level = "D"

    elif (
        score >= 75
        and (
            confirmed_activist_pressure
            or confirmed_journalist_pressure
            or severe_detected
            or confirmed_repression
            or (has_activist and primary_repression and primary_specific_right)
            or primary_lgbt_pressure
        )
    ):

        level = "A"

    elif score >= 55:

        level = "B"

    elif score >= 35:

        level = "C"

    else:

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

    if confirmed_activist_pressure:

        theme = (
            "Activistes / dissidents sous pression"
        )

    elif confirmed_journalist_pressure:

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
        regional_context
        and score >= 40
        and not non_news
        and not noise
        and (
            has_activist
            or has_journalist
            or has_repression
            or has_specific_rights
            or has_human_rights
            or major_geo
        )
    )

    # Cas très fort
    if (
        confirmed_activist_pressure
        and not non_news
        and not noise
    ):

        relevant = True

    if (
        confirmed_journalist_pressure
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
        "body_geo_count": body_geo_count,
        "strong_body_geography": (
            strong_body_geography
        ),
        "caucasus_only": caucasus_only,

        # Activistes
        "activists": activists,
        "body_activists": body_activists,

        # Journalistes
        "journalists": journalists,
        "body_journalists": body_journalists,

        # Droits
        "human_rights": human_rights,
        "body_human_rights": body_human_rights,
        "specific_rights": specific_rights,
        "body_specific_rights": body_specific_rights,

        # Répression
        "repression": repression,
        "legal_repression": legal_repression,
        "body_repression": body_repression,
        "body_legal_repression": (
            body_legal_repression
        ),
        "legal_context": legal_context,
        "body_legal_context": body_legal_context,
        "has_legal_context": has_legal_context,

        # Politique
        "domestic": domestic,

        # Géopolitique
        "major_geo": major_geo,
        "routine_geo": routine_geo,
        "actors": actors,
        "has_sco": has_sco,

        # Contexte
        "central_asia_hr": central_asia_hr,
        "historical": historical,
        "non_news": non_news,
        "noise": noise,
        "low_signal_context": low_signal_context,
        "regional_context": regional_context,

        # Relations
        "has_activist": has_activist,
        "has_journalist": has_journalist,
        "has_repression": has_repression,
        "has_specific_rights": has_specific_rights,
        "has_human_rights": has_human_rights,

        "activist_relation": activist_relation,
        "journalist_relation": journalist_relation,

        "confirmed_repression": (
            confirmed_repression
        ),

        "confirmed_rights": (
            confirmed_rights
        ),

        "confirmed_activist_pressure": (
            confirmed_activist_pressure
        ),

        "confirmed_journalist_pressure": (
            confirmed_journalist_pressure
        ),

        "severe_detected": severe_detected,

        # Scores
        "geography_score": geography_score,
        "target_score": target_score,
        "repression_score": repression_score,
        "rights_score": rights_score,
        "journalism_score": journalism_score,
        "geopolitical_score": geopolitical_score,
        "freshness_score": freshness_score,

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
