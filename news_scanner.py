# news_scanner.py

import html
import json
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

ARTICLES_TO_DISPLAY = 20

ARTICLE_PAGE_FETCH_LIMIT = 60

MIN_RELEVANCE_SCORE = 10

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; "
    "AsiaCentralNewsScanner/3.3; "
    "+https://github.com/RegardsSteppe/"
    "asia-central-news-scanner)"
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
    "Accept-Language": (
        "en-US,en;q=0.9,"
        "fr;q=0.8,ru;q=0.7"
    ),
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
# TEXT
# ============================================================

def normalize_text(text):
    if not text:
        return ""

    text = html.unescape(
        str(text)
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


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

    return (
        re.search(
            pattern,
            text.lower(),
        )
        is not None
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


# ============================================================
# DATES
# ============================================================

def parse_feed_date(entry):
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

    return None


def parse_date_string(value):
    if not value:
        return None

    value = normalize_text(
        value
    )

    # ISO avec Z
    candidates = [
        value,
        value.replace(
            "Z",
            "+00:00",
        ),
    ]

    for candidate in candidates:

        try:
            dt = datetime.fromisoformat(
                candidate
            )

            if dt.tzinfo is None:
                dt = dt.replace(
                    tzinfo=timezone.utc
                )

            return dt.astimezone(
                timezone.utc
            )

        except ValueError:
            pass

    # Formats courants
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",

        "%d.%m.%Y",
        "%d.%m.%Y %H:%M",

        "%d/%m/%Y",
        "%d/%m/%Y %H:%M",

        "%B %d, %Y",
        "%B %d, %Y %H:%M",

        "%b %d, %Y",
        "%b %d, %Y %H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                value,
                fmt,
            ).replace(
                tzinfo=timezone.utc
            )

        except ValueError:
            continue

    return None


def extract_date_from_html(
    soup,
):
    # --------------------------------------------------------
    # <time datetime="">
    # --------------------------------------------------------

    for element in soup.find_all(
        "time"
    ):

        value = (
            element.get(
                "datetime"
            )
            or element.get_text(
                " ",
                strip=True,
            )
        )

        parsed = parse_date_string(
            value
        )

        if parsed:
            return parsed

    # --------------------------------------------------------
    # Meta tags
    # --------------------------------------------------------

    meta_names = [
        "article:published_time",
        "article:modified_time",
        "datePublished",
        "datepublished",
        "publish-date",
        "publish_date",
        "published_time",
        "publication_date",
        "date",
        "dc.date",
        "dc.date.issued",
    ]

    for name in meta_names:

        element = soup.find(
            "meta",
            attrs={
                "property": name
            },
        )

        if element is None:
            element = soup.find(
                "meta",
                attrs={
                    "name": name
                },
            )

        if element:

            value = element.get(
                "content"
            )

            parsed = parse_date_string(
                value
            )

            if parsed:
                return parsed

    # --------------------------------------------------------
    # JSON-LD
    # --------------------------------------------------------

    for script in soup.find_all(
        "script",
        type="application/ld+json",
    ):

        try:
            data = json.loads(
                script.string
                or script.get_text()
            )

        except Exception:
            continue

        objects = (
            data
            if isinstance(
                data,
                list,
            )
            else [data]
        )

        for obj in objects:

            if not isinstance(
                obj,
                dict,
            ):
                continue

            for key in (
                "datePublished",
                "dateCreated",
                "dateModified",
            ):

                parsed = parse_date_string(
                    obj.get(key)
                )

                if parsed:
                    return parsed

    return None


# ============================================================
# RSS
# ============================================================

def parse_rss(
    url,
    source_name,
    max_articles=100,
):
    response = fetch_url(
        url
    )

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

    for entry in feed.entries[
        :max_articles
    ]:

        title = normalize_text(
            entry.get(
                "title",
                "",
            )
        )

        summary = normalize_text(
            entry.get(
                "summary",
                entry.get(
                    "description",
                    "",
                ),
            )
        )

        link = entry.get(
            "link",
            "",
        )

        if not title or not link:
            continue

        articles.append({
            "source": source_name,
            "title": title,
            "summary": summary,
            "url": link,
            "date": parse_feed_date(
                entry
            ),
        })

    return articles


# ============================================================
# HTML EXTRACTION
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

    page_date = extract_date_from_html(
        soup
    )

    # Supprime les zones inutiles.
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

    articles = []

    seen_urls = set()

    for link in soup.find_all(
        "a",
        href=True,
    ):

        title = normalize_text(
            link.get_text(
                " ",
                strip=True,
            )
        )

        href = link.get(
            "href"
        )

        if not title or not href:
            continue

        if len(title) < 20:
            continue

        absolute_url = urljoin(
            base_url,
            href,
        )

        clean_url = (
            absolute_url
            .split("#")[0]
        )

        if clean_url in seen_urls:
            continue

        lowered = title.lower()

        # Navigation évidente
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
            "about",
            "contact",
        }:
            continue

        # Évite quelques faux liens.
        if any(
            part in clean_url.lower()
            for part in [
                "/tag/",
                "/tags/",
                "/author/",
                "/category/",
            ]
        ):
            continue

        parent = link.parent

        context = ""

        if parent:
            context = normalize_text(
                parent.get_text(
                    " ",
                    strip=True,
                )
            )

        article_date = None

        # On cherche une date dans le bloc
        # entourant le lien.
        container = parent

        for _ in range(3):

            if container is None:
                break

            date_found = (
                extract_date_from_html(
                    container
                )
            )

            if date_found:
                article_date = date_found
                break

            container = (
                container.parent
            )

        if article_date is None:
            article_date = page_date

        seen_urls.add(
            clean_url
        )

        articles.append({
            "source": source_name,
            "title": title,
            "summary": context[:2500],
            "url": clean_url,
            "date": article_date,
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
            100,
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
                100,
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
                    100,
                ),
            )

    return []


