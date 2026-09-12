"""
categorisation.py — description FACTUELLE d'un article, sans jugement
de pertinence.

Contexte : classify_article() (scoring.py) mélange aujourd'hui trois
décisions dans un score unique — la région concernée, la nature de la
répression décrite, et si ça nous intéresse éditorialement. Les deux
premières sont des constats vérifiables dans le texte ; la troisième
est un choix qui peut changer. Ce module ne fait que le premier
travail : décrire un article (région, type d'acteur visé, type de
traitement subi...) sans jamais décider s'il est pertinent. Le choix
éditorial vit à côté, dans regles_editoriales.py, appliqué sur le dict
que categoriser() renvoie ici.

Ne modifie ni scoring.py ni keywords.py (consigne explicite) : réutilise
leurs listes de mots-clés et leurs fonctions de détection (find_terms,
relation_present, _find_terms_with_russian_stems, normalize,
detect_language...) telles quelles — aucune regex de détection n'est
réécrite ici. looks_like_article_link() (article_ingestion.py) est
réutilisée de la même façon pour le champ "type" : même logique de
"ne pas dupliquer une détection déjà existante ailleurs dans le
projet", pas seulement pour scoring.py/keywords.py. article_age_days()
(html_template.py) est réutilisée pour "age_jours" pour la même raison.

Aucun champ score/niveau/pertinent/retenu en sortie.
"""

from __future__ import annotations

from typing import Any

from article_ingestion import looks_like_article_link
from html_template import article_age_days

from keywords import (
    CENTRAL_ASIA_TERMS,
    CAUCASUS_TERMS,
    UYGHUR_TERMS,
    HUMAN_RIGHTS_DEFENDER_TERMS,
    JOURNALIST_TERMS,
    ACTIVIST_TERMS,
    FORCED_LABOR_TERMS,
    LEGAL_CONTEXT_TERMS,
    LEGAL_REPRESSION_TERMS,
    SPECIFIC_RIGHTS_TERMS,
    SEVERE_REPRESSION_TERMS,
    REPRESSION_TERMS,
    PRESS_REPRESSION_TERMS_V9,
    TRANSNATIONAL_REPRESSION_TERMS_V9,
    REGIONAL_SOURCE_HINTS_V9,
)

from scoring import (
    normalize,
    find_terms,
    relation_present,
    detect_language,
    _find_terms_with_russian_stems,
    _RUSSIAN_CENTRAL_ASIA_STEM_PATTERNS,
    _RUSSIAN_CAUCASUS_STEM_PATTERNS,
)


# ============================================================
# GÉOGRAPHIE — table de correspondance terme -> pays normalisé
# ============================================================
#
# CENTRAL_ASIA_TERMS/CAUCASUS_TERMS (keywords.py) sont des listes
# plates mélangeant noms de pays, adjectifs et grandes villes en
# 4 langues, sans rattachement à un pays précis. La détection
# (quels termes sont présents) reste entièrement déléguée à
# find_terms/_find_terms_with_russian_stems ; cette table ne fait que
# NORMALISER un terme déjà détecté vers un code pays — elle ne
# réimplémente aucune recherche dans le texte.
#
# Un terme détecté mais absent de cette table (ex. "central asia",
# "caucasus", générique, sans pays précis) tombe sur "autre" par
# défaut plutôt que d'être deviné.

_GEO_TERM_COUNTRY: dict[str, str] = {}


def _register_geo_terms(country: str, terms: list[str]) -> None:
    for term in terms:
        _GEO_TERM_COUNTRY[term] = country


_register_geo_terms("kazakhstan", [
    "kazakhstan", "kazakh", "almaty", "astana", "nur-sultan", "shymkent",
    "karaganda", "aktobe", "atyrau",
    "казахстан", "казах", "алматы", "астана", "нур-султан", "шымкент",
    "караганда", "актобе", "атырау",
    "قزاقستان", "قزاق", "آلماتی",
])

_register_geo_terms("ouzbekistan", [
    "uzbekistan", "uzbek", "tashkent", "samarkand", "bukhara", "khiva",
    "namangan", "andijan", "fergana", "nukus",
    "узбекистан", "узбек", "ташкент", "самарканд", "бухара", "хива",
    "наманган", "андижан", "фергана", "нукус",
    "ازبکستان", "ازبک", "تاشکند", "سمرقند", "بخارا",
    "ouzbékistan", "ouzbek", "samarcande", "boukhara", "tachkent",
])

