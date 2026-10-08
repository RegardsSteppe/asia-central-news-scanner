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


# ============================================================
# IDENTITÉ VISUELLE
# ============================================================
#
# Logo « Étoile scannée » (maquette Design, variante C) : l'étoile à
# huit branches des ornements d'Asie centrale, traversée par la ligne
# de balayage du scanner. Deux encres selon le fond, plus une version
# favicon aux traits épaissis — à 16 px, les traits de 7 de la grande
# version disparaissent.

def render_logo(size=44, on_dark=False):
    """SVG du logo, encre adaptée au fond (clair ou sombre)."""

    ink = "#F4F2EC" if on_dark else "#14213D"
    core = "#3FB8C1" if on_dark else "#13808A"

    return f"""<svg class="logo" viewBox="0 0 120 120" width="{size}" height="{size}" aria-hidden="true">
<line x1="4" y1="60" x2="116" y2="60" stroke="#E0A526" stroke-width="5" stroke-linecap="round"/>
<rect x="28" y="28" width="64" height="64" fill="none" stroke="{ink}" stroke-width="7" stroke-linejoin="round"/>
<rect x="28" y="28" width="64" height="64" fill="none" stroke="{ink}" stroke-width="7" stroke-linejoin="round" transform="rotate(45 60 60)"/>
<circle cx="60" cy="60" r="15" fill="{core}"/>
</svg>"""


# Encodé à la main plutôt que via urllib : seuls "<", ">", "#" et '"'
# posent problème dans un data: URI entre guillemets simples.
FAVICON_HREF = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120'%3E"
    "%3Crect width='120' height='120' rx='26' fill='%2314213D'/%3E"
    "%3Crect x='30' y='30' width='60' height='60' fill='none' stroke='%23F4F2EC' "
    "stroke-width='12' stroke-linejoin='round'/%3E"
    "%3Crect x='30' y='30' width='60' height='60' fill='none' stroke='%23F4F2EC' "
    "stroke-width='12' stroke-linejoin='round' transform='rotate(45 60 60)'/%3E"
    "%3Ccircle cx='60' cy='60' r='15' fill='%233FB8C1'/%3E"
    "%3C/svg%3E"
)

REPO_URL = "https://github.com/RegardsSteppe/asia-central-news-scanner"

# Couleurs de niveau : contraste >= 4.5:1 sous texte blanc (pastille
# A/B/C), et distinctes en luminance, pas seulement en teinte.
LEVEL_COLORS = {
    "A": "#B42318",
    "B": "#A04A06",
    "C": "#1D5BA3",
}

LEVEL_TITLES = {
    "A": "Droits humains / répression",
    "B": "Politique intérieure",
    "C": "Géopolitique majeure",
}


