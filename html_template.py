# html_template.py

import html
from datetime import datetime, timezone

from sources import PROFILE_GROUP_ORDER
from text_utils import article_age_days


def esc(value):
    """Escape HTML safely."""
    return html.escape(str(value))


# Schémas autorisés dans un href. Les URL affichées viennent du HTML
# scrapé de sites tiers : un site compromis (ou simplement malveillant)
# peut servir un <a href="javascript:..."> que le scanner republierait
# tel quel en lien cliquable sur le site public. L'échappement HTML ne
# protège pas de ça — il rend le texte inoffensif, pas le schéma.
_SAFE_URL_SCHEMES = ("http://", "https://")


def safe_url(value):
    """URL sûre pour un href, ou "" si le schéma n'est pas autorisé."""
    url = str(value or "").strip()

    if url.lower().startswith(_SAFE_URL_SCHEMES):
        return esc(url)

    return ""


def format_date(date):
    """Format article date."""

    if not date:
        return "Date non disponible"

    return date.strftime(
        "%d/%m/%Y à %H:%M UTC"
    )


# Seuil au-delà duquel une carte affiche le badge "republié" : purement
# informatif, n'influence jamais le score ni le niveau (voir
# scoring.py — le score reste une mesure de pertinence sémantique, pas
# de fraîcheur). Sert à repérer d'un coup d'œil un vieux rapport qui
# refait surface (ex. via le contournement Google News sur un site
# bloqué). Décidé avec l'utilisateur le 2026-09-11.
ARCHIVAL_AGE_DAYS = 60


def format_relative_age(date, now=None):
    """Âge relatif lisible ("il y a 3 j", "hier"...) pour l'affichage."""

    age_days = article_age_days(date, now=now)

    if age_days is None:
        return ""

    if age_days < 0:
        return "à l'instant"

    if age_days < 1:
        hours = max(1, int(age_days * 24))
        return f"il y a {hours} h"

    if age_days < 2:
        return "hier"

    if age_days < 30:
        return f"il y a {int(age_days)} j"

    if age_days < 365:
        return f"il y a {int(age_days / 30)} mois"

    return f"il y a {int(age_days / 365)} an(s)"


def render_stat(
    number,
    label,
):
    """Render one dashboard statistic."""

    return f"""
    <div class="stat">

        <div class="stat-number">
            {esc(number)}
        </div>

        <div class="stat-label">
            {esc(label)}
        </div>

    </div>
    """


# ============================================================
# VOCABULAIRE DES TITRES
# ============================================================

def render_title_vocabulary(
    title_words,
):
    """
    Render the most frequent words found in article titles.

    title_words is expected to be:

    [
        {
            "word": "kazakhstan",
            "count": 42,
        },
        ...
    ]
    """

    if not title_words:
        return ""

    words = []

    for item in title_words:

        word = item.get(
            "word",
            "",
        )

        count = item.get(
            "count",
            0,
        )

        if not word:
            continue

        words.append(
            f"""
            <span class="word-chip">

                <span class="word">
                    {esc(word)}
                </span>

                <span class="word-count">
                    {esc(count)}
                </span>

            </span>
            """
        )

    if not words:
        return ""

    return f"""
    <section class="title-vocabulary">

        <div class="title-vocabulary-header">

            <div>

                <h2>
                    Mots fréquents dans les titres
                </h2>

                <p class="vocabulary-description">

                    Vocabulaire extrait automatiquement
                    des titres des articles analysés.
                    Plus le nombre est élevé,
                    plus le mot apparaît souvent.

                </p>

            </div>

        </div>

        <div class="word-cloud">

            {"".join(words)}

        </div>

    </section>
    """


# ============================================================
# TABLEAU DE BORD DE CATÉGORISATION
# ============================================================