_register_geo_terms("kirghizistan", [
    "kyrgyzstan", "kyrgyz republic", "kyrgyz", "bishkek", "osh",
    "jalal-abad", "karakol",
    "кыргызстан", "киргизия", "киргиз", "бишкек", "ош", "джалал-абад",
    "каракол",
    "قرقیزستان", "قیرقیزستان", "قرقیز", "بیشکک",
    "kirghizistan", "kirghizstan", "kirghize", "bichkek",
])

_register_geo_terms("tadjikistan", [
    "tajikistan", "tajik", "dushanbe", "khujand", "khorog",
    "таджикистан", "таджик", "душанбе", "худжанд", "хорог",
    "تاجیکستان", "تاجیک",
    "tadjikistan", "tadjik", "douchanbé",
])

_register_geo_terms("turkmenistan", [
    "turkmenistan", "turkmen", "ashgabat", "turkmenabat", "dashoguz",
    "туркменистан", "туркмен", "ашхабад", "туркменабат", "дашогуз",
    "ترکمنستان", "ترکمن", "عشق‌آباد", "عشق آباد",
    "turkménistan", "turkmène", "achgabat",
])

_register_geo_terms("azerbaidjan", [
    "azerbaijan", "baku",
    "азербайджан", "баку",
    "آذربایجان", "باکو",
    "azerbaïdjan", "azerbaïdjanais", "bakou",
])

_register_geo_terms("armenie", [
    "armenia", "yerevan",
    "армения", "ереван",
    "ارمنستان", "ایروان",
    "arménie", "arménien", "erevan",
])

_register_geo_terms("georgie", [
    "georgia", "tbilisi",
    "грузия", "тбилиси",
    "گرجستان", "تفلیس",
    "géorgie", "géorgien", "tbilissi",
])

_register_geo_terms("caucase_nord", [
    "north caucasus", "chechnya", "dagestan", "north ossetia",
    "ingushetia", "grozny", "makhachkala",
    "северный кавказ", "чечня", "дагестан", "ингушетия", "грозный",
    "махачкала",
    "قفقاز شمالی", "چچن", "داغستان",
    "tchétchénie", "daguestan", "ossétie du nord", "ingouchie",
    "makhatchkala",
])

# Xinjiang/Ouïghours : traité comme un pays/une région à part entière
# dans le schéma géo demandé (pas seulement un "acteur minorité
# ethnique") — tous les termes d'UYGHUR_TERMS (keywords.py) y
# renvoient.
_register_geo_terms("xinjiang", list(UYGHUR_TERMS))

# Iran/Afghanistan/Russie : absents de CENTRAL_ASIA_TERMS/
# CAUCASUS_TERMS (ce ne sont pas des pays de la porte régionale
# principale de scoring.py) mais demandés explicitement dans le schéma
# geo. Formes reprises telles quelles de MAJOR_GEOPOLITICAL_TERMS
# (keywords.py) ; "russie" (français) est la seule forme ajoutée, sur
# le même principe que les formes françaises déjà ajoutées ailleurs
# dans keywords.py (voir les commentaires de CENTRAL_ASIA_TERMS).
_IRAN_AFGHANISTAN_RUSSIA_TERMS = [
    "iran", "иран",
    "afghanistan", "афганистан",
    "russia", "россия", "russie",
]
_register_geo_terms("iran", ["iran", "иран"])
_register_geo_terms("afghanistan", ["afghanistan", "афганистан"])
_register_geo_terms("russie", ["russia", "россия", "russie"])


def _geo_terms_in(text: str, is_russian_source: bool) -> list[str]:
    """Termes géo bruts détectés dans `text` (pas encore mappés à un pays)."""
    central_asia = _find_terms_with_russian_stems(
        text, CENTRAL_ASIA_TERMS,
        _RUSSIAN_CENTRAL_ASIA_STEM_PATTERNS if is_russian_source else (),
    )
    caucasus = _find_terms_with_russian_stems(
        text, CAUCASUS_TERMS,
        _RUSSIAN_CAUCASUS_STEM_PATTERNS if is_russian_source else (),
    )
    uyghur = find_terms(text, UYGHUR_TERMS)
    iran_afg_russia = find_terms(text, _IRAN_AFGHANISTAN_RUSSIA_TERMS)
    return list(dict.fromkeys(central_asia + caucasus + uyghur + iran_afg_russia))