def render_stat(
    number,
    label,
):
    """Render one dashboard statistic."""

    return f"""
    <div class="stat">
        <div class="stat-number">{esc(number)}</div>
        <div class="stat-label">{esc(label)}</div>
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
    "haut_karabakh": "Haut-Karabakh",
    "abkhazie": "Abkhazie",
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

# Valeurs qui ne décrivent rien : affichées en étiquette, elles
# feraient croire à une information là où il n'y en a pas.
_ETIQUETTES_MUETTES = {"aucun", "indetermine", "autre"}


def _categorisation_tags(article):
    """(clés géo, libellés d'étiquettes) tirés de la catégorisation."""

    cat = article.get("categorisation") or {}

    geo = [g for g in (cat.get("geo") or []) if g not in _ETIQUETTES_MUETTES]
    autres = [
        v
        for axe in ("acteur", "traitement")
        for v in (cat.get(axe) or [])
        if v not in _ETIQUETTES_MUETTES
    ]

    return geo, [_libelle_classe(v) for v in geo + autres]


def render_article_card(
    article,
):
    """Render one selected article."""

    level = article.get("level", "E")
    score = article.get("score", 0)
    source = article.get("source", "")
    source_label = article.get("source_label", "")
    title = article.get("title", "")
    url = article.get("url", "")
    summary = article.get("summary", "")
    theme = article.get("theme", "")
    reasons = article.get("reasons", [])

    raw_date = article.get("date")
    date = format_date(raw_date)
    relative_age = format_relative_age(raw_date)
    age_days = article_age_days(raw_date)
    is_archival = age_days is not None and age_days >= ARCHIVAL_AGE_DAYS

    reasons_text = " • ".join(reasons)

    archival_badge = (
        '<span class="badge badge-archival" '
        'title="Article ancien republié récemment">republié</span>'
        if is_archival
        else ""
    )

    geo_keys, tags = _categorisation_tags(article)
    tags_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)

    categorisation_summary = _categorisation_summary(article)
    categorisation_icon, categorisation_reason = _categorisation_pertinence(article)
    categorisation_block = (
        f"""
        <div class="categorisation">
            <strong>Catégorisation (indépendante du score) :</strong>
            {esc(categorisation_summary)}
            {f'<div class="categorisation-pertinence">{esc(categorisation_icon)} {esc(categorisation_reason)}</div>' if categorisation_icon else ""}
        </div>
        """
        if categorisation_summary
        else ""
    )

    return f"""
    <article class="article-card" data-level="{esc(level)}" data-geo="{esc(' '.join(geo_keys))}">

        <div class="article-top">
            <span class="badge badge-{esc(level)}">{esc(level)}</span>
            <strong class="score">{esc(score)}/100</strong>
            {archival_badge}
            <span class="article-sep" aria-hidden="true"></span>
            <span class="source">{esc(source)}</span>
            <span class="source-profile">{esc(source_label)}</span>
        </div>

        <h3>
            <a href="{safe_url(url)}" target="_blank" rel="noopener noreferrer">{esc(title)}</a>
        </h3>

        <div class="article-meta">
            <span class="date">{esc(date)}{f' <span class="relative-age">({esc(relative_age)})</span>' if relative_age else ""}</span>
            {tags_html}
        </div>

        {f'<p class="summary">{esc(summary[:900])}</p>' if summary else ""}

        <details class="why">
            <summary>Pourquoi cet article ?</summary>
            <div class="theme">{esc(theme)}</div>
            <div class="reasons">{esc(reasons_text)}</div>
            {categorisation_block}
        </details>

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

    cards = "".join(render_article_card(article) for article in articles)

    return f"""
    <section class="level-section" data-level="{esc(level)}">

        <h2>
            <span class="badge badge-{esc(level)}">{esc(level)}</span>
            {esc(LEVEL_TITLES[level])}
            <span class="level-count">{len(articles)}</span>
        </h2>

        {cards}

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
    <section class="panel synthesis">

        <h2>Synthèse du jour</h2>

        <p class="synthesis-text">{esc(synthesis)}</p>

        <p class="synthesis-note">
            Générée automatiquement à partir des articles de niveau A —
            à vérifier avant citation.
        </p>

    </section>
    """


def _fmt_int(value):
    """16134 → "16 134" (espace fine insécable, usage français)."""

    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def render_hero_stats(stats):
    """Les quatre chiffres du bandeau : retenus, A, sources, répartition A/B/C."""

    a = stats.get("level_a", 0)
    b = stats.get("level_b", 0)
    c = stats.get("level_c", 0)
    abc = a + b + c

    def part(n):
        return f"{(100 * n / abc) if abc else 0:.1f}%"

    return f"""
    <div class="hero-stats">

        <div class="hero-stat">
            <div class="hero-number">{esc(_fmt_int(stats.get("retained", 0)))}</div>
            <div class="hero-label">articles retenus sur {esc(_fmt_int(stats.get("analyzed", 0)))} analysés</div>
        </div>

        <div class="hero-stat">
            <div class="hero-number hero-number-a">{esc(a)}</div>
            <div class="hero-label">niveau A — droits humains / répression</div>
        </div>

        <div class="hero-stat">
            <div class="hero-number">{esc(stats.get("sources_successful", 0))}<span class="hero-sub">/{esc(stats.get("sources_total", 0))}</span></div>
            <div class="hero-label">sources lues au dernier scan</div>
        </div>

        <div class="hero-stat">
            <div class="hero-bar" role="img" aria-label="Répartition : A {a}, B {b}, C {c}">
                <div class="hero-bar-a" style="width: {part(a)}"></div>
                <div class="hero-bar-b" style="width: {part(b)}"></div>
                <div class="hero-bar-c" style="width: {part(c)}"></div>
            </div>
            <div class="hero-legend">
                <span>A {esc(a)}</span><span>B {esc(b)}</span><span>C {esc(c)}</span>
            </div>
        </div>

    </div>
    """


def render_dashboard(
    stats,
):
    """Détail complet du scan, sous le bandeau qui n'en montre que quatre."""

    return f"""
    <div class="dashboard">
        {render_stat(_fmt_int(stats["analyzed"]), "Articles analysés")}
        {render_stat(stats["retained"], "Articles retenus")}
        {render_stat(f'{stats["avg_score"]}/100', "Score moyen")}
        {render_stat(stats["level_a"], "Niveau A")}
        {render_stat(stats["level_b"], "Niveau B")}
        {render_stat(stats["level_c"], "Niveau C")}
        {render_stat(stats["level_d"], "Niveau D — activistes hors région")}
        {render_stat(stats["level_e"], "Niveau E — bruit")}
        {render_stat(stats.get("level_f", 0), "Niveau F — pages de rubrique")}
        {render_stat(f'{stats["sources_successful"]}/{stats["sources_total"]}', "Sources analysées")}
        {render_stat(f'{stats["relevance_rate"]}%', "Taux de pertinence")}
    </div>
    """