# Libellés lisibles pour les valeurs du schéma (categorisation.py),
# qui sont des identifiants sans accent ni espace.
_LIBELLES_CLASSES = {
    "caucase_nord": "Caucase du Nord",
    "azerbaidjan": "Azerbaïdjan",
    "georgie": "Géorgie",
    "armenie": "Arménie",
    "kazakhstan": "Kazakhstan",
    "kirghizistan": "Kirghizistan",
    "iran": "Iran",
    "xinjiang": "Xinjiang",
    "afghanistan": "Afghanistan",
    "indetermine": "Indéterminé",
    "tadjikistan": "Tadjikistan",
    "turkmenistan": "Turkménistan",
    "ouzbekistan": "Ouzbékistan",
    "russie": "Russie",
    "ukraine": "Ukraine",
    "chine": "Chine",
    "bielorussie": "Biélorussie",
    "turquie": "Turquie",
    "moldavie": "Moldavie",
    "autre": "Autre / non régional",
    "asie_centrale": "Asie centrale (région)",
    "caucase": "Caucase (région)",
    "ossetie": "Ossétie",
    "defenseur": "Défenseur des droits",
    "journaliste": "Journaliste",
    "opposant": "Opposant / activiste",
    "avocat": "Avocat",
    "croyant": "Croyant",
    "minorite_ethnique": "Minorité ethnique",
    "femme": "Femme",
    "migrant": "Migrant / réfugié",
    "ecologiste": "Écologiste",
    "syndicaliste": "Syndicaliste",
    "citoyen_ordinaire": "Citoyen ordinaire",
    "minorite_sexuelle": "Minorité sexuelle",
    "detenu": "Détenu / prisonnier politique",
    "universitaire": "Universitaire",
    "artiste": "Artiste / écrivain",
    "detention": "Détention",
    "condamnation": "Condamnation",
    "torture_mauvais_traitement": "Torture / mauvais traitement",
    "disparition": "Disparition",
    "violence_physique": "Violence physique",
    "censure_blocage": "Censure / blocage",
    "pression_administrative": "Pression administrative",
    "contrainte_travail": "Travail forcé",
    "expulsion_extradition": "Expulsion / extradition",
    "criminalisation": "Criminalisation",
    "surveillance": "Surveillance",
    "internement_psychiatrique": "Internement psychiatrique",
    "interdiction_voyager": "Interdiction de voyager",
    "exil_force": "Exil forcé",
    "evenement_date": "Événement daté",
    "rapport_analyse": "Rapport / analyse",
    "plaidoyer_communique": "Plaidoyer / communiqué",
    "navigation": "Page de navigation",
    "page_thematique": "Page thématique / pays",
    "aucun": "aucun",
}


def _libelle_classe(nom):
    """
    Libellé lisible d'une valeur du schéma.

    Les pays du monde viennent de la table générée (pays_monde.py) :
    les énumérer une seconde fois ici ne ferait que créer une occasion
    de divergence.
    """
    if nom in _LIBELLES_CLASSES:
        return _LIBELLES_CLASSES[nom]

    from pays_monde import PAYS_MONDE_LIBELLES

    return PAYS_MONDE_LIBELLES.get(nom, nom.replace("_", " "))


# ============================================================
# CATÉGORISATION (categorisation.py / regles_editoriales.py)
# ============================================================
#
# Signal indépendant de scoring.py : décrit l'article (région, acteur
# visé, traitement subi, type...) sans jamais influencer
# score/level/theme/relevant ci-dessus, qui restent entièrement
# décidés par classify_article(). "" si l'article n'a pas encore été
# catégorisé (categorisation.py pas branché à ce point du pipeline).

def _categorisation_summary(article):
    cat = article.get("categorisation")
    if not cat:
        return ""

    def lisible(valeurs):
        # Mêmes libellés que le tableau de bord : le lecteur d'une
        # carte et celui d'un graphique doivent voir le même mot, pas
        # "minorite_ethnique" ici et "Minorité ethnique" là-bas.
        return ", ".join(_libelle_classe(v) for v in valeurs)

    geo = lisible(cat.get("geo") or []) or "aucune"
    acteur = lisible(cat.get("acteur") or ["aucun"])
    traitement = lisible(cat.get("traitement") or ["aucun"])
    type_article = _libelle_classe(cat["type"]) if cat.get("type") else ""

    # Le rôle est annoté entre parenthèses : "acteur: Journaliste
    # (mention)" dit d'un coup d'oeil que le terme vient du corps et
    # non du titre — la différence entre un article SUR un journaliste
    # et un article qui en cite un au passage.
    def annoter(valeurs, role):
        if valeurs == "aucun" or not role or role == "sujet_principal":
            return valeurs
        if role == "mention_secondaire":
            return f"{valeurs} (mention)"
        return valeurs

    acteur = annoter(acteur, cat.get("acteur_role"))
    traitement = annoter(traitement, cat.get("traitement_role"))

    return f"geo: {geo} · acteur: {acteur} · traitement: {traitement} · type: {type_article}"


