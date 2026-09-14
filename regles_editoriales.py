"""
regles_editoriales.py — la couche éditoriale, séparée de la couche
factuelle (categorisation.py, module voisin).

categorisation.py décrit un article (région, acteur, traitement...)
sans jamais dire si on s'y intéresse. Ce module fait l'inverse : il ne
détecte rien, il applique des choix — quel périmètre géographique
retenir, quels acteurs comptent, quels traitements comptent, etc. —
sur le dict que categoriser() renvoie. Changer d'avis sur le périmètre
éditorial ne doit jamais nécessiter de retoucher categorisation.py ni
scoring.py.

Aucune valeur ci-dessous n'est devinée : les constantes qui encodent
un choix éditorial réel sont laissées à None (TODO), avec les options
possibles listées en commentaire. Tant qu'une constante reste à None,
est_pertinent() ne filtre PAS sur ce critère (elle ne bloque rien
plutôt que d'appliquer un choix que personne n'a fait). Remplir une
constante l'active comme un vrai filtre.

Aucune de ces valeurs ne doit être dupliquée en dur ailleurs dans le
code (scoring.py, news_scanner.py...) : c'est tout l'intérêt de la
séparation — un seul endroit à modifier pour changer le périmètre.
"""

from __future__ import annotations

from typing import Any


# ============================================================
# VERSION
# ============================================================

# À incrémenter à chaque changement des constantes ci-dessous, pour
# pouvoir dater/tracer quelle version des règles a produit une
# décision "pertinent"/"rejeté" donnée (utile en audit, ou si les
# règles changent et qu'on veut re-évaluer un corpus déjà catégorisé
# sans le re-scanner).
VERSION_REGLES = "2026-09-12.1"


# ============================================================
# CHOIX ÉDITORIAUX — TODO : aucune valeur devinée
# ============================================================

# Périmètre géographique retenu.
# Options possibles (voir categorisation.py: geo) :
#   - Un sous-ensemble de {"kazakhstan", "ouzbekistan", "kirghizistan",
#     "tadjikistan", "turkmenistan", "azerbaidjan", "armenie",
#     "georgie", "caucase_nord", "xinjiang", "iran", "afghanistan",
#     "russie", "autre"}
#   - Les 5 pays d'Asie centrale seuls
#   - Asie centrale + Caucase
#   - Asie centrale + Caucase + Xinjiang (couverture actuelle de
#     scoring.py: regional_context = central_asia OR caucasus OR uyghur)
#   - Région élargie incluant Iran/Afghanistan/Russie comme contexte
#     géopolitique plutôt que comme cœur de cible
# TODO: décider et remplacer None par un frozenset, ex.
#   PERIMETRE_GEO = frozenset({"kazakhstan", "ouzbekistan", ...})
PERIMETRE_GEO: frozenset[str] | None = None

# geo_role minimum accepté.
# Options possibles (voir categorisation.py: geo_role) :
#   - "sujet_principal" seul (le plus strict : la région doit être
#     annoncée dans le titre ou le chapô)
#   - "mention_secondaire" accepté aussi (plus permissif : une simple
#     mention dans le corps suffit — c'est peu ou prou ce que fait
#     aujourd'hui scoring.strong_body_geography, avec un seuil de 2
#     mentions plutôt qu'1)
# TODO: décider et remplacer None, ex. GEO_ROLE_MINIMUM = "mention_secondaire"
GEO_ROLE_MINIMUM: str | None = None

# acteur_role / traitement_role minimum accepté.
#
# Même mécanique que GEO_ROLE_MINIMUM, mais c'est ici que se joue le
# problème le plus coûteux du schéma. Mesuré le 2026-09-14 : sur les
# 1870 articles portant un acteur, 1424 (76%) ne le tiennent QUE du
# corps. "Armenia Courts Central Asia As TRIPP Corridor" ressort
# "femme", "Pickleball in China" ressort journaliste + femme +
# citoyen — des mots incidents dans 8000 caractères.
#
# Options :
#   - "sujet_principal" : l'acteur doit être nommé dans le titre ou le
#     chapô. Le plus net, mais il écarte aussi de vrais sujets — "The
#     Horrors Of Aktas Mental Hospital" est un cas réel de droits
#     humains dont les acteurs ne sont nommés que dans le corps.
#   - "mention_secondaire" : comportement actuel, tout est accepté.
#   - Piste intermédiaire, à écrire à la main si elle vous convient :
#     accepter "mention_secondaire" UNIQUEMENT quand
#     relation_acteur_traitement est vrai (l'acteur et ce qu'il subit
#     sont proches dans le texte). C'est le compromis qui garde Aktas
#     et écarte Pickleball.
#
#     La proximité exigée se règle par categorisation.FENETRE_RELATION
#     (140 caractères par défaut). Ce n'est pas une règle éditoriale
#     mais la définition du champ lui-même, d'où son emplacement ; la
#     courbe qui justifie la valeur est documentée au-dessus de
#     matching.FENETRE_RELATION_DEFAUT.
# TODO: décider et remplacer None, ex. ACTEUR_ROLE_MINIMUM = "sujet_principal"
ACTEUR_ROLE_MINIMUM: str | None = None
TRAITEMENT_ROLE_MINIMUM: str | None = None