# ============================================================
# SOURCE
# ============================================================

def scan_source(
    source,
):
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

    seen_urls = set()
    seen_titles = set()

    for article in articles:

        url = (
            article.get(
                "url",
                "",
            )
            .split("?")[0]
            .rstrip("/")
        )

        title = re.sub(
            r"\W+",
            " ",
            article.get(
                "title",
                "",
            ).lower(),
        ).strip()

        if url and url in seen_urls:
            continue

        if title and title in seen_titles:
            continue

        if url:
            seen_urls.add(url)

        if title:
            seen_titles.add(title)

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

    score = 0
    reasons = []

    # --------------------------------------------------------
    # GEOGRAPHIE
    # --------------------------------------------------------

    if geography:
        score += 2

        reasons.append(
            "géographie: "
            + ", ".join(
                geography[:6]
            )
        )

    # --------------------------------------------------------
    # DROITS HUMAINS CRITIQUES
    # --------------------------------------------------------

    if critical_hr:
        score += 14

        reasons.append(
            "droits humains critiques: "
            + ", ".join(
                critical_hr[:8]
            )
        )

    elif strong_hr:
        score += 10

        reasons.append(
            "droits humains/dissidence: "
            + ", ".join(
                strong_hr[:8]
            )
        )

    # --------------------------------------------------------
    # POLITIQUE
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

    if major_events:
        score += 10

        reasons.append(
            "événement régional majeur: "
            + ", ".join(
                major_events[:6]
            )
        )

    # --------------------------------------------------------
    # ACTEURS EXTÉRIEURS
    # --------------------------------------------------------

    if regional_actors:
        actor_bonus = min(
            len(regional_actors),
            2,
        )

        score += actor_bonus

        reasons.append(
            "acteur régional: "
            + ", ".join(
                regional_actors[:6]
            )
        )

    # --------------------------------------------------------
    # GÉOPOLITIQUE ORDINAIRE
    # --------------------------------------------------------

    if routine_geo:
        score -= 5

        reasons.append(
            "géopolitique/économie ordinaire: "
            + ", ".join(
                routine_geo[:6]
            )
        )

    # --------------------------------------------------------
    # BRUIT
    # --------------------------------------------------------

    if business:
        score -= 10

        reasons.append(
            "contenu secondaire: "
            + ", ".join(
                business[:6]
            )
        )

    # --------------------------------------------------------
    # CONTENU NON JOURNALISTIQUE
    # --------------------------------------------------------

    if non_news:

        # Une annonce peut être conservée dans
        # l'audit, mais ne doit jamais devenir
        # une fausse actualité importante.
        score = min(
            score,
            9,
        )

        reasons.append(
            "contenu non journalistique: "
            + ", ".join(
                non_news[:8]
            )
        )

    # --------------------------------------------------------
    # SCORE FINAL
    # --------------------------------------------------------

    score = max(
        0,
        min(
            score,
            20,
        ),
    )

    # --------------------------------------------------------
    # NIVEAU
    #
    # IMPORTANT :
    # A > C > B dans la logique de classification.
    # Cela évite qu'un article SCO soit classé B
    # simplement parce qu'il contient "president".
    # --------------------------------------------------------

    if geography and (
        critical_hr
        or strong_hr
    ):
        level = "A"

    elif geography and major_events:
        level = "C"

    elif geography and domestic:
        level = "B"

    else:
        level = "D"

    # Contenu institutionnel = D.
    if non_news:
        level = "D"

    # --------------------------------------------------------
    # RETENU
    # --------------------------------------------------------

    relevant = (
        bool(geography)
        and score >= MIN_RELEVANCE_SCORE
        and not non_news
    )

    article["score"] = score
    article["level"] = level
    article["reasons"] = reasons
    article["relevant"] = relevant

    return article