def _categorisation_pertinence(article):
    """
    (icône, raison) pour categorisation_pertinent/categorisation_reason
    — distinct du "Retenu" existant (article["relevant"], calculé par
    scoring.py). Tant que regles_editoriales.py n'a aucune constante
    configurée, ceci vaut toujours (True, "pertinent").
    """
    if "categorisation_pertinent" not in article:
        return "", ""

    icon = "✓" if article.get("categorisation_pertinent") else "—"
    return icon, article.get("categorisation_reason", "")


# ============================================================
# ARTICLE CARD
# ============================================================

def render_article_card(
    article,
):
    """Render one selected article."""

    level = article.get(
        "level",
        "E",
    )

    score = article.get(
        "score",
        0,
    )

    source = article.get(
        "source",
        "",
    )

    source_label = article.get(
        "source_label",
        "",
    )

    title = article.get(
        "title",
        "",
    )

    url = article.get(
        "url",
        "",
    )

    summary = article.get(
        "summary",
        "",
    )

    theme = article.get(
        "theme",
        "",
    )

    reasons = article.get(
        "reasons",
        [],
    )

    raw_date = article.get("date")

    date = format_date(raw_date)

    relative_age = format_relative_age(raw_date)

    age_days = article_age_days(raw_date)

    is_archival = age_days is not None and age_days >= ARCHIVAL_AGE_DAYS

    reasons_text = " • ".join(
        reasons
    )

    archival_badge = (
        """
            <span class="badge badge-archival" title="Article ancien republié récemment">
                🕓 republié
            </span>
        """
        if is_archival
        else ""
    )

    categorisation_summary = _categorisation_summary(article)
    categorisation_icon, categorisation_reason = _categorisation_pertinence(article)
    categorisation_block = (
        f"""
        <div class="categorisation">

            <strong>
                Catégorisation (indépendante du score) :
            </strong>
            {esc(categorisation_summary)}

            {f'<div class="categorisation-pertinence">{esc(categorisation_icon)} {esc(categorisation_reason)}</div>' if categorisation_icon else ""}

        </div>
        """
        if categorisation_summary
        else ""
    )

    return f"""
    <article class="article-card">

        <div class="article-top">

            <span class="
                badge
                badge-{esc(level)}
            ">
                {esc(level)}
            </span>

            <strong class="score">
                {esc(score)}/100
            </strong>

            {archival_badge}

        </div>

        <div class="source">

            {esc(source)}

            <span class="source-profile">
                {esc(source_label)}
            </span>

        </div>

        <h3>

            <a
                href="{safe_url(url)}"
                target="_blank"
                rel="noopener noreferrer"
            >
                {esc(title)}
            </a>

        </h3>

        <div class="date">

            📅 {esc(date)}
            {f'<span class="relative-age">({esc(relative_age)})</span>' if relative_age else ""}

        </div>

        <div class="theme">

            {esc(theme)}

        </div>

        <p>

            {esc(summary[:900])}

        </p>

        <div class="reasons">

            <strong>
                Pourquoi :
            </strong>

            {esc(reasons_text)}

        </div>

        {categorisation_block}

    </article>
    """


# ============================================================
# LEVEL SECTION
# ============================================================

def render_level_section(
    level,
    articles,
):
    """Render one A/B/C section."""

    if not articles:
        return ""

    titles = {

        "A":
            "🟥 A — Droits humains / répression",

        "B":
            "🟧 B — Politique intérieure",

        "C":
            "🟦 C — Géopolitique majeure",

    }

    cards = []

    for article in articles:

        cards.append(
            render_article_card(
                article
            )
        )

    return f"""
    <section class="level-section">

        <h2>
            {titles[level]}
        </h2>

        {''.join(cards)}

    </section>
    """


# ============================================================
# AUDIT ROW
# ============================================================

