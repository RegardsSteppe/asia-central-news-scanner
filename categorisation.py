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

Aucune détection n'est réécrite ici : tout passe par matching.py, la
couche partagée avec scoring.py (normalisation, recherche de termes,
morphologie russe, motifs farsi, détection de langue). Le vocabulaire
vient de keywords.py. Ce module ne fait que du câblage : il applique
ces primitives aux listes qui l'intéressent et range le résultat dans
un schéma descriptif.

C'est délibéré : les deux couches consommatrices partagent la même
intelligence de détection, donc une racine russe ajoutée ou une langue
mieux gérée profite aux deux. Tant que categorisation.py réimplémentait
sa propre détection, elle était systématiquement en retard sur
scoring.py (cas réel du 2026-09-12 : un article HRW russe titré
"пытки и произвольные аресты" ressortait traitement=aucun).

looks_like_article_link() (article_ingestion.py) et article_age_days()
(text_utils.py) sont réutilisées de la même façon pour "type" et
"age_jours".

Aucun champ score/niveau/pertinent/retenu en sortie.
"""

from __future__ import annotations

import re
from typing import Any

from article_ingestion import looks_like_article_link
from text_utils import article_age_days

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
    ACTIVIST_REPRESSION_FA_PATTERNS,
    JOURNALIST_REPRESSION_FA_PATTERNS,
)

from matching import (
    compiled,
    contains_pattern,
    find_caucasus_terms,
    find_central_asia_terms,
    find_terms,
    has_russian_repression_morphology,
    normalize,
    relation_present,
    resolve_language,
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
    # "кыргыз" (adjectif russe moderne, ex. "кыргызские власти") ajouté
    # le 2026-09-12 aux côtés de "кыргызстан"/"киргиз" (voir
    # _RUSSIAN_CENTRAL_ASIA_STEM_PATTERNS dans scoring.py pour le même
    # correctif côté détection).
    "кыргызстан", "киргизия", "киргиз", "кыргыз", "бишкек", "ош",
    "джалал-абад", "каракол",
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


def _geo_terms_in(text: str, language: str) -> list[str]:
    """Termes géo bruts détectés dans `text` (pas encore mappés à un pays)."""
    central_asia = find_central_asia_terms(text, CENTRAL_ASIA_TERMS, language)
    caucasus = find_caucasus_terms(text, CAUCASUS_TERMS, language)
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

# Aucun vocabulaire "croyant"/"pratiquant" dans keywords.py (seulement
# des termes de sujet "religious persecution"/"religious freedom" dans
# SPECIFIC_RIGHTS_TERMS, pas des termes désignant une personne).
#
# Enrichie le 2026-09-14 : la version d'origine ne reposait que sur des
# mots abstraits ("believer", "member of a religious community") et ne
# sortait que 4 articles sur 7795. Un article ne dit pas "un croyant a
# été arrêté", il dit "un imam" ou "des Témoins de Jéhovah" : ce sont
# les dénominations concrètes qui font le travail, en particulier
# celles effectivement réprimées dans la région (Témoins de Jéhovah,
# musulmans pratiquants, Hizb ut-Tahrir).
CROYANT_TERMS = [
    "believer", "believers", "worshipper", "worshippers",
    "religious minority", "religious minorities",
    "member of a religious community", "prisoner of faith",
    "imam", "imams", "mosque", "mosques",
    "jehovah's witness", "jehovah's witnesses", "jehovah witnesses",
    "pastor", "missionary", "missionaries",
    "religious leader", "religious leaders", "hizb ut-tahrir",
    "верующий", "верующие", "член религиозной общины",
    "имам", "имамы", "мечеть", "мечети",
    "свидетели иеговы", "свидетелей иеговы", "пастор",
    "религиозный деятель", "хизб ут-тахрир",
    "امام جمعه", "مسجد", "روحانی",
]

# Volontairement absents : "muslim"/"christian"/"мусульман"/"مسلمان".
# Un gentilé religieux décrit une population, pas quelqu'un à qui on
# fait subir quelque chose — vérifié sur le corpus, "muslim" seul
# déclenchait 11 fois, sur des articles de couverture de guerre ("How
# Central Asia navigates Russia's war on Ukraine", "Captured Tajik
# tells of life on Ukraine frontlines"). Les rôles religieux (imam,
# pasteur) et les congrégations visées (Témoins de Jéhovah, Hizb
# ut-Tahrir) désignent bien un acteur, eux.

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

# Absent de keywords.py — vocabulaire créé pour ce module. Enrichi le
# 2026-09-14 (5 articles sur 7795 avec les seules locutions d'origine).
ECOLOGISTE_TERMS = [
    "environmental activist", "environmental activists",
    "environmentalist", "environmentalists",
    "climate activist", "climate activists",
    "environmental defender", "environmental defenders",
    "land defender", "land defenders", "ecologist", "ecologists",
    "écologiste", "écologistes", "militant écologiste",
    "défenseur de l'environnement",
    "эколог", "экологи", "экологический активист",
    "активист-эколог", "экоактивист", "экоактивисты",
    "защитник окружающей среды",
    "فعال محیط زیست", "محیط زیست",
]

# Absent de keywords.py — vocabulaire créé pour ce module. Enrichi le
# 2026-09-14 (2 articles sur 7795 avec les seules locutions d'origine).
SYNDICALISTE_TERMS = [
    "trade unionist", "trade unionists", "union leader", "union leaders",
    "labor union activist", "labour union activist",
    "trade union", "trade unions", "labour union", "labor union",
    "union member", "union members", "striking workers",
    "syndicaliste", "syndicalistes", "syndicat", "syndicats",
    "профсоюзный активист", "профсоюзный лидер", "профсоюз",
    "профсоюзы", "профсоюза", "профсоюзник", "бастующие рабочие",
    "اتحادیه کارگری", "کارگران اعتصابی",
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

# Sous-ensemble de LEGAL_CONTEXT_TERMS (keywords.py). Les formes
# russes fléchies individuelles ("задержан", "арестован"...) ne
# couvrent pas leurs propres variantes (ex. "арест" ne matche pas
# "аресты", pluriel, via find_terms — limite de mot exigée juste
# après le terme) : couvertes par _TRAITEMENT_STEM_PATTERNS
# ci-dessous plutôt que d'énumérer chaque forme une à une.
DETENTION_TERMS = [
    "detained", "detention", "arrest", "arrested",
    "بازداشت", "دستگیری", "دستگیر",
]

# Sous-ensemble de LEGAL_CONTEXT_TERMS + LEGAL_REPRESSION_TERMS
# (keywords.py). Mêmes racines russes fléchies déplacées vers
# _TRAITEMENT_STEM_PATTERNS que pour DETENTION_TERMS ci-dessus.
CONDAMNATION_TERMS = [
    "conviction", "convicted", "sentenced", "sentence", "imprisoned",
    "prisoner of conscience", "prisoners of conscience",
    "political prisoner", "political prisoners",
    "политзаключенный", "политзаключенные",
    "محکومیت", "محکوم", "حکم زندان", "زندانی",
]

# Sous-ensemble de SPECIFIC_RIGHTS_TERMS (keywords.py). "пытк"/
# "истязани" retirés d'ici : ce sont des racines russes délibérément
# incomplètes (voir le commentaire "Russian stems / morphology handled
# by substring matching" sur REPRESSION_TERMS dans keywords.py) —
# find_terms() exige une limite de mot juste après le terme, donc ne
# matche jamais une forme fléchie réelle ("пытки", "пытками"...).
# Couvertes séparément par _TRAITEMENT_STEM_PATTERNS ci-dessous.
TORTURE_TERMS = [
    "torture", "tortured", "ill-treatment", "mistreatment",
    "abuse in custody", "custodial abuse", "police abuse",
    "police brutality",
    "жестокое обращение",
    "насилие в местах лишения свободы", "полицейское насилие",
    "насилие полиции",
    "شکنجه", "بدرفتاری", "خشونت پلیس",
]

# Sous-ensemble de SPECIFIC_RIGHTS_TERMS (keywords.py). "исчезнувш"
# retiré d'ici pour la même raison que "пытк" ci-dessus (racine
# incomplète) — couvert par _TRAITEMENT_STEM_PATTERNS.
DISPARITION_TERMS = [
    "forced disappearance", "enforced disappearance", "disappeared",
    "missing after detention",
    "насильственное исчезновение", "насильственно исчез",
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

# PRESS_REPRESSION_TERMS_V9 (keywords.py) ne suffit pas ici, et c'est
# structurel : cette liste est écrite pour le SCORING, où une locution
# entière ("journalist detained") est un signal précis qui mérite des
# points. Pour DÉCRIRE un article, la question est seulement "parle-t-il
# de censure ou de blocage ?", et la réponse tient en un mot. Audit du
# 2026-09-14 : 51 de ses 52 entrées sont des locutions de 2+ mots qui
# n'apparaissent jamais telles quelles dans un titre — d'où 2 articles
# étiquetés censure_blocage sur 7795.
#
# On complète donc sans rien retirer (les locutions restent justes
# quand elles matchent) : formes d'un seul mot, dans les 4 langues du
# corpus. Choisies pour ne pas être ambiguës hors contexte — "ban" ou
# "blocked" seuls sont écartés ("blocked the road", "banned from the
# stadium"), "censorship"/"цензура"/"سانسور" ne désignent qu'une chose.
CENSURE_BLOCAGE_TERMS = [
    *PRESS_REPRESSION_TERMS_V9,

    # English
    "censorship", "censor", "censored", "censoring", "censors",
    "gag order", "media ban", "website blocking",
    "internet restrictions", "blocked access",

    # French
    "censure", "censuré", "censurée", "censurés", "censurer",
    "blocage", "blocages", "coupure internet",

    # Farsi — "فیلترینگ" (filtrage) est le mot courant pour le blocage
    # de sites ; "سانسور" est la censure au sens strict.
    "سانسور", "فیلترینگ", "قطع اینترنت",
]

# Écartés après vérification sur le corpus, parce qu'un traitement doit
# décrire ce qu'on a FAIT SUBIR à quelqu'un :
#   - "press freedom"/"liberté de la presse" : un THÈME, pas un fait.
#     17 des 60 détections, et seuls déclencheurs sur "Sierra Leone",
#     "Protect journalists", "Services aux journalistes et aux médias"
#     ou un guide RSF sur les drones — du mobilier de site RSF/CPJ.
#   - "مسدود" (bloqué) : trop générique hors contexte. 4 détections sur
#     4 fausses, toutes routières ("چالوس مسدود شد" — 7 km de bouchon
#     sur la route de Chalus).

TRAITEMENT_TYPE_TERMS: dict[str, list[str]] = {
    "detention": DETENTION_TERMS,
    "condamnation": CONDAMNATION_TERMS,
    "torture_mauvais_traitement": TORTURE_TERMS,
    "disparition": DISPARITION_TERMS,
    "violence_physique": VIOLENCE_PHYSIQUE_TERMS,
    "censure_blocage": CENSURE_BLOCAGE_TERMS,
    "pression_administrative": REPRESSION_TERMS,
    "contrainte_travail": FORCED_LABOR_TERMS,
    "expulsion_extradition": TRANSNATIONAL_REPRESSION_TERMS_V9,
}

# Repéré en audit réel le 2026-09-12 sur un article HRW russe
# ("Киргизия: пытки и произвольные аресты нагнетают напряженность",
# ressorti traitement=aucun malgré "пытки" dans le titre) : plusieurs
# des listes ci-dessus contiennent des racines russes délibérément
# incomplètes (REPRESSION_TERMS — "репресс", "преследован",
# "преследова", "давлен", "запугив", "угроз", "подавлен", "подавля",
# "гонен", "притеснен", "притесн", "давлени", "репрессив" — le
# commentaire d'origine dans keywords.py dit explicitement "Russian
# stems / morphology handled by substring matching") que find_terms()
# ne peut jamais matcher : il exige une limite de mot immédiatement
# après le terme, donc "давлен" ne correspond à aucune forme réelle
# ("давление", "давлением"...). Sur un exemple concret, ça rendait
# "pression_administrative" (basé sur REPRESSION_TERMS en entier)
# systématiquement muet sur du texte russe, même très explicite.
#
# Motifs \bRACINE\w*\b — même principe que
# RUSSIAN_CENTRAL_ASIA_STEM_PATTERNS/REPRESSION_MORPHOLOGY_PATTERNS_V9
# (matching.py/keywords.py) : capture la racine et tout suffixe fléchi,
# sans jamais matcher à l'intérieur d'un autre mot (contrairement à une
# simple recherche de sous-chaîne, qui matcherait par exemple "сми" au
# début de "смирение").
#
# Ces motifs sont PLUS FINS que REPRESSION_MORPHOLOGY_PATTERNS_V9, qui
# dit seulement "il y a de la répression quelque part" : ici il faut
# savoir LAQUELLE (une détention n'est pas une condamnation). D'où une
# table par type de traitement plutôt qu'une liste unique.
_TRAITEMENT_STEM_PATTERNS: dict[str, list[str]] = {
    # "арест"/"задерж" : racines russes couvrant à la fois le nom et
    # le verbe/participe (арест/аресты/арестован/арестованный,
    # задержан/задержание/задержания) — remplace l'énumération forme
    # par forme de DETENTION_TERMS, incomplète par construction (le
    # pluriel "аресты" de l'exemple réel ne matchait aucune des formes
    # listées individuellement).
    "detention": [r"\bарест\w*\b", r"\bзадерж\w*\b"],
    # "осужден"/"заключен"/"приговор" : mêmes raisons pour
    # CONDAMNATION_TERMS (осужден couvre aussi осуждена/осуждены/
    # осужденный ; заключен couvre заключена/заключенный ; приговор
    # couvre aussi приговорен/приговорили, verbe/participe).
    "condamnation": [r"\bосужден\w*\b", r"\bзаключен\w*\b", r"\bприговор\w*\b"],
    "torture_mauvais_traitement": [r"\bпытк\w*\b", r"\bистязани\w*\b"],
    "disparition": [r"\bисчезнувш\w*\b"],
    # "преследован" et "притеснен" ne sont pas repris séparément :
    # déjà couverts par les préfixes plus courts "преследова"/
    # "притесн" ci-dessous (ex. "преследован" = "преследова" + "н").
    "pression_administrative": [
        r"\bрепресс\w*\b", r"\bпреследова\w*\b",
        r"\bдавлен\w*\b", r"\bзапугив\w*\b", r"\bугроз\w*\b",
        r"\bподавлен\w*\b", r"\bподавля\w*\b", r"\bгонен\w*\b",
        r"\bпритесн\w*\b",
    ],
    # Même raison que les autres racines russes : "цензура" se décline
    # (цензуры, цензуре, цензурой) et "заблокирован" s'accorde
    # (заблокирована, заблокированный), donc aucune forme énumérée ne
    # suffit. "блокиров" couvre блокировка/блокировать/блокировке.
    "censure_blocage": [
        r"\bцензур\w*\b", r"\bзаблокир\w*\b", r"\bблокиров\w*\b",
    ],
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


def _stem_match(text: str, pattern: str) -> str:
    """
    Mot réellement trouvé par un motif de racine, ou "" si aucun.

    Renvoyer le mot ("аресты") plutôt qu'un libellé générique
    ("(racine russe détectée)") : les preuves servent à auditer une
    catégorisation surprenante, et "une racine a matché" ne permet pas
    de dire laquelle ni de juger si c'est un faux positif.
    """
    found = compiled(pattern, re.I).search(text)
    return found.group(0) if found else ""


def _detect_type(article: dict[str, Any], body_text: str) -> tuple[str, str]:
    """
    Renvoie (type, raison) — la raison alimente preuves["type"].

    Le dernier cas est "indetermine" et non "page_institutionnelle" :
    audit du 2026-09-14 sur les 7795 articles publiés, l'ancien
    libellé couvrait 64,5% du corpus et 100% de ces articles n'avaient
    qu'un point commun — pas de date. Affirmer "page institutionnelle"
    sur cette seule base, c'est décrire l'absence d'information comme
    une observation. Or presque tout le corpus est sans corps (les
    liens Google News, un tiers du total, ne rendent jamais l'article)
    et sans date : on ne sait pas, et le schéma doit pouvoir le dire.
    """
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

    if not body_text:
        return "indetermine", "sans date et sans corps récupérable"

    return "indetermine", "sans date, corps court, aucun signal de plaidoyer"


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
    resolved_language = resolve_language(article.get("language"), full_text)

    # --------------------------------------------------------
    # GEO / GEO_ROLE
    # --------------------------------------------------------
    headline_geo_raw = _geo_terms_in(headline, resolved_language)
    body_geo_raw = _geo_terms_in(body, resolved_language)
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

    # Farsi : les listes d'acteurs ci-dessus sont quasi muettes en
    # persan, alors que keywords.py contient déjà des motifs
    # "acteur + répression à moins de 100 caractères" que scoring.py
    # exploite depuis toujours et que ce module ignorait. Sans eux, un
    # article de Fararu/IRNA sur un journaliste emprisonné ressortait
    # acteur=aucun. Motifs lancés uniquement sur du texte persan (ils
    # n'ont aucun sens ailleurs et coûtent cher).
    farsi_relation_hit = False
    if resolved_language == "fa":
        for key, patterns in (
            ("opposant", ACTIVIST_REPRESSION_FA_PATTERNS),
            ("journaliste", JOURNALIST_REPRESSION_FA_PATTERNS),
        ):
            if contains_pattern(full_text, patterns):
                farsi_relation_hit = True
                if key not in acteur:
                    acteur.append(key)
                preuves_acteur.setdefault(key, []).append(
                    "(motif farsi acteur+répression)"
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

        # Racines russes délibérément incomplètes (voir
        # _TRAITEMENT_STEM_PATTERNS) : find_terms() ne peut jamais les
        # matcher (limite de mot exigée juste après le terme), donc
        # vérifiées séparément via des motifs \bRACINE\w*\b.
        for pattern in _TRAITEMENT_STEM_PATTERNS.get(key, ()):
            found = _stem_match(full_text, pattern)
            if found:
                matched = list(matched) + [found]

        if matched:
            traitement.append(key)
            preuves_traitement[key] = matched

    if not traitement:
        traitement = ["aucun"]

        # Filet de diagnostic : le texte décrit une répression en russe
        # (morphologie partagée avec scoring.py) mais aucun type précis
        # n'a matché. C'est exactement le trou de vocabulaire à combler
        # — on le rend visible dans les preuves plutôt que de laisser un
        # "aucun" muet, qui ne dit pas s'il n'y a rien à voir ou si la
        # détection est passée à côté.
        if resolved_language == "ru" and has_russian_repression_morphology(full_text):
            preuves_traitement["_non_typé"] = [
                "répression détectée en russe, mais aucun type ne correspond "
                "— vocabulaire à enrichir"
            ]

    preuves["traitement"] = preuves_traitement

    # --------------------------------------------------------
    # RELATION ACTEUR / TRAITEMENT
    # --------------------------------------------------------
    acteur_terms_flat = [t for terms in ACTEUR_TYPE_TERMS.values() for t in terms]
    traitement_terms_flat = [t for terms in TRAITEMENT_TYPE_TERMS.values() for t in terms]

    # Les motifs farsi exigent déjà acteur et répression à moins de 100
    # caractères l'un de l'autre : c'est la relation, établie par
    # construction.
    relation_acteur_traitement = bool(
        farsi_relation_hit
        or (
            acteur != ["aucun"]
            and traitement != ["aucun"]
            and relation_present(full_text, acteur_terms_flat, traitement_terms_flat)
        )
    )

    # Les preuves passent par find_terms (limite de mot) et non par un
    # test de sous-chaîne : "in full_text" listait des termes que la
    # détection elle-même n'aurait jamais retenus (ex. "arrest" trouvé
    # dans "arrested"), donnant des preuves qui ne correspondaient pas
    # à ce qui a réellement déclenché la relation.
    preuves["relation_acteur_traitement"] = (
        {
            "acteur_termes": find_terms(full_text, acteur_terms_flat),
            "traitement_termes": find_terms(full_text, traitement_terms_flat),
            "via_motif_farsi": farsi_relation_hit,
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


# ============================================================
# AGRÉGATION POUR LE TABLEAU DE BORD
# ============================================================

# Valeur "rien détecté" de chaque axe. Elle est comptée à part et
# jamais affichée comme une classe : "aucun" représente 92% de l'axe
# acteur, donc le laisser dans le même graphique écraserait les onze
# classes réelles contre l'axe et ne dirait qu'une chose, déjà dite par
# le taux de couverture.
_AXE_VALEUR_NULLE = {
    "geo": None,            # liste vide
    "acteur": "aucun",
    "traitement": "aucun",
    "type": "indetermine",
}

# (clé, libellé, multivalué) — l'ordre est celui de l'affichage.
AXES_DESCRIPTIFS: tuple[tuple[str, str, bool], ...] = (
    ("geo", "Géographie", True),
    ("acteur", "Acteur visé", True),
    ("traitement", "Traitement subi", True),
    ("type", "Type d'article", False),
)


def _valeurs_axe(categorisation: dict[str, Any], axe: str, multivalue: bool) -> list[str]:
    brut = categorisation.get(axe)

    if not multivalue:
        return [brut] if brut else []

    return list(brut or [])


def agreger_categorisations(categorisations: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compte les classes de chaque axe descriptif sur un corpus.

    Renvoie, par axe : les classes triées par effectif décroissant, et
    le nombre d'articles que l'axe décrit réellement (au moins une
    classe non nulle).

    Le taux de couverture est délibérément séparé des effectifs. Sans
    lui, un tableau de bord montrerait "journaliste 164, minorité 139"
    et donnerait l'impression d'un corpus abondamment décrit, alors que
    92% des articles n'ont aucun acteur identifié. L'effectif dit ce
    qu'on a trouvé, la couverture dit sur quelle part du corpus — les
    deux sont nécessaires pour ne pas surinterpréter le premier.

    Les axes multivalués (un article peut être à la fois Kazakhstan et
    Russie) ne somment pas à 100% : c'est pourquoi on renvoie "total"
    plutôt que de laisser l'affichage déduire un dénominateur.
    """
    total = len(categorisations)
    axes = []

    for axe, libelle, multivalue in AXES_DESCRIPTIFS:
        valeur_nulle = _AXE_VALEUR_NULLE[axe]
        compteur: dict[str, int] = {}
        decrits = 0

        for categorisation in categorisations:
            valeurs = _valeurs_axe(categorisation, axe, multivalue)
            reelles = [v for v in valeurs if v != valeur_nulle]

            if reelles:
                decrits += 1

            for valeur in reelles:
                compteur[valeur] = compteur.get(valeur, 0) + 1

        classes = sorted(compteur.items(), key=lambda kv: (-kv[1], kv[0]))

        axes.append({
            "cle": axe,
            "libelle": libelle,
            "multivalue": multivalue,
            "classes": [{"nom": nom, "effectif": n} for nom, n in classes],
            "decrits": decrits,
            "couverture": round(100 * decrits / total, 1) if total else 0.0,
        })

    return {"total": total, "axes": axes}