# ============================================================
# ACTEURS — terme -> "qui" est visé
# ============================================================
#
# HUMAN_RIGHTS_DEFENDER_TERMS/JOURNALIST_TERMS/ACTIVIST_TERMS
# (keywords.py) sont réutilisées telles quelles. Le reste
# (avocat/croyant/minorite_ethnique/femme/migrant/citoyen_ordinaire)
# n'a pas de liste dédiée dans keywords.py : listes minimales
# ci-dessous, sourcées quand possible depuis du vocabulaire déjà
# présent ailleurs dans le projet (cité en commentaire), incomplètes,
# à enrichir — même statut que ecologiste/syndicaliste (voir plus bas).
#
# ATTENTION : ACTIVIST_TERMS (keywords.py) mélange lui-même vocabulaire
# "activiste de la société civile" et "opposant/dissident" sous un même
# nom (pas de scission propre disponible côté keywords.py) — utilisée
# ici pour "opposant". Un article peut donc légitimement ressortir à la
# fois "defenseur" et "opposant" si le terme détecté est ambigu (ex.
# "activist"/"активист" apparaissent dans les deux listes sources) :
# c'est le vocabulaire lui-même qui est ambigu, pas un bug de ce
# module — voir "preuves" pour l'auditer.

# Repris de scoring.TARGET_TERMS_V9 (termes "lawyer"/"avocat"/
# "адвокат"), isolés ici pour le sous-acteur "avocat" — incomplet
# (ex. "barrister", "defense attorney", formes farsi manquantes).
AVOCAT_TERMS = [
    "lawyer", "lawyers", "avocat", "avocate", "avocats",
    "адвокат", "адвокаты",
]

# Incomplet — aucun vocabulaire "croyant"/"pratiquant" dans keywords.py
# (seulement des termes de sujet "religious persecution"/"religious
# freedom" dans SPECIFIC_RIGHTS_TERMS, pas des termes désignant une
# personne). À enrichir (formes farsi notamment).
CROYANT_TERMS = [
    "believer", "believers", "worshipper", "worshippers",
    "religious minority", "religious minorities",
    "member of a religious community", "prisoner of faith",
    "верующий", "верующие", "член религиозной общины",
]

# Incomplet — UYGHUR_TERMS couvre déjà la minorité ouïghoure via geo
# (voir plus bas, ajout automatique), le reste est minimal.
MINORITE_ETHNIQUE_TERMS = [
    "ethnic minority", "ethnic minorities", "national minority",
    "indigenous people", "indigenous community",
    "этническое меньшинство", "национальное меньшинство",
    "коренной народ",
]

# Consolidé depuis les termes déjà présents dans VICTIM_TERMS/
# SPECIFIC_RIGHTS_TERMS/GENDER_VIOLENCE_TERMS_V9 (keywords.py) —
# pas de nouveau vocabulaire, juste un sous-ensemble ciblé "femme"
# extrait de listes qui mélangent plusieurs types de victimes/sujets.
FEMME_TERMS = [
    "women", "girls", "women's rights", "girls' rights", "girls rights",
    "женщины", "девушки", "права женщин", "права девушек",
]

# Partiellement nouveau — "asylum seeker"/"political asylum" viennent
# de TRANSNATIONAL_REPRESSION_TERMS_V9 (keywords.py) ; "migrant"/
# "refugee" sont absents de keywords.py et ajoutés ici. Incomplet
# (formes farsi manquantes).
MIGRANT_TERMS = [
    "migrant", "migrants", "migrant worker", "migrant workers",
    "refugee", "refugees", "asylum seeker", "asylum seekers",
    "мигрант", "мигранты", "трудовой мигрант", "беженец", "беженцы",
    "проситель убежища",
]

# Incomplet — pas de liste dédiée dans keywords.py ; "civilian(s)"
# repris de VICTIM_TERMS, le reste ajouté minimalement.
CITOYEN_TERMS = [
    "civilian", "civilians", "resident", "residents",
    "ordinary citizen", "ordinary citizens",
    "гражданин", "граждане", "мирные жители", "местный житель",
]