def render_audit_row(
    article,
):
    """Render one audit table row."""

    level = article.get(
        "level",
        "E",
    )

    retained = (
        "✓"
        if article.get(
            "relevant",
            False,
        )
        else "—"
    )

    categorisation_summary = _categorisation_summary(article)
    categorisation_icon, categorisation_reason = _categorisation_pertinence(article)

    return f"""
    <tr>

        <td>

            <span class="
                badge
                badge-{esc(level)}
            ">
                {esc(level)}
            </span>

        </td>

        <td>

            <strong>
                {esc(
                    article.get(
                        "score",
                        0,
                    )
                )}/100
            </strong>

        </td>

        <td>

            {esc(
                format_date(
                    article.get(
                        "date"
                    )
                )
            )}

        </td>

        <td>

            {esc(
                article.get(
                    "source",
                    "",
                )
            )}

        </td>

        <td>

            {esc(
                article.get(
                    "theme",
                    "",
                )
            )}

        </td>

        <td>

            <a
                href="{safe_url(
                    article.get(
                        "url",
                        "",
                    )
                )}"
                target="_blank"
                rel="noopener noreferrer"
            >

                {esc(
                    article.get(
                        "title",
                        "",
                    )
                )}

            </a>

        </td>

        <td>

            {retained}

        </td>

        <td class="audit-categorisation">

            {esc(categorisation_summary)}

        </td>

        <td>

            {esc(categorisation_icon)}
            <span class="audit-reason">{esc(categorisation_reason)}</span>

        </td>

    </tr>
    """


def render_audit_group(
    category,
    rows_html,
    count,
):
    """Render one category block of the audit table (heading + table)."""

    return f"""
    <div class="audit-group">

        <h3>
            {esc(category)}
            <span class="audit-group-count">
                {esc(count)} article{esc("s" if count != 1 else "")}
            </span>
        </h3>

        <div class="audit-wrapper">

        <table>

        <thead>
        <tr>
            <th>Niveau</th>
            <th>Score</th>
            <th>Date</th>
            <th>Source</th>
            <th>Thème</th>
            <th>Article</th>
            <th>Retenu</th>
            <th>Catégorisation</th>
            <th>Pertinent (règles)</th>
        </tr>
        </thead>

        <tbody>
        {rows_html}
        </tbody>

        </table>

        </div>

    </div>
    """


# ============================================================
# DASHBOARD
# ============================================================

def render_synthesis(
    synthesis,
):
    """Render the generated synthesis section, if any."""

    if not synthesis:
        return ""

    return f"""
    <section class="synthesis">

        <h2>
            🧭 Synthèse du jour
        </h2>

        <p class="synthesis-text">
            {esc(synthesis)}
        </p>

        <p class="synthesis-note">
            Généré automatiquement à partir des articles de niveau A —
            à vérifier avant citation.
        </p>

    </section>
    """


def render_dashboard(
    stats,
):
    """Render statistics dashboard."""

    return f"""
    <div class="dashboard">

        {render_stat(
            stats["analyzed"],
            "📰 Articles analysés"
        )}

        {render_stat(
            stats["retained"],
            "🎯 Articles retenus"
        )}

        {render_stat(
            f'{stats["avg_score"]}/100',
            "📊 Score moyen"
        )}

        {render_stat(
            stats["level_a"],
            "🟥 Niveau A"
        )}

        {render_stat(
            stats["level_b"],
            "🟧 Niveau B"
        )}

        {render_stat(
            stats["level_c"],
            "🟦 Niveau C"
        )}

        {render_stat(
            stats["level_d"],
            "⚪ Niveau D — activistes hors région"
        )}

        {render_stat(
            stats["level_e"],
            "⬜ Niveau E — bruit"
        )}

        {render_stat(
            stats.get("level_f", 0),
            "🗂️ Niveau F — pages de rubrique"
        )}

        {render_stat(
            f'{stats["sources_successful"]}/{stats["sources_total"]}',
            "📡 Sources analysées"
        )}

        {render_stat(
            f'{stats["relevance_rate"]}%',
            "🎯 Taux de pertinence"
        )}

    </div>
    """