# ============================================================
# ARTICLE BODY
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

    selectors = [
        "article",
        "main",
        ".article-body",
        ".article-content",
        ".entry-content",
        ".post-content",
        "[itemprop='articleBody']",
    ]

    for selector in selectors:

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
    )[:18000]


# ============================================================
# TRI
# ============================================================

LEVEL_PRIORITY = {
    "A": 4,
    "B": 3,
    "C": 2,
    "D": 1,
}


def article_sort_key(
    article,
):
    level = article.get(
        "level",
        "D",
    )

    score = article.get(
        "score",
        0,
    )

    date = article.get(
        "date"
    )

    if date is None:
        date = datetime.min.replace(
            tzinfo=timezone.utc
        )

    return (
        LEVEL_PRIORITY.get(
            level,
            0,
        ),
        score,
        date,
    )


# ============================================================
# SCAN
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

        logger.info(
            "%s: %d articles collected",
            source["name"],
            len(articles),
        )

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
    # PREMIÈRE CLASSIFICATION
    # --------------------------------------------------------

    classified = [
        classify_article(
            article
        )
        for article in articles
    ]

    # --------------------------------------------------------
    # ENRICHISSEMENT
    #
    # On récupère le corps uniquement des articles
    # qui ont déjà des signaux intéressants.
    # --------------------------------------------------------

    candidates = [
        article
        for article in classified
        if article.get(
            "score",
            0,
        ) >= 5
        or article.get(
            "level"
        ) in {
            "A",
            "B",
            "C",
        }
    ]

    candidates.sort(
        key=lambda article: (
            article.get(
                "score",
                0,
            ),
            article.get(
                "date"
            )
            or datetime.min.replace(
                tzinfo=timezone.utc
            ),
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

        classify_article(
            article
        )

    # --------------------------------------------------------
    # ARTICLES RETENUS
    # --------------------------------------------------------

    relevant = [
        article
        for article in classified
        if article.get(
            "relevant",
            False,
        )
    ]

    # --------------------------------------------------------
    # TRI :
    #
    # A > B > C > D
    # puis score
    # puis date
    # --------------------------------------------------------

    relevant.sort(
        key=article_sort_key,
        reverse=True,
    )

    # --------------------------------------------------------
    # STATISTIQUES
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
        "%d retained / "
        "average score %.1f",
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
# HTML HELPERS
# ============================================================

def format_date(
    value,
):
    if not value:
        return "Date non disponible"

    return value.strftime(
        "%d/%m/%Y à %H:%M UTC"
    )


def level_label(
    level,
):
    return {
        "A": "🟥 A — Droits humains / répression",
        "B": "🟧 B — Politique intérieure",
        "C": "🟦 C — Géopolitique majeure",
        "D": "⚪ D — Faible priorité",
    }.get(
        level,
        level,
    )


def escape(
    value,
):
    return html.escape(
        str(value)
    )


# ============================================================
# HTML
# ============================================================

def create_web_page(
    data,
):

    articles = data[
        "articles"
    ]

    audit = data[
        "audit"
    ]

    stats = data[
        "stats"
    ]

    now = datetime.now(
        timezone.utc
    )

    now_display = now.strftime(
        "%d/%m/%Y à %H:%M UTC"
    )

    # ========================================================
    # ARTICLES PRINCIPAUX
    # ========================================================

    cards = []

    for article in articles:

        date = format_date(
            article.get(
                "date"
            )
        )

        reasons = (
            " • ".join(
                article.get(
                    "reasons",
                    [],
                )
            )
            or "Aucun signal particulier"
        )

        cards.append(
            f"""
            <article class="article-card">

                <div class="article-header">

                    <span class="level level-{article["level"]}">
                        {escape(article["level"])}
                    </span>

                    <span class="score">
                        {article["score"]}/20
                    </span>

                </div>

                <div class="article-source">
                    {escape(article["source"])}
                </div>

                <h2>
                    <a
                        href="{escape(article["url"])}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        {escape(article["title"])}
                    </a>
                </h2>

                <div class="article-date">
                    📅 {escape(date)}
                </div>

                <div class="theme">
                    {escape(
                        level_label(
                            article["level"]
                        )
                    )}
                </div>

                <p>
                    {escape(
                        article.get(
                            "summary",
                            "",
                        )[:700]
                    )}
                </p>

                <div class="reasons">
                    <strong>Pourquoi :</strong>
                    {escape(reasons)}
                </div>

            </article>
            """
        )

    # ========================================================
    # AUDIT
    # ========================================================

    audit_sorted = sorted(
        audit,
        key=article_sort_key,
        reverse=True,
    )

    audit_rows = []

    for article in audit_sorted:

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

                <td>
                    <span class="audit-level level-{article.get("level", "D")}">
                        {escape(article.get("level", "D"))}
                    </span>
                </td>

                <td>
                    <strong>
                        {article.get("score", 0)}/20
                    </strong>
                </td>

                <td>
                    {escape(
                        format_date(
                            article.get("date")
                        )
                    )}
                </td>

                <td>
                    {escape(
                        article.get(
                            "source",
                            "",
                        )
                    )}
                </td>

                <td>
                    <a
                        href="{escape(article.get("url", ""))}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        {escape(
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
        )

    # ========================================================
    # PAGE
    # ========================================================

    return f"""
<!DOCTYPE html>

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

<style>

* {{
    box-sizing: border-box;
}}

body {{

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    max-width: 1300px;

    margin: auto;

    padding: 30px;

    background: #f5f6f8;

    color: #202124;
}}

h1 {{
    margin-bottom: 5px;
}}

.subtitle {{
    color: #666;
    margin-bottom: 10px;
}}

.scan-date {{
    color: #555;
    font-size: 14px;
    margin-bottom: 25px;
}}


/* ==========================================================
   DASHBOARD
   ========================================================== */

.dashboard {{

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(145px, 1fr)
        );

    gap: 12px;

    margin: 25px 0 35px;
}}

.stat {{

    background: white;

    padding: 17px;

    border-radius: 10px;

    box-shadow:
        0 2px 8px
        rgba(0,0,0,.07);
}}

.stat-number {{

    font-size: 27px;

    font-weight: 700;

    margin-bottom: 5px;
}}

.stat-label {{

    color: #666;

    font-size: 13px;
}}


/* ==========================================================
   ARTICLE
   ========================================================== */

.article-card {{

    background: white;

    padding: 22px;

    margin: 18px 0;

    border-radius: 10px;

    box-shadow:
        0 2px 8px
        rgba(0,0,0,.08);
}}

.article-header {{

    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-bottom: 8px;
}}

.level {{

    display: inline-block;

    padding: 5px 9px;

    border-radius: 6px;

    font-size: 12px;

    font-weight: 700;
}}

.level-A {{
    background: #ffdede;
}}

.level-B {{
    background: #ffe8cc;
}}

.level-C {{
    background: #dceaff;
}}

.level-D {{
    background: #eeeeee;
}}

.score {{

    font-weight: 700;

    font-size: 18px;
}}

.article-source {{

    font-weight: 700;

    color: #555;

    margin-top: 5px;
}}

.article-card h2 {{

    margin: 7px 0 8px;

    font-size: 21px;
}}

.article-card h2 a {{

    color: #202124;

    text-decoration: none;
}}

.article-card h2 a:hover {{
    text-decoration: underline;
}}

.article-date {{

    font-size: 14px;

    font-weight: 600;

    color: #444;

    margin: 8px 0;
}}

.theme {{

    color: #666;

    font-size: 13px;

    margin-bottom: 12px;
}}

.article-card p {{

    line-height: 1.5;

    color: #444;
}}

.reasons {{

    margin-top: 14px;

    padding: 11px;

    background: #f1f2f3;

    border-radius: 6px;

    font-size: 13px;

    line-height: 1.5;
}}


/* ==========================================================
   AUDIT
   ========================================================== */

.audit {{

    margin-top: 55px;
}}

.audit-description {{

    color: #666;

    margin-bottom: 15px;
}}

.audit-table-wrapper {{

    overflow-x: auto;

    background: white;

    border-radius: 10px;

    box-shadow:
        0 2px 8px
        rgba(0,0,0,.06);
}}

table {{

    width: 100%;

    border-collapse: collapse;
}}

th,
td {{

    padding: 10px;

    border-bottom:
        1px solid #ddd;

    text-align: left;

    font-size: 13px;

    vertical-align: top;
}}

th {{

    background: #eeeeee;

    position: sticky;

    top: 0;
}}

td a {{

    color: #222;

    text-decoration: none;
}}

td a:hover {{
    text-decoration: underline;
}}

.audit-level {{

    display: inline-block;

    min-width: 25px;

    text-align: center;

    padding: 4px 6px;

    border-radius: 5px;

    font-weight: 700;
}}


/* ==========================================================
   FOOTER
   ========================================================== */

footer {{

    margin-top: 40px;

    padding-top: 20px;

    border-top:
        1px solid #ddd;

    color: #777;

    font-size: 13px;
}}

</style>

</head>


<body>


<h1>
Central Asia News Scanner
</h1>


<div class="subtitle">

Actualités récentes d’Asie centrale —
droits humains, dissidence,
politique intérieure,
sécurité et géopolitique majeure.

</div>


<div class="scan-date">

Dernier scan :
<strong>
{escape(now_display)}
</strong>

</div>


<!-- ========================================================
     DASHBOARD
========================================================= -->

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


<!-- ========================================================
     ARTICLES
========================================================= -->

<h2>
Actualités prioritaires
</h2>

<p class="subtitle">

Classement :
<strong>
niveau A → B → C → D
</strong>,
puis score décroissant,
puis date la plus récente.

</p>


{"".join(cards)}


<!-- ========================================================
     AUDIT
========================================================= -->

<section class="audit">

<h2>
Audit complet du scan
</h2>

<p class="audit-description">

Tous les articles analysés sont conservés ici,
y compris ceux qui ont été filtrés.
La date, le score, le niveau et le statut
de sélection permettent de contrôler les décisions
du filtre.

</p>


<div class="audit-table-wrapper">

<table>

<thead>

<tr>

<th>
Niveau
</th>

<th>
Score
</th>

<th>
Date
</th>

<th>
Source
</th>

<th>
Article
</th>

<th>
Retenu
</th>

</tr>

</thead>


<tbody>

{"".join(audit_rows)}

</tbody>

</table>

</div>

</section>


<footer>

Central Asia News Scanner ·
Scan automatique du
{escape(now_display)}

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