# Absent de keywords.py — vocabulaire minimal créé pour ce module,
# signalé incomplet comme demandé.
ECOLOGISTE_TERMS = [
    "environmental activist", "environmental activists",
    "environmentalist", "environmentalists",
    "climate activist", "climate activists",
    "эколог", "экологи", "экологический активист",
    "активист-эколог",
]

# Absent de keywords.py — vocabulaire minimal créé pour ce module,
# signalé incomplet comme demandé.
SYNDICALISTE_TERMS = [
    "trade unionist", "trade unionists", "union leader", "union leaders",
    "labor union activist", "labour union activist",
    "профсоюзный активист", "профсоюзный лидер", "профсоюз",
]

ACTEUR_TYPE_TERMS: dict[str, list[str]] = {
    "defenseur": HUMAN_RIGHTS_DEFENDER_TERMS,
    "journaliste": JOURNALIST_TERMS,
    "opposant": ACTIVIST_TERMS,
    "avocat": AVOCAT_TERMS,
    "croyant": CROYANT_TERMS,
    "minorite_ethnique": MINORITE_ETHNIQUE_TERMS,
    "femme": FEMME_TERMS,
    "migrant": MIGRANT_TERMS,
    "ecologiste": ECOLOGISTE_TERMS,
    "syndicaliste": SYNDICALISTE_TERMS,
    "citoyen_ordinaire": CITOYEN_TERMS,
}


# ============================================================
# TRAITEMENTS — terme -> "quoi"
# ============================================================
#
# FORCED_LABOR_TERMS/PRESS_REPRESSION_TERMS_V9/REPRESSION_TERMS
# (keywords.py) réutilisées telles quelles. Les autres sont des
# sous-ensembles ciblés, extraits verbatim de listes keywords.py plus
# larges qui mélangent plusieurs notions (ex. LEGAL_CONTEXT_TERMS
# contient à la fois "détention" et "condamnation") — pas de nouveau
# vocabulaire inventé, juste une scission.

# Sous-ensemble de LEGAL_CONTEXT_TERMS (keywords.py).
DETENTION_TERMS = [
    "detained", "detention", "arrest", "arrested",
    "задержан", "задержана", "задержание", "арест", "арестован",
    "арестована",
    "بازداشت", "دستگیری", "دستگیر",
]

# Sous-ensemble de LEGAL_CONTEXT_TERMS + LEGAL_REPRESSION_TERMS
# (keywords.py).
CONDAMNATION_TERMS = [
    "conviction", "convicted", "sentenced", "sentence", "imprisoned",
    "prisoner of conscience", "prisoners of conscience",
    "political prisoner", "political prisoners",
    "осужден", "осуждена", "осуждены", "приговор", "заключен",
    "заключена", "политзаключенный", "политзаключенные",
    "محکومیت", "محکوم", "حکم زندان", "زندانی",
]

# Sous-ensemble de SPECIFIC_RIGHTS_TERMS (keywords.py).
TORTURE_TERMS = [
    "torture", "tortured", "ill-treatment", "mistreatment",
    "abuse in custody", "custodial abuse", "police abuse",
    "police brutality",
    "пытк", "истязани", "жестокое обращение",
    "насилие в местах лишения свободы", "полицейское насилие",
    "насилие полиции",
    "شکنجه", "بدرفتاری", "خشونت پلیس",
]

# Sous-ensemble de SPECIFIC_RIGHTS_TERMS (keywords.py).
DISPARITION_TERMS = [
    "forced disappearance", "enforced disappearance", "disappeared",
    "missing after detention",
    "насильственное исчезновение", "насильственно исчез", "исчезнувш",
    "ناپدید شدن اجباری",
]

# Sous-ensemble de SPECIFIC_RIGHTS_TERMS + SEVERE_REPRESSION_TERMS
# (keywords.py).
VIOLENCE_PHYSIQUE_TERMS = [
    "extrajudicial killing", "unlawful killing", "death in custody",
    "custody death", "violent crackdown", "deadly crackdown",
    "sexual violence", "sexual abuse", "gender-based violence",
    "domestic violence",
    "внесудебное убийство", "смерть в заключении", "жесткий разгон",
    "жестокий разгон", "сексуальное насилие", "гендерное насилие",
    "домашнее насилие",
    "اعدام", "اعدام خارج از روند قضایی", "مرگ در بازداشت",
    "خشونت خانگی", "خشونت جنسی",
]