def render_categorisation_axe(axe, total):
    """
    Un axe descriptif : son taux de couverture, puis ses classes en
    barres horizontales.

    Barres horizontales et non verticales parce que les libellés sont
    longs ("torture / mauvais traitement") et qu'il y a jusqu'à
    quatorze classes : en colonnes, les étiquettes se chevauchent ou
    basculent à l'oblique.

    Une seule teinte pour toutes les barres : la longueur porte déjà la
    grandeur, et les classes n'ont pas d'ordre naturel. Les colorer
    chacune différemment coderait deux fois la même information, ou
    ferait croire à une progression qui n'existe pas.

    Chaque barre porte son effectif en clair : l'échelle est propre à
    l'axe (sinon les onze classes d'"acteur", toutes sous 170, seraient
    des traits invisibles à côté des 2738 événements datés), donc la
    longueur ne se compare qu'à l'intérieur d'un même axe. Le nombre
    écrit, lui, se compare partout.
    """
    classes = axe["classes"]
    maximum = max((c["effectif"] for c in classes), default=0)

    lignes = []

    for classe in classes:
        effectif = classe["effectif"]
        largeur = (100 * effectif / maximum) if maximum else 0
        part = (100 * effectif / total) if total else 0

        lignes.append(f"""
        <div
            class="cat-ligne"
            title="{esc(_libelle_classe(classe['nom']))} — {effectif} articles ({part:.1f}% du corpus)"
        >
            <div class="cat-nom">{esc(_libelle_classe(classe["nom"]))}</div>
            <div class="cat-piste">
                <div class="cat-barre" style="width: {largeur:.1f}%"></div>
            </div>
            <div class="cat-valeur">{effectif}</div>
        </div>
        """)

    if not lignes:
        lignes.append(
            '<div class="cat-vide">Aucune classe détectée sur ce corpus.</div>'
        )

    return f"""
    <div class="cat-carte">

        <div class="cat-entete">
            <h3>{esc(axe["libelle"])}</h3>
            <div class="cat-couverture-valeur">{axe["couverture"]:.1f}%</div>
        </div>

        <div class="cat-piste cat-piste-couverture">
            <div
                class="cat-barre cat-barre-couverture"
                style="width: {axe["couverture"]:.1f}%"
            ></div>
        </div>

        <div class="cat-sous-titre">
            {axe["decrits"]} articles sur {total} portent au moins une valeur
        </div>

        <div class="cat-lignes">
            {"".join(lignes)}
        </div>

    </div>
    """


def render_categorisation_dashboard(cat_stats):
    """
    Tableau de bord des catégories descriptives (categorisation.py).

    Distinct du tableau de bord de scoring juste au-dessus, et c'est
    voulu : celui-là dit ce qu'on a RETENU, celui-ci ce qu'on a su
    DÉCRIRE. Les deux chiffres n'ont rien à voir et les confondre
    donnerait une fausse impression de couverture.
    """
    if not cat_stats or not cat_stats.get("total"):
        return ""

    total = cat_stats["total"]

    cartes = "".join(
        render_categorisation_axe(axe, total)
        for axe in cat_stats["axes"]
    )

    return f"""
    <h2>Catégorisation du corpus</h2>

    <p class="subtitle">

    Description factuelle des {total} articles archivés, indépendante du
    score. Un article peut porter plusieurs valeurs sur un même axe
    (Kazakhstan <em>et</em> Russie), donc les effectifs d’un axe ne
    s’additionnent pas à 100&nbsp;%. L’échelle des barres est propre à
    chaque axe.

    </p>

    <div class="cat-grille">
        {cartes}
    </div>
    """


# ============================================================
# CSS
# ============================================================