def _axe(cat_stats, cle):
    if not cat_stats:
        return None
    return next((a for a in cat_stats.get("axes", []) if a.get("cle") == cle), None)


def render_aside_bars(cat_stats, cle, titre, limite, barre_sombre=False):
    """Encart latéral : les premières classes d'un axe, en barres."""

    axe = _axe(cat_stats, cle)
    if not axe or not axe["classes"]:
        return ""

    classes = [c for c in axe["classes"] if c["nom"] not in _ETIQUETTES_MUETTES][:limite]
    if not classes:
        return ""

    maximum = classes[0]["effectif"]
    classe_barre = "mini-barre mini-barre-sombre" if barre_sombre else "mini-barre"

    lignes = "".join(
        f"""
        <div class="mini-ligne">
            <span>{esc(_libelle_classe(c["nom"]))}</span>
            <span class="mini-piste"><span class="{classe_barre}" style="width: {100 * c["effectif"] / maximum:.1f}%"></span></span>
            <span class="mini-valeur">{esc(_fmt_int(c["effectif"]))}</span>
        </div>
        """
        for c in classes
    )

    return f"""
    <section class="panel">
        <div class="panel-head">
            <h2>{esc(titre)}</h2>
            <span class="panel-meta">CORPUS · {esc(_fmt_int(cat_stats["total"]))}</span>
        </div>
        {lignes}
    </section>
    """


def render_sources_panel(articles, stats, limite=9):
    """Sources les plus présentes parmi les articles retenus."""

    compte: dict[str, int] = {}
    for article in articles:
        nom = article.get("source")
        if nom:
            compte[nom] = compte.get(nom, 0) + 1

    noms = sorted(compte, key=lambda n: (-compte[n], n))[:limite]
    if not noms:
        return ""

    return f"""
    <section id="sources" class="panel panel-dashed">
        <h2>Sources</h2>
        <p>{esc(", ".join(noms))}… <a href="#audit">Voir les {esc(stats.get("sources_total", 0))} sources</a></p>
    </section>
    """


def render_filters(articles, stats, limite_pays=8):
    """
    Barre de filtres (niveau, pays, recherche). Cachée sans JavaScript :
    sans lui, les boutons ne feraient rien et la page montre déjà tout.
    """

    compte: dict[str, int] = {}
    for article in articles:
        for g in _categorisation_tags(article)[0]:
            compte[g] = compte.get(g, 0) + 1

    pays = sorted(compte, key=lambda g: (-compte[g], g))[:limite_pays]

    niveaux = [("all", f"Tous · {len(articles)}")] + [
        (lvl, f"{lvl} · {LEVEL_TITLES[lvl].split(' / ')[0]} · {stats.get('level_' + lvl.lower(), 0)}")
        for lvl in ("A", "B", "C")
    ]

    boutons_niveau = "".join(
        f'<button type="button" class="chip" data-filter-level="{esc(v)}" '
        f'aria-pressed="{"true" if v == "all" else "false"}">{esc(libelle)}</button>'
        for v, libelle in niveaux
    )

    boutons_pays = "".join(
        f'<button type="button" class="chip chip-geo" data-filter-geo="{esc(g)}" '
        f'aria-pressed="false">{esc(_libelle_classe(g))}</button>'
        for g in pays
    )

    return f"""
    <div class="filters" hidden>
        <div class="search">
            <label for="q">Rechercher</label>
            <input id="q" type="search" placeholder="Nom, ville, organisation…" autocomplete="off">
        </div>
        <div role="group" aria-label="Filtrer par niveau" class="chips">{boutons_niveau}</div>
        {f'<div role="group" aria-label="Filtrer par pays" class="chips">{boutons_pays}</div>' if boutons_pays else ""}
        <p class="filters-empty" hidden>Aucun article ne correspond à ces filtres.</p>
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

FONTS_HREF = (
    "https://fonts.googleapis.com/css2?"
    "family=Space+Grotesk:wght@400;500;700"
    "&family=IBM+Plex+Mono:wght@400;500"
    "&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600"
    "&display=swap"
)


def render_css():
    """Return all website CSS."""

    return """