TRAITEMENT_TYPE_TERMS: dict[str, list[str]] = {
    "detention": DETENTION_TERMS,
    "condamnation": CONDAMNATION_TERMS,
    "torture_mauvais_traitement": TORTURE_TERMS,
    "disparition": DISPARITION_TERMS,
    "violence_physique": VIOLENCE_PHYSIQUE_TERMS,
    "censure_blocage": PRESS_REPRESSION_TERMS_V9,
    "pression_administrative": REPRESSION_TERMS,
    "contrainte_travail": FORCED_LABOR_TERMS,
    "expulsion_extradition": TRANSNATIONAL_REPRESSION_TERMS_V9,
}


# ============================================================
# TYPE D'ARTICLE
# ============================================================

# Seuil (caractères) au-delà duquel un corps sans date associée est
# considéré comme un rapport/une analyse plutôt qu'une brève page
# institutionnelle. Choisi arbitrairement (pas de valeur fournie par
# l'utilisateur) — à ajuster si besoin.
REPORT_BODY_LENGTH_THRESHOLD = 3000

# Absent de keywords.py — vocabulaire minimal pour repérer un
# communiqué/plaidoyer, incomplet, à enrichir (formes farsi
# manquantes).
ADVOCACY_TERMS = [
    "press release", "joint statement", "open letter", "we call on",
    "we urge", "statement by", "joint letter",
    "communiqué de presse", "lettre ouverte", "nous appelons",
    "заявление", "совместное заявление", "открытое письмо",
    "призываем",
]


