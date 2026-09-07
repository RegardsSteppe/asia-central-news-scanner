# news_scanner.py

import html
import logging
import re
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

from sources import SOURCES
from keywords import (
    CENTRAL_ASIA_TERMS,
    CRITICAL_HR_TERMS,
    STRONG_HR_TERMS,
    DOMESTIC_POLITICAL_TERMS,
    MAJOR_REGIONAL_EVENTS,
    ROUTINE_GEO_TERMS,
    REGIONAL_ACTORS,
    NON_NEWS_TERMS,
    BUSINESS_SPORTS_TECH_TERMS,
)


# ============================================================
# CONFIGURATION
# ============================================================

REQUEST_TIMEOUT = 20

MAX_ARTICLES_PER_SOURCE = 100

ARTICLES_TO_DISPLAY = 10

ARTICLE_PAGE_FETCH_LIMIT = 50

MIN_RELEVANCE_SCORE = 10

USER_AGENT = (
    "Mozilla/5.0 (compatible; "
    "AsiaCentralNewsScanner/3.3; "
    "+https://github.com/RegardsSteppe/asia-central-news-scanner)"
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# HTTP
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8,ru;q=0.7",
})


def fetch_url(url):
    try:
        response = SESSION.get(
            url,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response

    except requests.RequestException as exc:
        logger.warning(
            "Failed to fetch %s: %s",
            url,
            exc,
        )

        return None


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text):
    if not text:
        return ""

    text = html.unescape(text)

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def phrase_present(text, phrase):
    """
    Recherche relativement robuste d'une expression.
    """

    if not text or not phrase:
        return False

    pattern = r"(?<!\w)" + re.escape(
        phrase.lower()
    ) + r"(?!\w)"

    return re.search(
        pattern,
        text.lower(),
    ) is not None


def find_terms(text, terms):
    found = []

    for term in terms:
        if phrase_present(text, term):
            found.append(term)

    return found


# ============================================================
# DATE
# ============================================================

def parse_date(entry):
    for key in (
        "published_parsed",
        "updated_parsed",
        "created_parsed",
    ):
        value = entry.get(key)

        if value:
            try:
                return datetime(
                    *value[:6],
                    tzinfo=timezone.utc,
                )
            except Exception:
                pass

    for key in (
        "published",
        "updated",
        "created",
    ):
        value = entry.get(key)

        if value:
            try:
                parsed = feedparser._parse_date(
                    value
                )

                if parsed:
                    return datetime(
                        *parsed[:6],
                        tzinfo=timezone.utc,
                    )
            except Exception:
                pass

    return None


# ============================================================
# RSS
# ============================================================

def parse_rss(
    url,
    source_name,
    max_articles=100,
):
    response = fetch_url(url)

    if response is None:
        return []

    try:
        feed = feedparser.parse(
            response.content
        )
    except Exception as exc:
        logger.warning(
            "RSS parse error %s: %s",
            url,
            exc,
        )
        return []

    articles = []

    for entry in feed.entries[:max_articles]:

        title = normalize_text(
            entry.get("title", "")
        )

        summary = normalize_text(
            entry.get(
                "summary",
                entry.get("description", ""),
            )
        )

        link = entry.get("link", "")

        if not title or not link:
            continue

        articles.append({
            "source": source_name,
            "title": title,
            "summary": summary,
            "url": link,
            "date": parse_date(entry),
        })

    return articles


# ============================================================
# HTML ARTICLE EXTRACTION
# ============================================================

def extract_articles_from_html(
    html_content,
    base_url,
    source_name,
    max_articles=100,
):
    soup = BeautifulSoup(
        html_content,
        "html.parser",
    )

    articles = []

    seen_urls = set()

    # Supprime les zones qui contiennent souvent
    # navigation / publicité / menus / footer.
    for tag in soup([
        "script",
        "style",
        "noscript",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
    ]):
        tag.decompose()

    for link in soup.find_all("a", href=True):

        title = normalize_text(
            link.get_text(" ", strip=True)
        )

        href = link.get("href")

        if not title or not href:
            continue

        if len(title) < 20:
            continue

        absolute_url = urljoin(
            base_url,
            href,
        )

        if absolute_url in seen_urls:
            continue

        # Évite les liens qui sont clairement
        # navigationnels.
        lowered = title.lower()

        if lowered in {
            "home",
            "latest",
            "news",
            "more",
            "read more",
            "next",
            "previous",
            "login",
            "subscribe",
        }:
            continue

        seen_urls.add(
            absolute_url
        )

        parent = link.parent

        summary = ""

        if parent:
            summary = normalize_text(
                parent.get_text(
                    " ",
                    strip=True,
                )
            )

        articles.append({
            "source": source_name,
            "title": title,
            "summary": summary[:2000],
            "url": absolute_url,
            "date": None,
        })

        if len(articles) >= max_articles:
            break

    return articles