<style>

:root {
    --ink: #14213D;
    --ink-2: #1E2F52;
    --ink-line: #2C3D63;
    --paper: #F4F2EC;
    --card: #FFFFFF;
    --line: #DAD6CC;
    --line-soft: #ECE8DF;
    --line-strong: #C9C3B6;
    --muted: #5A6378;
    --muted-dark: #A9B4C8;
    --on-dark: #C9D1E0;
    --teal: #13808A;
    --teal-ink: #0F6A72;
    --teal-light: #3FB8C1;
    --gold: #E0A526;
    --level-a: #B42318;
    --level-b: #A04A06;
    --level-c: #1D5BA3;
    --sans: "Space Grotesk", system-ui, sans-serif;
    --mono: "IBM Plex Mono", ui-monospace, monospace;
    --serif: "Source Serif 4", Georgia, serif;
    --gutter: clamp(16px, 4vw, 40px);
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font-family: var(--sans);
}

a {
    color: var(--ink);
}

a:hover {
    color: var(--teal-ink);
}

.wrap {
    max-width: 1240px;
    margin: 0 auto;
    padding-left: var(--gutter);
    padding-right: var(--gutter);
}

.subtitle {
    color: var(--muted);
    line-height: 1.5;
}


/* ========================================================
   EN-TÊTE
======================================================== */

.site-header {
    border-bottom: 1px solid var(--line);
}

.site-header .wrap {
    padding-top: 18px;
    padding-bottom: 18px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 16px 32px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 14px;
    text-decoration: none;
    color: var(--ink);
}

.brand-name {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.brand-name strong {
    font-size: 20px;
    line-height: 1;
}

.brand-name span {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: 0.3em;
}

.site-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 28px;
    font-size: 15px;
    font-weight: 500;
}

.site-nav a {
    text-decoration: none;
    padding: 10px 0;
    border-bottom: 2px solid transparent;
}

.site-nav a:first-child {
    border-bottom-color: var(--ink);
}

.scan-date {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    border-radius: 999px;
    background: var(--card);
    border: 1px solid var(--line);
    font-family: var(--mono);
    font-size: 12px;
}

.scan-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--teal);
}


/* ========================================================
   BANDEAU
======================================================== */

.hero {
    background: var(--ink);
    color: var(--paper);
}

.hero .wrap {
    padding-top: clamp(40px, 6vw, 72px);
    padding-bottom: clamp(40px, 6vw, 72px);
    display: flex;
    flex-direction: column;
    gap: 40px;
}

.hero-text {
    display: flex;
    flex-direction: column;
    gap: 16px;
    max-width: 760px;
}

.eyebrow {
    font-family: var(--mono);
    font-size: 12px;
    letter-spacing: 0.16em;
    color: var(--gold);
}

.hero h1 {
    margin: 0;
    font-size: clamp(32px, 4.6vw, 56px);
    line-height: 1.05;
    letter-spacing: -0.02em;
}

.hero-lede {
    margin: 0;
    font-family: var(--serif);
    font-size: 19px;
    line-height: 1.5;
    color: var(--on-dark);
}

.hero-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 1px;
    background: var(--ink-line);
    border: 1px solid var(--ink-line);
    border-radius: 14px;
    overflow: hidden;
}