# Acteurs retenus.
# Options possibles (voir categorisation.py: acteur) — un sous-ensemble
# de {"defenseur", "journaliste", "opposant", "avocat", "croyant",
# "minorite_ethnique", "femme", "migrant", "ecologiste", "syndicaliste",
# "citoyen_ordinaire", "aucun"} :
#   - Uniquement les cibles "classiques" HR : defenseur/journaliste/
#     opposant/avocat
#   - Élargi aux minorités : + croyant/minorite_ethnique/femme/migrant
#   - Élargi aux nouveaux mouvements : + ecologiste/syndicaliste
#   - Tout le monde sauf "aucun" (n'importe quel acteur identifié
#     suffit)
# TODO: décider et remplacer None par un frozenset.
ACTEURS_RETENUS: frozenset[str] | None = None

# Traitements retenus.
# Options possibles (voir categorisation.py: traitement) — un
# sous-ensemble de {"detention", "condamnation",
# "torture_mauvais_traitement", "disparition", "violence_physique",
# "censure_blocage", "pression_administrative", "contrainte_travail",
# "expulsion_extradition", "aucun"} :
#   - Uniquement les traitements graves : torture_mauvais_traitement/
#     disparition/violence_physique
#   - + detention/condamnation (répression judiciaire, pas seulement
#     physique)
#   - + censure_blocage/pression_administrative (répression non
#     carcérale)
#   - Tout sauf "aucun"
# TODO: décider et remplacer None par un frozenset.
TRAITEMENTS_RETENUS: frozenset[str] | None = None

# Types d'article exclus.
# Options possibles (voir categorisation.py: type) — un sous-ensemble
# de {"evenement_date", "rapport_analyse", "plaidoyer_communique",
# "page_thematique", "indetermine", "navigation"}.
#
# Répartition mesurée le 2026-09-14 sur les 7795 articles publiés :
#   evenement_date        35,1%
#   indetermine           64,5%   (ni date ni corps récupérable)
#   rapport_analyse        0,2%
#   plaidoyer_communique   0,1%
#   navigation             0,0%   (filtré dès l'ingestion)
#
#   - "navigation" ne coûte rien à exclure, mais ne rapporte rien non
#     plus : looks_like_article_link() écarte déjà ces liens à
#     l'ingestion, donc aucun n'atteint cette couche.
#   - "indetermine" NE DOIT PAS être exclu à la légère : ce n'est pas
#     un jugement ("page sans intérêt") mais un aveu ("on n'a ni date
#     ni corps"). L'exclure jetterait les deux tiers du corpus sur la
#     base de ce qu'on n'a pas réussi à récupérer — notamment tous les
#     liens Google News, dont le corps n'est structurellement jamais
#     accessible (voir fetch_all_bodies.py).
#   - "page_thematique" est LE filtre qui a un sens aujourd'hui : ce
#     sont des pages de rubrique (pays, région, thème) et du mobilier
#     de site, jamais des articles — "Burkina Faso" chez CPJ, "Central
#     Asia" chez Eurasianet, "Cookie Statement" chez Amnesty. Les
#     exclure retire 442 non-articles sans rien perdre :
#       TYPES_EXCLUS = frozenset({"page_thematique", "navigation"})
#   - "plaidoyer_communique" est un vrai choix éditorial (actualité
#     plutôt que communiqués), mais porte sur 45 articles.
#   - "rapport_analyse" est souvent la source la plus détaillée.
#
# Le champ "type" sert d'abord à décrire ; "page_thematique" est la
# seule valeur qui se prête aussi à un tri, parce qu'elle désigne des
# pages qui ne sont pas du journalisme du tout.
TYPES_EXCLUS: frozenset[str] | None = None