def render_css():
    """Return all website CSS."""

    return """
<style>

* {
    box-sizing: border-box;
}

body {

    margin: auto;

    max-width: 1400px;

    padding: 30px;

    background: #f5f6f8;

    color: #202124;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

h1 {
    margin-bottom: 6px;
}

.subtitle {
    color: #666;
    line-height: 1.5;
}

.scan-date {

    margin:
        12px 0 25px;

    font-size: 14px;

    color: #555;
}


/* ========================================================
   SYNTHÈSE
======================================================== */

.synthesis {

    background: #eef4ff;

    border-left: 4px solid #3a5fcd;

    border-radius: 6px;

    padding: 18px 22px;

    margin-bottom: 30px;
}

.synthesis h2 {

    margin: 0 0 10px;

    font-size: 18px;
}

.synthesis-text {

    line-height: 1.6;

    white-space: pre-wrap;
}

.synthesis-note {

    margin-top: 10px;

    font-size: 12px;

    color: #667;
}


/* ========================================================
   DASHBOARD
======================================================== */

.dashboard {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(140px, 1fr)
        );

    gap: 12px;

    margin-bottom: 40px;
}

.stat {

    background: white;

    padding: 18px;

    border-radius: 10px;

    box-shadow:
        0 2px 8px
        rgba(0,0,0,.07);
}

/* --------------------------------------------------------
   TABLEAU DE BORD DE CATÉGORISATION

   Une seule teinte de marque (--cat-serie) pour toutes les
   barres : la longueur code déjà la grandeur, et les classes
   d'un axe n'ont pas d'ordre naturel. Vérifiée contre la
   surface blanche des cartes (contraste >= 3:1).

   Le texte ne porte jamais la couleur des données : les
   libellés et les valeurs restent en encre neutre, la barre
   à côté d'eux suffit à les rattacher à la série.
-------------------------------------------------------- */

.cat-grille {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(320px, 1fr)
        );

    gap: 16px;

    margin-bottom: 40px;
}

.cat-carte {

    background: white;

    padding: 20px;

    border-radius: 10px;

    box-shadow:
        0 2px 8px
        rgba(0,0,0,.07);
}

.cat-entete {

    display: flex;

    align-items: baseline;

    justify-content: space-between;

    gap: 12px;
}

.cat-entete h3 {

    margin: 0;

    font-size: 15px;

    font-weight: 600;

    color: #0b0b0b;
}

.cat-couverture-valeur {

    font-size: 22px;

    font-weight: 700;

    color: #0b0b0b;
}

.cat-sous-titre {

    margin: 6px 0 16px;

    font-size: 12px;

    color: #898781;
}

/* Piste : un cran hors surface, jamais un trait autour de la
   barre — c'est le creux qui sépare, pas une bordure. */
.cat-piste {

    flex: 1;

    height: 14px;

    background: #f0efec;

    border-radius: 3px;

    overflow: hidden;
}

.cat-piste-couverture {

    height: 8px;

    margin-top: 10px;
}

.cat-barre {

    height: 100%;

    background: #2a78d6;

    border-radius: 0 4px 4px 0;

    min-width: 2px;
}

.cat-lignes {

    display: flex;

    flex-direction: column;

    /* > 2px : l'écart en couleur de surface est ce qui
       sépare deux barres voisines. */
    gap: 7px;
}

.cat-ligne {

    display: flex;

    align-items: center;

    gap: 10px;

    /* Cible de survol plus grande que la barre elle-même. */
    padding: 3px 4px;

    margin: -3px -4px;

    border-radius: 5px;
}

.cat-ligne:hover {

    background: #f7f9fc;
}

.cat-nom {

    flex: 0 0 132px;

    font-size: 12px;

    color: #52514e;

    overflow-wrap: anywhere;
}

.cat-valeur {

    flex: 0 0 46px;

    text-align: right;

    font-size: 12px;

    font-weight: 600;

    color: #0b0b0b;

    font-variant-numeric: tabular-nums;
}

.cat-vide {

    font-size: 12px;

    color: #898781;
}

@media (max-width: 520px) {

    .cat-nom {
        flex-basis: 96px;
    }
}

.stat-number {

    font-size: 27px;

    font-weight: 700;
}

.stat-label {

    margin-top: 4px;

    color: #666;

    font-size: 13px;
}


/* ========================================================
   TITLE VOCABULARY
======================================================== */

.title-vocabulary {

    margin:
        35px 0 40px;

    padding: 22px;

    background: white;

    border-radius: 10px;

    box-shadow:
        0 2px 8px
        rgba(0,0,0,.07);
}

.title-vocabulary h2 {

    margin:
        0 0 5px;
}

.vocabulary-description {

    margin:
        0 0 18px;

    color: #666;

    font-size: 14px;

    line-height: 1.5;
}

.word-cloud {

    display: flex;

    flex-wrap: wrap;

    gap: 8px;
}

.word-chip {

    display: inline-flex;

    align-items: center;

    gap: 7px;

    padding:
        7px 10px;

    border-radius: 7px;

    background: #f1f2f3;

    font-size: 14px;

    line-height: 1;

    transition:
        transform 0.15s ease,
        background 0.15s ease;
}

.word-chip:hover {

    transform:
        translateY(-1px);

    background: #e4e6e8;
}

.word {

    font-weight: 600;
}

.word-count {

    min-width: 20px;

    padding:
        3px 5px;

    border-radius: 4px;

    background: #d9dadd;

    color: #555;

    font-size: 11px;

    font-weight: 700;

    text-align: center;
}


/* ========================================================
   LEVELS
======================================================== */

.level-section {

    margin-top: 35px;
}

.level-section > h2 {

    margin-bottom: 15px;
}


/* ========================================================
   ARTICLE CARD
======================================================== */

.article-card {

    background: white;

    padding: 22px;

    margin:
        0 0 16px;

    border-radius: 10px;

    box-shadow:
        0 2px 8px
        rgba(0,0,0,.07);
}

.article-top {

    display: flex;

    justify-content:
        space-between;

    align-items: center;

    margin-bottom: 8px;
}

.badge {

    display: inline-block;

    padding:
        4px 8px;

    border-radius: 5px;

    font-size: 12px;

    font-weight: 700;
}

.badge-A {
    background: #ffdede;
}

.badge-B {
    background: #ffe8cc;
}

.badge-C {
    background: #dceaff;
}

.badge-D {
    background: #eeeeee;
}

.badge-E {
    background: #f7f7f7;
    color: #999999;
}

.badge-archival {
    background: #fff3c4;
    color: #7a5b00;
}

.score {

    font-size: 19px;
}

.source {

    font-size: 14px;

    font-weight: 700;

    color: #555;
}

.source-profile {

    display: inline-block;

    margin-left: 8px;

    padding:
        3px 7px;

    border-radius: 4px;

    background: #eeeeee;

    font-size: 11px;

    font-weight: 500;

    color: #666;
}

.article-card h3 {

    margin:
        7px 0;

    font-size: 20px;
}

.article-card h3 a {

    color: #202124;

    text-decoration: none;
}

.article-card h3 a:hover {

    text-decoration: underline;
}

.date {

    font-size: 14px;

    font-weight: 600;

    margin:
        8px 0;

    color: #444;
}

.relative-age {

    font-weight: 400;

    color: #888;
}

.theme {

    color: #666;

    font-size: 13px;

    margin-bottom: 10px;
}

.article-card p {

    color: #444;

    line-height: 1.5;
}

.reasons {

    padding: 10px;

    background: #f1f2f3;

    border-radius: 6px;

    font-size: 13px;

    line-height: 1.5;
}

.categorisation {

    margin-top: 8px;

    padding: 10px;

    background: #eef4fb;

    border-radius: 6px;

    font-size: 12px;

    line-height: 1.5;

    color: #444;
}

.categorisation-pertinence {

    margin-top: 4px;

    color: #666;
}


/* ========================================================
   AUDIT
======================================================== */

.audit {

    margin-top: 55px;
}

.audit-description {

    color: #666;

    margin-bottom: 15px;
}

.audit-group {

    margin-bottom: 35px;
}

.audit-group h3 {

    margin-bottom: 12px;

    font-size: 17px;
}

.audit-group-count {

    color: #888;

    font-size: 13px;

    font-weight: 500;

    margin-left: 6px;
}

.audit-wrapper {

    overflow-x: auto;

    background: white;

    border-radius: 10px;

    box-shadow:
        0 2px 8px
        rgba(0,0,0,.06);
}

table {

    width: 100%;

    border-collapse: collapse;
}

th,
td {

    padding: 10px;

    border-bottom:
        1px solid #ddd;

    text-align: left;

    vertical-align: top;

    font-size: 13px;
}

th {

    background: #eeeeee;

    position: sticky;

    top: 0;
}

td a {

    color: #202124;

    text-decoration: none;
}

td a:hover {

    text-decoration: underline;
}

.audit-categorisation {

    font-size: 12px;

    color: #555;

    max-width: 280px;
}

.audit-reason {

    display: block;

    font-size: 11px;

    color: #888;
}


/* ========================================================
   FOOTER
======================================================== */

footer {

    margin-top: 40px;

    padding-top: 20px;

    border-top:
        1px solid #ddd;

    color: #777;

    font-size: 13px;
}


/* ========================================================
   MOBILE
======================================================== */

@media (max-width: 700px) {

    body {
        padding: 16px;
    }

    .article-card {
        padding: 16px;
    }

    .article-card h3 {
        font-size: 18px;
    }

    .source-profile {
        display: block;
        width: fit-content;
        margin:
            6px 0 0;
    }

    .title-vocabulary {
        padding: 16px;
    }

    .word-chip {
        font-size: 13px;
    }

}

</style>
"""