def _detect_type(article: dict[str, Any], body_text: str) -> tuple[str, str]:
    """Renvoie (type, raison) — la raison alimente preuves["type"]."""
    url = article.get("url") or article.get("link") or ""
    title = article.get("title") or ""

    if not looks_like_article_link(url, title):
        return "navigation", "looks_like_article_link()=False"

    if article.get("date"):
        return "evenement_date", "date d'article présente"

    if len(body_text) >= REPORT_BODY_LENGTH_THRESHOLD:
        return "rapport_analyse", f"corps >= {REPORT_BODY_LENGTH_THRESHOLD} caractères"

    advocacy_terms = find_terms(normalize(title) + " " + body_text, ADVOCACY_TERMS)
    if advocacy_terms:
        return "plaidoyer_communique", ", ".join(advocacy_terms[:4])

    return "page_institutionnelle", "sans date, corps court, aucun signal de plaidoyer"


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def categoriser(article: dict[str, Any]) -> dict[str, Any]:
    """
    Décrit factuellement un article : région concernée, type d'acteur
    visé, type de traitement subi, etc. Ne juge jamais de la
    pertinence éditoriale (voir regles_editoriales.py pour ça) — aucun
    champ score/niveau/pertinent/retenu en sortie.

    Ne modifie pas `article` (contrairement à classify_article(), qui
    réécrit article["language"] sur place) : categoriser() est une
    fonction de lecture pure.
    """
    title = article.get("title", "")
    summary = article.get("summary", "")
    body = normalize(article.get("body", ""))

    source_text = normalize(article.get("source", ""))
    link_text = normalize(article.get("link", article.get("url", "")))
    source_context = source_text + " " + link_text

    # Mêmes fenêtres de troncature que classify_article() (scoring.py)
    # pour un comportement/coût comparable.
    headline = (normalize(title) + " " + normalize(summary)[:3000]).strip()
    full_text = (headline + " " + body[:12000]).strip()

    preuves: dict[str, Any] = {}

    # --------------------------------------------------------
    # Langue résolue (pour les vérifications russes/farsi ciblées) —
    # calculée localement, jamais écrite sur `article` (voir
    # docstring : categoriser() ne mute pas son entrée).
    # --------------------------------------------------------
    declared_language = (article.get("language") or "").strip().lower()
    if declared_language in ("", "multi"):
        resolved_language = detect_language(full_text) or declared_language
    else:
        resolved_language = declared_language
    is_russian_source = resolved_language == "ru"

    # --------------------------------------------------------
    # GEO / GEO_ROLE
    # --------------------------------------------------------
    headline_geo_raw = _geo_terms_in(headline, is_russian_source)
    body_geo_raw = _geo_terms_in(body, is_russian_source)
    all_geo_raw = list(dict.fromkeys(headline_geo_raw + body_geo_raw))

    geo = list(dict.fromkeys(
        _GEO_TERM_COUNTRY.get(term, "autre") for term in all_geo_raw
    ))

    if headline_geo_raw:
        geo_role = "sujet_principal"
    elif body_geo_raw:
        geo_role = "mention_secondaire"
    else:
        geo_role = "absent"

    preuves["geo"] = all_geo_raw
    preuves["geo_role"] = {
        "titre_ou_chapo": headline_geo_raw,
        "corps": body_geo_raw,
    }

    # --------------------------------------------------------
    # ACTEUR
    # --------------------------------------------------------
    acteur: list[str] = []
    preuves_acteur: dict[str, list[str]] = {}
    for key, terms in ACTEUR_TYPE_TERMS.items():
        matched = find_terms(full_text, terms)
        if matched:
            acteur.append(key)
            preuves_acteur[key] = matched

    # Un article Ouïghour/Xinjiang concerne par construction une
    # minorité ethnique, même si aucun terme MINORITE_ETHNIQUE_TERMS
    # générique n'est présent — réutilise la détection géo déjà faite
    # ci-dessus plutôt que de la refaire.
    if "xinjiang" in geo and "minorite_ethnique" not in acteur:
        acteur.append("minorite_ethnique")
        preuves_acteur.setdefault("minorite_ethnique", []).append(
            "(déduit de geo=xinjiang)"
        )

    if not acteur:
        acteur = ["aucun"]
    preuves["acteur"] = preuves_acteur

    # --------------------------------------------------------
    # TRAITEMENT
    # --------------------------------------------------------
    traitement: list[str] = []
    preuves_traitement: dict[str, list[str]] = {}
    for key, terms in TRAITEMENT_TYPE_TERMS.items():
        matched = find_terms(full_text, terms)
        if matched:
            traitement.append(key)
            preuves_traitement[key] = matched

    if not traitement:
        traitement = ["aucun"]
    preuves["traitement"] = preuves_traitement

    # --------------------------------------------------------
    # RELATION ACTEUR / TRAITEMENT
    # --------------------------------------------------------
    acteur_terms_flat = [t for terms in ACTEUR_TYPE_TERMS.values() for t in terms]
    traitement_terms_flat = [t for terms in TRAITEMENT_TYPE_TERMS.values() for t in terms]
    relation_acteur_traitement = bool(
        acteur != ["aucun"]
        and traitement != ["aucun"]
        and relation_present(full_text, acteur_terms_flat, traitement_terms_flat)
    )
    preuves["relation_acteur_traitement"] = (
        {
            "acteur_termes": [t for t in acteur_terms_flat if t in full_text],
            "traitement_termes": [t for t in traitement_terms_flat if t in full_text],
        }
        if relation_acteur_traitement
        else {}
    )

    # --------------------------------------------------------
    # TYPE D'ARTICLE
    # --------------------------------------------------------
    type_article, type_reason = _detect_type(article, body)
    preuves["type"] = type_reason

    # --------------------------------------------------------
    # AGE_JOURS
    # --------------------------------------------------------
    date = article.get("date")
    age_days_float = article_age_days(date) if date else None
    age_jours = round(age_days_float) if age_days_float is not None else None
    preuves["age_jours"] = date if date else None

    # --------------------------------------------------------
    # SOURCE_SPECIALISEE
    # --------------------------------------------------------
    source_hint_terms = find_terms(source_context, REGIONAL_SOURCE_HINTS_V9)
    source_specialisee = bool(source_hint_terms)
    preuves["source_specialisee"] = source_hint_terms

    return {
        "geo": geo,
        "geo_role": geo_role,
        "acteur": acteur,
        "traitement": traitement,
        "relation_acteur_traitement": relation_acteur_traitement,
        "type": type_article,
        "age_jours": age_jours,
        "source_specialisee": source_specialisee,
        "preuves": preuves,
    }