# Âge maximum accepté (en jours).
# Options possibles (voir categorisation.py: age_jours) :
#   - Pas de limite (None) : cohérent avec la décision du 2026-09-11 de
#     ne jamais pénaliser le score sur la fraîcheur (voir scoring.py)
#   - Une fenêtre courte (7-14 jours) si on veut de l'actualité chaude
#     seulement — cohérent avec MAX_ARTICLE_AGE_DAYS de synthesis.py
#   - Une fenêtre large (60-90 jours) alignée sur ARCHIVAL_AGE_DAYS de
#     html_template.py (au-delà, un article est déjà marqué "republié"
#     à l'affichage)
# TODO: décider et remplacer None par un entier, ex. AGE_MAXIMUM_JOURS = 14
AGE_MAXIMUM_JOURS: int | None = None

# Faut-il exiger que relation_acteur_traitement soit vrai (acteur et
# traitement doivent co-occurrer dans le texte, pas seulement être
# présents chacun de leur côté) ?
# Options possibles :
#   - True : plus strict, réduit les faux positifs (ex. un article qui
#     mentionne un journaliste ET une détention sans rapport entre eux)
#   - False : plus permissif, garde tout article où acteur ET
#     traitement sont présents quelque part dans le texte
#   - None : pas encore décidé (voir TODO ci-dessous pour le
#     comportement par défaut)
# TODO: décider et remplacer None par True/False.
EXIGER_RELATION_ACTEUR_TRAITEMENT: bool | None = None


# ============================================================
# APPLICATION DES RÈGLES
# ============================================================

def est_pertinent(categorisation: dict[str, Any]) -> tuple[bool, str]:
    """
    Applique les choix éditoriaux ci-dessus à une categorisation()
    (categorisation.py). Renvoie (pertinent, raison) — raison est
    toujours renseignée, y compris quand pertinent=True (ex.
    "pertinent" tout court si tous les filtres sont encore des TODO
    non configurés).

    Tant qu'une constante reste à None (TODO non résolu), le critère
    correspondant n'est PAS appliqué : ce module reste fonctionnel dès
    aujourd'hui (permissif par défaut) sans qu'aucune valeur n'ait été
    devinée à la place de l'utilisateur.
    """
    geo = categorisation.get("geo", [])
    geo_role = categorisation.get("geo_role", "absent")
    acteur = categorisation.get("acteur", ["aucun"])
    traitement = categorisation.get("traitement", ["aucun"])
    type_article = categorisation.get("type", "")
    age_jours = categorisation.get("age_jours")
    relation = categorisation.get("relation_acteur_traitement", False)

    if PERIMETRE_GEO is not None:
        if not (set(geo) & PERIMETRE_GEO):
            return False, "hors périmètre géographique retenu"

    if GEO_ROLE_MINIMUM is not None:
        rank = {"absent": 0, "mention_secondaire": 1, "sujet_principal": 2}
        if rank.get(geo_role, 0) < rank.get(GEO_ROLE_MINIMUM, 0):
            return False, f"geo_role '{geo_role}' sous le minimum requis"

    acteur_role = categorisation.get("acteur_role", "absent")
    traitement_role = categorisation.get("traitement_role", "absent")

    _RANG_ROLE = {"absent": 0, "mention_secondaire": 1, "sujet_principal": 2}

    if ACTEUR_ROLE_MINIMUM is not None:
        if _RANG_ROLE.get(acteur_role, 0) < _RANG_ROLE.get(ACTEUR_ROLE_MINIMUM, 0):
            return False, f"acteur_role '{acteur_role}' sous le minimum requis"

    if TRAITEMENT_ROLE_MINIMUM is not None:
        if _RANG_ROLE.get(traitement_role, 0) < _RANG_ROLE.get(
            TRAITEMENT_ROLE_MINIMUM, 0
        ):
            return False, f"traitement_role '{traitement_role}' sous le minimum requis"

    if ACTEURS_RETENUS is not None:
        if not (set(acteur) & ACTEURS_RETENUS):
            return False, "aucun acteur retenu détecté"

    if TRAITEMENTS_RETENUS is not None:
        if not (set(traitement) & TRAITEMENTS_RETENUS):
            return False, "aucun traitement retenu détecté"

    if TYPES_EXCLUS is not None:
        if type_article in TYPES_EXCLUS:
            return False, f"type d'article exclu: {type_article}"

    if AGE_MAXIMUM_JOURS is not None:
        if age_jours is not None and age_jours > AGE_MAXIMUM_JOURS:
            return False, f"article trop ancien ({age_jours} j > {AGE_MAXIMUM_JOURS} j)"

    if EXIGER_RELATION_ACTEUR_TRAITEMENT:
        if not relation:
            return False, "acteur et traitement ne co-occurrent pas dans le texte"

    return True, "pertinent"