.hero-stat {
    background: var(--ink);
    padding: 22px 24px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.hero-number {
    font-size: 36px;
    font-weight: 700;
    letter-spacing: -0.02em;
}

.hero-number-a {
    color: #FF8A7A;
}

.hero-sub {
    font-size: 20px;
    color: var(--muted-dark);
}

.hero-label {
    font-size: 14px;
    color: var(--muted-dark);
}

.hero-bar {
    display: flex;
    height: 10px;
    margin-top: 12px;
    border-radius: 5px;
    overflow: hidden;
    gap: 2px;
}

.hero-bar-a { background: #E5533F; }
.hero-bar-b { background: var(--gold); }
.hero-bar-c { background: var(--teal-light); }

.hero-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 14px;
    margin-top: 4px;
    font-family: var(--mono);
    font-size: 12px;
    color: var(--on-dark);
}


/* ========================================================
   COLONNES
======================================================== */

.veille {
    padding-top: 40px;
    padding-bottom: 64px;
    display: flex;
    flex-wrap: wrap;
    gap: 40px;
    align-items: flex-start;
}

.veille-main {
    flex: 999 1 560px;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.veille-aside {
    flex: 1 1 320px;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.veille-main > h2,
.block-title {
    margin: 0;
    font-size: 28px;
    letter-spacing: -0.01em;
}

.ranking-note {
    margin: -8px 0 0;
    font-size: 14px;
    color: var(--muted);
}


/* ========================================================
   FILTRES
======================================================== */

.filters {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.filters[hidden],
.filters-empty[hidden],
.article-card[hidden],
.level-section[hidden] {
    display: none;
}

.search {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-width: 360px;
}

.search label {
    font-size: 13px;
    color: var(--muted);
}

.search input {
    height: 44px;
    padding: 0 14px;
    border: 1px solid var(--line-strong);
    border-radius: 10px;
    background: var(--card);
    font: inherit;
    font-size: 15px;
    color: var(--ink);
}

.chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.chip {
    min-height: 44px;
    padding: 0 18px;
    border-radius: 999px;
    border: 1px solid var(--line-strong);
    background: var(--card);
    color: var(--ink);
    font: inherit;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
}

.chip[aria-pressed="true"] {
    border-color: var(--ink);
    background: var(--ink);
    color: var(--paper);
}

.chip-geo {
    min-height: 36px;
    padding: 0 12px;
    border-radius: 8px;
    border-style: dashed;
    background: transparent;
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 400;
}

.chip-geo[aria-pressed="true"] {
    border-style: solid;
}

.filters-empty {
    margin: 0;
    color: var(--muted);
}


/* ========================================================
   NIVEAUX ET CARTES
======================================================== */

.level-section {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.level-section > h2 {
    margin: 12px 0 0;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 20px;
}

.level-count {
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 400;
    color: var(--muted);
}

.article-card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.article-top {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 14px;
}

.badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 30px;
    height: 30px;
    padding: 0 8px;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 700;
    color: #FFFFFF;
    background: #6B7280;
}

.badge-A { background: var(--level-a); }
.badge-B { background: var(--level-b); }
.badge-C { background: var(--level-c); }
.badge-D { background: #5A6378; }
.badge-E,
.badge-F { background: #ECE8DF; color: #5A6378; }

.badge-archival {
    height: 24px;
    font-size: 12px;
    font-weight: 500;
    background: #FBF3DF;
    color: #6B4A00;
}

.score {
    font-family: var(--mono);
    font-size: 14px;
    font-weight: 500;
}

.article-sep {
    width: 1px;
    height: 18px;
    background: var(--line);
}

.source {
    font-size: 14px;
    font-weight: 500;
}

.source-profile {
    font-size: 13px;
    color: var(--muted);
}

.article-card h3 {
    margin: 0;
    font-family: var(--serif);
    font-size: 22px;
    line-height: 1.3;
    font-weight: 600;
}

.article-card h3 a {
    text-decoration: none;
}

.article-card h3 a:hover {
    text-decoration: underline;
}

.article-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
}

.date {
    margin-right: 6px;
    font-family: var(--mono);
    font-size: 12px;
    color: var(--muted);
}

.tag {
    padding: 4px 10px;
    border-radius: 6px;
    background: #EEF3F4;
    color: #0F5A61;
    font-size: 13px;
}

.summary {
    margin: 0;
    font-family: var(--serif);
    font-size: 16px;
    line-height: 1.55;
    color: #333B4F;
}

.why {
    border-top: 1px solid var(--line-soft);
    padding-top: 12px;
}

.why summary {
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    color: var(--teal-ink);
    min-height: 24px;
}

.theme {
    margin-top: 10px;
    font-size: 13px;
    font-weight: 500;
}

.reasons,
.categorisation {
    margin-top: 8px;
    font-family: var(--mono);
    font-size: 12px;
    line-height: 1.6;
    color: var(--muted);
}

.categorisation strong {
    font-family: var(--sans);
    font-weight: 500;
    color: var(--ink);
}

.categorisation-pertinence {
    margin-top: 4px;
}


/* ========================================================
   ENCARTS LATÉRAUX
======================================================== */

.panel {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.panel h2 {
    margin: 0;
    font-size: 18px;
}

.panel-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
}

.panel-meta {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--muted);
}

.panel-dashed {
    background: transparent;
    border-style: dashed;
    border-color: #B9B2A3;
    padding: 20px 24px;
}

.panel-dashed h2 {
    font-size: 15px;
}

.panel-dashed p {
    margin: 0;
    font-size: 14px;
    line-height: 1.5;
    color: #4A5368;
}

.synthesis-text {
    margin: 0;
    font-family: var(--serif);
    font-size: 16px;
    line-height: 1.6;
    white-space: pre-wrap;
}

.synthesis-note {
    margin: 0;
    padding: 10px 12px;
    border-radius: 8px;
    background: #FBF3DF;
    font-size: 13px;
    line-height: 1.4;
    color: #6B4A00;
}

.mini-ligne {
    display: grid;
    grid-template-columns: 130px minmax(0, 1fr) 52px;
    align-items: center;
    gap: 10px;
    font-size: 13px;
}

.mini-piste {
    height: 8px;
    border-radius: 4px;
    background: var(--line-soft);
    overflow: hidden;
}

.mini-barre {
    display: block;
    height: 100%;
    border-radius: 4px;
    background: var(--teal);
    min-width: 2px;
}

.mini-barre-sombre {
    background: var(--ink);
}

.mini-valeur {
    font-family: var(--mono);
    font-size: 12px;
    text-align: right;
    color: var(--muted);
}


/* ========================================================
   CORPUS : DÉTAIL DU SCAN ET CATÉGORISATION
======================================================== */

.corpus {
    padding-top: 48px;
    padding-bottom: 48px;
    border-top: 1px solid var(--line);
}

.corpus h2 {
    font-size: 24px;
    letter-spacing: -0.01em;
}

.dashboard {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
    margin: 20px 0 40px;
}

.stat {
    background: var(--card);
    border: 1px solid var(--line);
    padding: 16px 18px;
    border-radius: 12px;
}

.stat-number {
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -0.01em;
}

.stat-label {
    margin-top: 4px;
    color: var(--muted);
    font-size: 13px;
}

/* --------------------------------------------------------
   TABLEAU DE BORD DE CATÉGORISATION

   Une seule teinte (--teal) pour toutes les barres : la
   longueur code déjà la grandeur, et les classes d'un axe
   n'ont pas d'ordre naturel. Contraste >= 3:1 sur blanc.

   Le texte ne porte jamais la couleur des données : les
   libellés et les valeurs restent en encre neutre, la barre
   à côté d'eux suffit à les rattacher à la série.
-------------------------------------------------------- */

.cat-grille {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 16px;
    margin-bottom: 40px;
}

.cat-carte {
    background: var(--card);
    border: 1px solid var(--line);
    padding: 20px;
    border-radius: 14px;
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
}

.cat-couverture-valeur {
    font-size: 22px;
    font-weight: 700;
}

.cat-sous-titre {
    margin: 6px 0 16px;
    font-size: 12px;
    color: var(--muted);
}

/* Piste : un cran hors surface, jamais un trait autour de la
   barre — c'est le creux qui sépare, pas une bordure. */
.cat-piste {
    flex: 1;
    height: 14px;
    background: var(--line-soft);
    border-radius: 3px;
    overflow: hidden;
}

.cat-piste-couverture {
    height: 8px;
    margin-top: 10px;
}

.cat-barre {
    height: 100%;
    background: var(--teal);
    border-radius: 0 4px 4px 0;
    min-width: 2px;
}

.cat-barre-couverture {
    background: var(--ink);
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
    background: #F7F5F0;
}

.cat-nom {
    flex: 0 0 132px;
    font-size: 12px;
    color: #4A5368;
    overflow-wrap: anywhere;
}

.cat-valeur {
    flex: 0 0 46px;
    text-align: right;
    font-family: var(--mono);
    font-size: 12px;
    font-variant-numeric: tabular-nums;
}

.cat-vide {
    font-size: 12px;
    color: var(--muted);
}


/* ========================================================
   TITLE VOCABULARY
======================================================== */

.title-vocabulary {
    margin: 0 0 40px;
    padding: 24px;
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
}

.title-vocabulary h2 {
    margin: 0 0 5px;
}

.vocabulary-description {
    margin: 0 0 18px;
    color: var(--muted);
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
    padding: 7px 10px;
    border-radius: 7px;
    background: #F1EFE9;
    font-size: 14px;
    line-height: 1;
}

.word {
    font-weight: 500;
}

.word-count {
    min-width: 20px;
    padding: 3px 5px;
    border-radius: 4px;
    background: var(--line);
    color: #4A5368;
    font-family: var(--mono);
    font-size: 11px;
    text-align: center;
}


/* ========================================================
   AUDIT
======================================================== */

.audit {
    padding-top: 48px;
    padding-bottom: 64px;
    border-top: 1px solid var(--line);
}

.audit h2 {
    font-size: 24px;
}

.audit-description {
    color: var(--muted);
    margin-bottom: 15px;
    line-height: 1.5;
}

.audit-group {
    margin-bottom: 35px;
}

.audit-group h3 {
    margin-bottom: 12px;
    font-size: 17px;
}

.audit-group-count {
    color: var(--muted);
    font-size: 13px;
    font-weight: 400;
    margin-left: 6px;
}

.audit-wrapper {
    overflow-x: auto;
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    padding: 10px;
    border-bottom: 1px solid var(--line-soft);
    text-align: left;
    vertical-align: top;
    font-size: 13px;
}

th {
    background: #F1EFE9;
    position: sticky;
    top: 0;
    font-weight: 500;
}

td .badge {
    min-width: 24px;
    height: 24px;
    font-size: 12px;
    padding: 0 6px;
}

td a {
    text-decoration: none;
}

td a:hover {
    text-decoration: underline;
}

.audit-categorisation {
    font-size: 12px;
    color: #4A5368;
    max-width: 280px;
}

.audit-reason {
    display: block;
    font-size: 11px;
    color: var(--muted);
}


/* ========================================================
   PIED DE PAGE
======================================================== */

.site-footer {
    background: var(--ink);
    color: var(--on-dark);
}

.site-footer .wrap {
    padding-top: 40px;
    padding-bottom: 40px;
    display: flex;
    flex-wrap: wrap;
    gap: 24px 48px;
    justify-content: space-between;
    align-items: flex-start;
    font-size: 14px;
    line-height: 1.6;
}

.footer-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--paper);
    font-weight: 700;
}

.site-footer p {
    margin: 0;
    max-width: 520px;
}

.footer-links {
    display: flex;
    gap: 20px;
}

.site-footer a {
    color: var(--paper);
}


/* ========================================================
   MOBILE
======================================================== */

@media (max-width: 700px) {

    .site-nav {
        gap: 4px 18px;
        font-size: 14px;
    }

    .article-card,
    .panel {
        padding: 18px;
    }

    .article-card h3 {
        font-size: 19px;
    }

    .title-vocabulary {
        padding: 16px;
    }

    .word-chip {
        font-size: 13px;
    }

    .mini-ligne {
        grid-template-columns: 100px minmax(0, 1fr) 48px;
    }

    .cat-grille {
        grid-template-columns: minmax(0, 1fr);
    }

    .cat-nom {
        flex-basis: 96px;
    }
}

</style>
"""


# Filtres côté navigateur : niveau, pays (clés de catégorisation
# portées par data-geo) et texte libre sur le contenu de la carte.
# Une section de niveau sans carte visible est masquée avec elle.
FILTER_SCRIPT = """
<script>
(function () {
    var bar = document.querySelector(".filters");
    if (!bar) return;
    bar.hidden = false;

    var cards = Array.prototype.slice.call(document.querySelectorAll(".article-card[data-level]"));
    var sections = document.querySelectorAll(".level-section");
    var empty = bar.querySelector(".filters-empty");
    var input = document.getElementById("q");
    var state = { level: "all", geo: "", q: "" };

    cards.forEach(function (c) { c._text = c.textContent.toLowerCase(); });

    function apply() {
        var shown = 0;
        cards.forEach(function (c) {
            var ok = (state.level === "all" || c.dataset.level === state.level)
                && (!state.geo || (" " + c.dataset.geo + " ").indexOf(" " + state.geo + " ") !== -1)
                && (!state.q || c._text.indexOf(state.q) !== -1);
            c.hidden = !ok;
            if (ok) shown++;
        });
        Array.prototype.forEach.call(sections, function (s) {
            s.hidden = !s.querySelector(".article-card:not([hidden])");
        });
        empty.hidden = shown !== 0;
    }

    function press(selector, button) {
        Array.prototype.forEach.call(bar.querySelectorAll(selector), function (b) {
            b.setAttribute("aria-pressed", b === button ? "true" : "false");
        });
    }

    bar.addEventListener("click", function (e) {
        var b = e.target.closest("button");
        if (!b) return;
        if (b.dataset.filterLevel) {
            state.level = b.dataset.filterLevel;
            press("[data-filter-level]", b);
        } else if (b.dataset.filterGeo) {
            var same = state.geo === b.dataset.filterGeo;
            state.geo = same ? "" : b.dataset.filterGeo;
            press("[data-filter-geo]", same ? null : b);
        }
        apply();
    });

    input.addEventListener("input", function () {
        state.q = input.value.trim().toLowerCase();
        apply();
    });
})();
</script>
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

    grouped = {"A": [], "B": [], "C": []}

    for article in articles:
        level = article.get("level", "E")
        if level in grouped:
            grouped[level].append(article)

    sections = "".join(
        render_level_section(level, grouped[level])
        for level in ("A", "B", "C")
    )

    shown_articles = grouped["A"] + grouped["B"] + grouped["C"]

    # --------------------------------------------------------
    # AUDIT — regroupé par catégorie de source (PROFILE_GROUP_ORDER)
    # pour rester lisible malgré la masse de niveau D.
    # --------------------------------------------------------

    audit_by_category: dict[str, list] = {}

    for article in audit:
        category = article.get("category", "Autres")
        audit_by_category.setdefault(category, []).append(article)

    category_order = list(PROFILE_GROUP_ORDER)

    for category in audit_by_category:
        if category not in category_order:
            category_order.append(category)

    audit_groups_html = []

    for category in category_order:
        articles_in_category = audit_by_category.get(category)

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

    vocabulary_html = render_title_vocabulary(title_words)

    scan_date = now.strftime("%d/%m/%Y %H:%M UTC")

    # --------------------------------------------------------
    # FINAL HTML
    # --------------------------------------------------------

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Central Asia News Scanner</title>
<meta name="description" content="Veille quotidienne Asie centrale et Caucase : droits humains, dissidence et répression.">
<meta name="theme-color" content="#14213D">
<link rel="icon" type="image/svg+xml" href="{FAVICON_HREF}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{esc(FONTS_HREF)}">
{render_css()}
</head>

<body>

<header class="site-header">
<div class="wrap">

    <a class="brand" href="#">
        {render_logo(44)}
        <span class="brand-name">
            <strong>Central Asia</strong>
            <span>NEWS SCANNER</span>
        </span>
    </a>

    <nav class="site-nav" aria-label="Navigation principale">
        <a href="#veille">Veille</a>
        <a href="#corpus">Corpus</a>
        <a href="#sources">Sources</a>
        <a href="#audit">Audit</a>
        <a href="#methode">Méthode</a>
    </nav>

    <div class="scan-date">
        <span class="scan-dot" aria-hidden="true"></span>
        Dernier scan · {esc(scan_date)}
    </div>

</div>
</header>


<section class="hero">
<div class="wrap">

    <div class="hero-text">
        <div class="eyebrow">VEILLE QUOTIDIENNE · ASIE CENTRALE &amp; CAUCASE</div>
        <h1>Droits humains, dissidence et répression, filtrés chaque jour.</h1>
        <p class="hero-lede">
            Des milliers d’articles en anglais, russe et français, triés par
            un moteur de règles transparent : chaque article retenu dit pourquoi.
        </p>
    </div>

    {render_hero_stats(stats)}

</div>
</section>


<main id="veille" class="wrap veille">

    <div class="veille-main">

        <h2>Actualités prioritaires</h2>

        <p class="ranking-note">
            Classement : <strong>A → B → C</strong>, puis meilleur score,
            puis date la plus récente.
        </p>

        {render_filters(shown_articles, stats)}

        {sections}

    </div>

    <aside class="veille-aside">
        {render_synthesis(synthesis)}
        {render_aside_bars(cat_stats, "geo", "Pays mentionnés", 8)}
        {render_aside_bars(cat_stats, "traitement", "Traitement subi", 5, barre_sombre=True)}
        {render_sources_panel(shown_articles, stats)}
    </aside>

</main>


<section id="corpus" class="wrap corpus">

    <h2>Détail du scan</h2>

    {render_dashboard(stats)}

    {render_categorisation_dashboard(cat_stats)}

    {vocabulary_html}

</section>


<section id="audit" class="wrap audit">

    <h2>Audit complet</h2>

    <p class="audit-description">
        Tous les articles analysés sont conservés ici, regroupés par
        catégorie de source. Les articles filtrés restent visibles pour
        permettre de contrôler les décisions du moteur.
    </p>

    {"".join(audit_groups_html)}

</section>


<footer id="methode" class="site-footer">
<div class="wrap">

    <div class="footer-brand">
        {render_logo(36, on_dark=True)}
        Central Asia News Scanner
    </div>

    <p>
        Filtrage par règles et mots-clés, sans IA au premier niveau.
        Le score mesure la pertinence pour la veille, pas la gravité des faits.
    </p>

    <div class="footer-links">
        <a href="{REPO_URL}/blob/main/docs/SPEC.md">Méthode</a>
        <a href="{REPO_URL}">GitHub</a>
    </div>

</div>
</footer>

{FILTER_SCRIPT}

</body>
</html>
"""