# ============================================================
# HTML SOURCE
# ============================================================

def scrape_html_source(
    source,
):
    source_name = source["name"]

    logger.info(
        "Scanning %s",
        source_name,
    )

    response = fetch_url(
        source["url"]
    )

    if response is None:
        return []

    return extract_articles_from_html(
        response.text,
        source["url"],
        source_name,
        source.get(
            "max_articles",
            MAX_ARTICLES_PER_SOURCE,
        ),
    )


# ============================================================
# RSS SOURCE
# ============================================================

def scrape_rss_source(
    source,
):
    source_name = source["name"]

    logger.info(
        "Scanning %s",
        source_name,
    )

    articles = []

    for feed_url in source.get(
        "feeds",
        [],
    ):
        logger.info(
            "Trying feed: %s",
            feed_url,
        )

        found = parse_rss(
            feed_url,
            source_name,
            source.get(
                "max_articles",
                MAX_ARTICLES_PER_SOURCE,
            ),
        )

        articles.extend(
            found
        )

    if articles:
        return articles

    fallback = source.get(
        "fallback"
    )

    if fallback:
        logger.info(
            "RSS unavailable for %s, "
            "using HTML fallback",
            source_name,
        )

        response = fetch_url(
            fallback
        )

        if response:
            return extract_articles_from_html(
                response.text,
                fallback,
                source_name,
                source.get(
                    "max_articles",
                    MAX_ARTICLES_PER_SOURCE,
                ),
            )

    return []


# ============================================================
# SOURCE SCANNING
# ============================================================

def scan_source(source):
    if source["type"] == "rss":
        return scrape_rss_source(
            source
        )

    if source["type"] == "html":
        return scrape_html_source(
            source
        )

    logger.warning(
        "Unknown source type: %s",
        source["type"],
    )

    return []


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_articles(
    articles,
):
    result = []

    seen = set()

    for article in articles:

        url = article.get(
            "url",
            "",
        ).split("?")[0].rstrip("/")

        title = re.sub(
            r"\W+",
            " ",
            article.get(
                "title",
                "",
            ).lower(),
        ).strip()

        key = (
            url
            if url
            else title
        )

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)

        result.append(
            article
        )

    return result


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_article(
    article,
):
    title = normalize_text(
        article.get(
            "title",
            "",
        )
    )

    summary = normalize_text(
        article.get(
            "summary",
            "",
        )
    )

    body = normalize_text(
        article.get(
            "body",
            "",
        )
    )

    # Le titre et le résumé ont davantage
    # d'importance que le corps.
    headline_text = (
        title
        + " "
        + summary
    )

    all_text = (
        headline_text
        + " "
        + body
    )

    geography = find_terms(
        all_text,
        CENTRAL_ASIA_TERMS,
    )

    critical_hr = find_terms(
        headline_text,
        CRITICAL_HR_TERMS,
    )

    strong_hr = find_terms(
        headline_text,
        STRONG_HR_TERMS,
    )

    domestic = find_terms(
        headline_text,
        DOMESTIC_POLITICAL_TERMS,
    )

    major_events = find_terms(
        headline_text,
        MAJOR_REGIONAL_EVENTS,
    )

    routine_geo = find_terms(
        headline_text,
        ROUTINE_GEO_TERMS,
    )

    regional_actors = find_terms(
        headline_text,
        REGIONAL_ACTORS,
    )

    non_news = find_terms(
        headline_text,
        NON_NEWS_TERMS,
    )

    business = find_terms(
        headline_text,
        BUSINESS_SPORTS_TECH_TERMS,
    )

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = 0

    reasons = []

    if geography:
        score += 2
        reasons.append(
            "géographie: "
            + ", ".join(
                geography[:5]
            )
        )

    # CRITIQUE = priorité absolue.
    if critical_hr:
        score += 14

        reasons.append(
            "droits humains critiques: "
            + ", ".join(
                critical_hr[:6]
            )
        )

    elif strong_hr:
        score += 10

        reasons.append(
            "droits humains/dissidence: "
            + ", ".join(
                strong_hr[:6]
            )
        )

    if domestic:
        score += 6

        reasons.append(
            "politique intérieure: "
            + ", ".join(
                domestic[:6]
            )
        )

    # Important :
    # C est évalué AVANT B.
    if major_events:
        score += 10

        reasons.append(
            "événement régional majeur: "
            + ", ".join(
                major_events[:5]
            )
        )

    if regional_actors:
        score += min(
            len(regional_actors),
            2,
        )

        reasons.append(
            "acteur régional: "
            + ", ".join(
                regional_actors[:5]
            )
        )

    if routine_geo:
        score -= 5

        reasons.append(
            "géopolitique/économie ordinaire: "
            + ", ".join(
                routine_geo[:5]
            )
        )

    if business:
        score -= 10

        reasons.append(
            "contenu secondaire: "
            + ", ".join(
                business[:5]
            )
        )

    # --------------------------------------------------------
    # NON-NEWS
    # --------------------------------------------------------

    if non_news:
        # Une annonce de recrutement peut être
        # intéressante pour l'audit, mais ne doit
        # jamais devenir une fausse actualité A.
        score = min(
            score,
            9,
        )

        reasons.append(
            "contenu non journalistique: "
            + ", ".join(
                non_news[:5]
            )
        )

    score = max(
        0,
        min(
            score,
            20,
        ),
    )

    # --------------------------------------------------------
    # LEVEL
    # --------------------------------------------------------

    if (
        geography
        and (
            critical_hr
            or strong_hr
        )
    ):
        level = "A"

    elif (
        geography
        and major_events
    ):
        level = "C"

    elif (
        geography
        and domestic
    ):
        level = "B"

    else:
        level = "D"

    # Une annonce reste D.
    if non_news:
        level = "D"

    # --------------------------------------------------------
    # RELEVANCE
    # --------------------------------------------------------

    relevant = (
        score >= MIN_RELEVANCE_SCORE
        and bool(geography)
        and not non_news
    )

    article["score"] = score
    article["level"] = level
    article["reasons"] = reasons
    article["relevant"] = relevant

    return article