# ============================================================
# CREATE WEB PAGE
# ============================================================

def create_web_page(
    articles,
    audit,
    stats,
    title_words=None,
    synthesis="",
    cat_stats=None,
):
    """
    Build the complete HTML page.

    The scanner supplies:
    - selected articles
    - complete audit
    - statistics
    - title vocabulary

    All HTML/CSS lives in this file.
    """

    if title_words is None:
        title_words = []

    now = datetime.now(
        timezone.utc
    )

    # --------------------------------------------------------
    # GROUP ARTICLES
    # --------------------------------------------------------

    grouped = {

        "A": [],

        "B": [],

        "C": [],

    }

    for article in articles:

        level = article.get(
            "level",
            "E",
        )

        if level in grouped:

            grouped[level].append(
                article
            )

    sections = []

    for level in (
        "A",
        "B",
        "C",
    ):

        sections.append(
            render_level_section(
                level,
                grouped[level],
            )
        )

    # --------------------------------------------------------
    # AUDIT — regroupé par catégorie de source (PROFILE_GROUP_ORDER)
    # pour rester lisible malgré la masse de niveau D.
    # --------------------------------------------------------

    audit_by_category: dict[str, list] = {}

    for article in audit:

        category = article.get(
            "category",
            "Autres",
        )

        audit_by_category.setdefault(
            category,
            [],
        ).append(
            article
        )

    category_order = list(PROFILE_GROUP_ORDER)

    for category in audit_by_category:

        if category not in category_order:

            category_order.append(
                category
            )

    audit_groups_html = []

    for category in category_order:

        articles_in_category = audit_by_category.get(
            category
        )

        if not articles_in_category:
            continue

        rows_html = "".join(
            render_audit_row(article)
            for article in articles_in_category
        )

        audit_groups_html.append(
            render_audit_group(
                category,
                rows_html,
                len(articles_in_category),
            )
        )

    # --------------------------------------------------------
    # VOCABULAIRE
    # --------------------------------------------------------

    vocabulary_html = render_title_vocabulary(
        title_words
    )

    # --------------------------------------------------------
    # FINAL HTML
    # --------------------------------------------------------

    return f"""<!DOCTYPE html>

<html lang="fr">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
Central Asia News Scanner
</title>

{render_css()}

</head>


<body>


<h1>
Central Asia News Scanner
</h1>


<div class="subtitle">

Actualités récentes d’Asie centrale et du Caucase :
droits humains, dissidence, politique intérieure,
sécurité et géopolitique majeure.

</div>


<div class="scan-date">

Dernier scan :

<strong>
{esc(
    now.strftime(
        "%d/%m/%Y à %H:%M UTC"
    )
)}
</strong>

</div>


<!-- ========================================================
     DASHBOARD
========================================================= -->

{render_dashboard(stats)}


<!-- ========================================================
     CATÉGORISATION
========================================================= -->

{render_categorisation_dashboard(cat_stats)}


<!-- ========================================================
     SYNTHÈSE
========================================================= -->

{render_synthesis(synthesis)}


<!-- ========================================================
     VOCABULAIRE DES TITRES
========================================================= -->

{vocabulary_html}


<!-- ========================================================
     ARTICLES
========================================================= -->

<h2>
Actualités prioritaires
</h2>


<p class="subtitle">

Classement :

<strong>
A → B → C
</strong>

puis meilleur score,
puis date la plus récente.

</p>


{"".join(sections)}


<!-- ========================================================
     AUDIT
========================================================= -->

<section class="audit">

<h2>
Audit complet
</h2>


<p class="audit-description">

Tous les articles analysés sont conservés ici, regroupés par
catégorie de source. Les articles filtrés restent visibles pour
permettre de contrôler les décisions du moteur.

</p>


{"".join(audit_groups_html)}

</section>


<footer>

Central Asia News Scanner ·
Moteur déterministe basé sur des règles et mots-clés

</footer>


</body>

</html>
"""
