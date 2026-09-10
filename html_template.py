# html_template.py

import html
from datetime import datetime, timezone

from sources import PROFILE_GROUP_ORDER


def esc(value):
    """Escape HTML safely."""
    return html.escape(str(value))


def format_date(date):
    """Format article date."""

    if not date:
        return "Date non disponible"

    return date.strftime(
        "%d/%m/%Y à %H:%M UTC"
    )


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
# ARTICLE CARD
# ============================================================

def render_article_card(
    article,
):
    """Render one selected article."""

    level = article.get(
        "level",
        "D",
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

    date = format_date(
        article.get("date")
    )

    reasons_text = " • ".join(
        reasons
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

        </div>

        <div class="source">

            {esc(source)}

            <span class="source-profile">
                {esc(source_label)}
            </span>

        </div>

        <h3>

            <a
                href="{esc(url)}"
                target="_blank"
                rel="noopener noreferrer"
            >
                {esc(title)}
            </a>

        </h3>

        <div class="date">

            📅 {esc(date)}

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
        "D",
    )

    retained = (
        "✓"
        if article.get(
            "relevant",
            False,
        )
        else "—"
    )

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
                href="{esc(
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
            "⚪ Niveau D"
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
            "D",
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