# ============================================================
# ARTICLE PAGE ENRICHMENT
# ============================================================

def fetch_article_body(
    article,
):
    response = fetch_url(
        article["url"]
    )

    if response is None:
        return ""

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    for tag in soup([
        "script",
        "style",
        "noscript",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "iframe",
    ]):
        tag.decompose()

    candidates = []

    for selector in [
        "article",
        "main",
        ".article-body",
        ".article-content",
        ".entry-content",
        ".post-content",
    ]:
        for element in soup.select(
            selector
        ):
            text = normalize_text(
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(text) > 200:
                candidates.append(
                    text
                )

    if not candidates:
        paragraphs = soup.find_all(
            "p"
        )

        candidates = [
            normalize_text(
                p.get_text(
                    " ",
                    strip=True,
                )
            )
            for p in paragraphs
        ]

    candidates = [
        text
        for text in candidates
        if len(text) > 80
    ]

    return " ".join(
        candidates
    )[:15000]


# ============================================================
# MAIN SCAN
# ============================================================

def scan_news():
    logger.info(
        "Starting Asia Central News Scanner"
    )

    raw_articles = []

    successful_sources = 0

    for source in SOURCES:

        articles = scan_source(
            source
        )

        if articles:
            successful_sources += 1

        raw_articles.extend(
            articles
        )

    logger.info(
        "Raw articles collected: %d",
        len(raw_articles),
    )

    articles = deduplicate_articles(
        raw_articles
    )

    logger.info(
        "Articles after deduplication: %d",
        len(articles),
    )

    # --------------------------------------------------------
    # Première classification
    # --------------------------------------------------------

    classified = []

    for article in articles:
        classified.append(
            classify_article(
                article
            )
        )

    # --------------------------------------------------------
    # Enrichissement des articles
    # potentiellement pertinents.
    # --------------------------------------------------------

    candidates = [
        article
        for article in classified
        if article["score"] >= 5
        or article["level"] in {
            "A",
            "B",
            "C",
        }
    ]

    candidates = sorted(
        candidates,
        key=lambda item: (
            item["date"]
            or datetime.min.replace(
                tzinfo=timezone.utc
            )
        ),
        reverse=True,
    )

    for article in candidates[
        :ARTICLE_PAGE_FETCH_LIMIT
    ]:

        body = fetch_article_body(
            article
        )

        if not body:
            continue

        article["body"] = body

        # Reclassification avec confirmation
        # du contenu de l'article.
        classify_article(
            article
        )

    # --------------------------------------------------------
    # Sélection
    # --------------------------------------------------------

    relevant = [
        article
        for article in classified
        if article.get(
            "relevant",
            False,
        )
    ]

    # Tri par date quand disponible,
    # puis score.
    relevant.sort(
        key=lambda item: (
            item.get("date")
            or datetime.min.replace(
                tzinfo=timezone.utc
            ),
            item.get(
                "score",
                0,
            ),
        ),
        reverse=True,
    )

    # --------------------------------------------------------
    # Stats
    # --------------------------------------------------------

    level_counts = Counter(
        article.get(
            "level",
            "D",
        )
        for article in classified
    )

    analyzed = len(
        classified
    )

    retained = len(
        relevant
    )

    average_score = (
        round(
            sum(
                article.get(
                    "score",
                    0,
                )
                for article in classified
            )
            / analyzed,
            1,
        )
        if analyzed
        else 0
    )

    relevance_rate = (
        round(
            retained
            / analyzed
            * 100,
            1,
        )
        if analyzed
        else 0
    )

    stats = {
        "raw": len(raw_articles),
        "analyzed": analyzed,
        "retained": retained,
        "avg_score": average_score,
        "levels": {
            "A": level_counts.get(
                "A",
                0,
            ),
            "B": level_counts.get(
                "B",
                0,
            ),
            "C": level_counts.get(
                "C",
                0,
            ),
            "D": level_counts.get(
                "D",
                0,
            ),
        },
        "sources": successful_sources,
        "sources_total": len(
            SOURCES
        ),
        "relevance_rate": relevance_rate,
    }

    logger.info(
        "Dashboard: %d analyzed / "
        "%d retained / average score %.1f",
        analyzed,
        retained,
        average_score,
    )

    logger.info(
        "Levels: A=%d B=%d C=%d D=%d",
        stats["levels"]["A"],
        stats["levels"]["B"],
        stats["levels"]["C"],
        stats["levels"]["D"],
    )

    return {
        "articles": relevant[
            :ARTICLES_TO_DISPLAY
        ],
        "audit": classified,
        "stats": stats,
    }


# ============================================================
# HTML
# ============================================================

def format_date(value):
    if not value:
        return "Date inconnue"

    return value.strftime(
        "%Y-%m-%d %H:%M UTC"
    )


def level_label(level):
    return {
        "A": "🟥 A — Priorité droits humains",
        "B": "🟧 B — Politique intérieure",
        "C": "🟦 C — Géopolitique majeure",
        "D": "⚪ D — Faible priorité",
    }.get(
        level,
        level,
    )


def escape(value):
    return html.escape(
        str(value)
    )


def create_web_page(
    data,
):
    articles = data["articles"]
    audit = data["audit"]
    stats = data["stats"]

    now = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    cards = []

    for article in articles:

        reasons = (
            " • ".join(
                article.get(
                    "reasons",
                    [],
                )
            )
            or "Aucune raison particulière"
        )

        cards.append(
            f"""
            <article class="article-card">
                <div class="article-source">
                    {escape(article["source"])}
                </div>

                <h2>
                    <a href="{escape(article["url"])}"
                       target="_blank"
                       rel="noopener">
                        {escape(article["title"])}
                    </a>
                </h2>

                <div class="article-meta">
                    {format_date(article.get("date"))}
                    ·
                    {level_label(article["level"])}
                    ·
                    Score {article["score"]}/20
                </div>

                <p>
                    {escape(article.get("summary", "")[:500])}
                </p>

                <div class="reasons">
                    {escape(reasons)}
                </div>
            </article>
            """
        )

    audit_rows = []

    for article in sorted(
        audit,
        key=lambda item: (
            item.get(
                "score",
                0,
            ),
            item.get(
                "date"
            )
            or datetime.min.replace(
                tzinfo=timezone.utc
            ),
        ),
        reverse=True,
    ):

        retained = (
            "✓"
            if article.get(
                "relevant",
                False,
            )
            else "—"
        )

        audit_rows.append(
            f"""
            <tr>
                <td>{escape(article["source"])}</td>
                <td>
                    <a href="{escape(article["url"])}"
                       target="_blank"
                       rel="noopener">
                        {escape(article["title"])}
                    </a>
                </td>
                <td>{format_date(article.get("date"))}</td>
                <td>{article.get("score", 0)}/20</td>
                <td>{article.get("level", "D")}</td>
                <td>{retained}</td>
            </tr>
            """
        )

    return f"""
<!DOCTYPE html>
<html lang="fr">

<head>
<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Central Asia News Scanner</title>

<style>

body {{
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    max-width: 1200px;
    margin: auto;
    padding: 30px;

    background: #f5f5f5;
    color: #222;
}}

h1 {{
    margin-bottom: 5px;
}}

.subtitle {{
    color: #666;
    margin-bottom: 25px;
}}

.dashboard {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(150px, 1fr));

    gap: 12px;
    margin: 25px 0;
}}

.stat {{
    background: white;
    padding: 18px;
    border-radius: 10px;
    box-shadow:
        0 2px 8px rgba(0,0,0,.08);
}}

.stat-number {{
    font-size: 28px;
    font-weight: 700;
}}

.stat-label {{
    color: #666;
    font-size: 13px;
}}

.article-card {{
    background: white;
    padding: 22px;
    margin: 18px 0;
    border-radius: 10px;
    box-shadow:
        0 2px 8px rgba(0,0,0,.08);
}}

.article-card h2 {{
    margin: 8px 0;
}}

.article-card a {{
    color: #222;
    text-decoration: none;
}}

.article-card a:hover {{
    text-decoration: underline;
}}

.article-source {{
    font-weight: 700;
    color: #555;
}}

.article-meta {{
    font-size: 13px;
    color: #666;
}}

.reasons {{
    margin-top: 12px;
    padding: 10px;
    background: #f1f1f1;
    border-radius: 6px;
    font-size: 13px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
}}

th, td {{
    padding: 9px;
    border-bottom: 1px solid #ddd;
    text-align: left;
    font-size: 13px;
}}

th {{
    background: #eee;
}}

.audit {{
    margin-top: 50px;
    overflow-x: auto;
}}

footer {{
    margin-top: 40px;
    color: #777;
    font-size: 13px;
}}

</style>

</head>

<body>

<h1>Central Asia News Scanner</h1>

<div class="subtitle">
Actualités récentes d’Asie centrale —
droits humains, dissidence, politique,
sécurité, géopolitique majeure et événements régionaux.
</div>

<div>
Dernier scan : {now}
</div>

<div class="dashboard">

<div class="stat">
    <div class="stat-number">
        {stats["analyzed"]}
    </div>
    <div class="stat-label">
        📰 Articles analysés
    </div>
</div>

<div class="stat">
    <div class="stat-number">
        {stats["retained"]}
    </div>
    <div class="stat-label">
        🎯 Articles retenus
    </div>
</div>

<div class="stat">
    <div class="stat-number">
        {stats["avg_score"]}/20
    </div>
    <div class="stat-label">
        📊 Score moyen
    </div>
</div>

<div class="stat">
    <div class="stat-number">
        {stats["levels"]["A"]}
    </div>
    <div class="stat-label">
        🟥 Niveau A
    </div>
</div>

<div class="stat">
    <div class="stat-number">
        {stats["levels"]["B"]}
    </div>
    <div class="stat-label">
        🟧 Niveau B
    </div>
</div>

<div class="stat">
    <div class="stat-number">
        {stats["levels"]["C"]}
    </div>
    <div class="stat-label">
        🟦 Niveau C
    </div>
</div>

<div class="stat">
    <div class="stat-number">
        {stats["levels"]["D"]}
    </div>
    <div class="stat-label">
        ⚪ Niveau D
    </div>
</div>

<div class="stat">
    <div class="stat-number">
        {stats["sources"]}/{stats["sources_total"]}
    </div>
    <div class="stat-label">
        📡 Sources analysées
    </div>
</div>

<div class="stat">
    <div class="stat-number">
        {stats["relevance_rate"]}%
    </div>
    <div class="stat-label">
        🎯 Taux de pertinence
    </div>
</div>

</div>

<h2>Actualités retenues</h2>

{"".join(cards)}

<div class="audit">

<h2>Audit du scan</h2>

<p>
Tous les articles analysés sont listés ci-dessous,
y compris ceux qui ont été filtrés.
</p>

<table>

<thead>
<tr>
    <th>Source</th>
    <th>Article</th>
    <th>Date</th>
    <th>Score</th>
    <th>Niveau</th>
    <th>Retenu</th>
</tr>
</thead>

<tbody>

{"".join(audit_rows)}

</tbody>

</table>

</div>

<footer>
Scanner automatique — dernière exécution :
{now}
</footer>

</body>
</html>
"""


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    result = scan_news()

    page = create_web_page(
        result
    )

    with open(
        "index.html",
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            page
        )

    logger.info(
        "Website generated: index.html"
    )
