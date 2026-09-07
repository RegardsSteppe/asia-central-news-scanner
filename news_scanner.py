#!/usr/bin/env python3
"""
Asia Central Human Rights News Scanner

Collecte les dernières actualités de plusieurs sources d'Asie centrale,
filtre les articles liés aux droits humains, à la dissidence,
à la répression et aux libertés publiques, puis génère index.html.

Fonctionnement :
1. Recherche un flux RSS sur chaque source.
2. Si aucun RSS n'est disponible, utilise le HTML.
3. Collecte jusqu'à 30 articles par source.
4. Calcule la pertinence de chaque article.
5. Garde les 3 articles pertinents les plus récents.
6. Génère index.html pour GitHub Pages.
"""

import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape
from urllib.parse import urljoin

import pytz
import requests
from bs4 import BeautifulSoup
import feedparser


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("news_scanner.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ============================================================
# SOURCES
# ============================================================

TOP_NEWS_SOURCES = [
    {
        "name": "Eurasianet",
        "url": "https://eurasianet.org/",
        "description": "News and analysis from the Caucasus and Central Asia"
    },
    {
        "name": "Cabar.asia",
        "url": "https://cabar.asia/",
        "description": "Central Asia news portal"
    },
    {
        "name": "Azernews",
        "url": "https://www.azernews.az/",
        "description": "Azerbaijan news source"
    },
    {
        "name": "Radio Free Liberty",
        "url": "https://www.rferl.org/",
        "description": "Radio Free Europe / Radio Liberty"
    }
]


# ============================================================
# CONFIGURATION
# ============================================================

MAX_ARTICLES_TO_COLLECT = 30
ARTICLES_TO_DISPLAY = 3

REQUEST_TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}


# ============================================================
# KEYWORDS
# ============================================================

# Mots très fortement liés à la dissidence / répression.
STRONG_KEYWORDS = [
    "political prisoner",
    "political prisoners",
    "dissident",
    "opposition leader",
    "opposition figure",
    "opposition activist",
    "political activist",
    "human rights defender",
    "rights defender",
    "political persecution",
    "politically motivated",
    "political repression",
    "crackdown",
    "torture",
    "arbitrary detention",
    "arbitrarily detained",
    "forced disappearance",
    "enforced disappearance",
]

# Droits humains et libertés publiques.
HUMAN_RIGHTS_KEYWORDS = [
    "human rights",
    "rights violation",
    "rights violations",
    "civil rights",
    "civil liberties",
    "freedom of speech",
    "freedom of expression",
    "freedom of press",
    "press freedom",
    "free speech",
    "freedom of assembly",
    "freedom of religion",
    "freedom of association",
    "independent media",
    "journalist",
    "journalists",
    "journalism",
    "activist",
    "activists",
    "ngo",
    "civil society",
    "protest",
    "protests",
    "demonstration",
    "demonstrators",
    "arrested",
    "arrest",
    "detained",
    "detention",
    "imprisoned",
    "imprisonment",
    "jailed",
    "prison",
    "sentenced",
    "convicted",
    "trial",
    "court",
    "persecution",
    "repression",
]

# Termes fréquemment utilisés dans les articles concernant
# les mêmes sujets en Asie centrale.
REGIONAL_KEYWORDS = [
    "kazakhstan",
    "kyrgyzstan",
    "kyrgyz",
    "tajikistan",
    "tajik",
    "turkmenistan",
    "turkmen",
    "uzbekistan",
    "uzbek",
    "azerbaijan",
    "kazakh",
]

ALL_KEYWORDS = (
    STRONG_KEYWORDS
    + HUMAN_RIGHTS_KEYWORDS
    + REGIONAL_KEYWORDS
)


# ============================================================
# TEXT UTILITIES
# ============================================================

def normalize_text(text):
    """Normalise un texte pour faciliter la recherche."""
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def keyword_score(title, summary=""):
    """
    Calcule un score de pertinence.

    Le titre est volontairement plus important que le résumé.
    """

    title_text = normalize_text(title)
    summary_text = normalize_text(summary)

    score = 0

    # Très forte priorité aux mots du titre.
    for keyword in STRONG_KEYWORDS:
        if keyword in title_text:
            score += 10
        elif keyword in summary_text:
            score += 5

    # Droits humains / libertés.
    for keyword in HUMAN_RIGHTS_KEYWORDS:
        if keyword in title_text:
            score += 5
        elif keyword in summary_text:
            score += 2

    # Présence d'un pays d'Asie centrale.
    for keyword in REGIONAL_KEYWORDS:
        if keyword in title_text:
            score += 2
        elif keyword in summary_text:
            score += 1

    return score


def is_relevant(title, summary=""):
    """
    Détermine si un article est suffisamment lié
    aux droits humains / dissidence.
    """

    score = keyword_score(title, summary)

    return score >= 5


# ============================================================
# DATE PARSING
# ============================================================

def parse_date(value):
    """
    Convertit différentes formes de dates en datetime UTC.
    """

    if not value:
        return None

    # RSS / RFC 822
    try:
        date = parsedate_to_datetime(value)

        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        return date.astimezone(timezone.utc)

    except Exception:
        pass

    # ISO 8601
    try:
        value = value.replace("Z", "+00:00")
        date = datetime.fromisoformat(value)

        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        return date.astimezone(timezone.utc)

    except Exception:
        return None


# ============================================================
# RSS DISCOVERY
# ============================================================

def discover_rss_feed(source_url):
    """
    Cherche automatiquement un flux RSS déclaré
    dans le HTML de la page d'accueil.
    """

    try:
        response = requests.get(
            source_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        # Flux RSS déclaré dans <link>.
        for link in soup.find_all(
            "link",
            href=True
        ):
            rel = " ".join(
                link.get("rel", [])
            ).lower()

            feed_type = (
                link.get("type", "")
                .lower()
            )

            if (
                "alternate" in rel
                and (
                    "rss" in feed_type
                    or "atom" in feed_type
                    or "feed" in feed_type
                )
            ):
                return urljoin(
                    source_url,
                    link["href"]
                )

        # Quelques noms classiques en fallback.
        candidates = [
            "rss.xml",
            "feed.xml",
            "rss",
            "feed",
            "atom.xml"
        ]

        for candidate in candidates:

            feed_url = urljoin(
                source_url,
                candidate
            )

            try:
                test = requests.get(
                    feed_url,
                    headers=HEADERS,
                    timeout=10
                )

                content_type = (
                    test.headers
                    .get("Content-Type", "")
                    .lower()
                )

                if (
                    test.status_code == 200
                    and (
                        "xml" in content_type
                        or "rss" in content_type
                        or "atom" in content_type
                    )
                ):
                    return feed_url

            except Exception:
                continue

    except Exception as error:
        logger.warning(
            "RSS discovery failed for %s: %s",
            source_url,
            error
        )

    return None


# ============================================================
# FETCH RSS
# ============================================================

def fetch_from_rss(source, feed_url):
    """
    Récupère les articles depuis un flux RSS/Atom.
    """

    logger.info(
        "Using RSS for %s: %s",
        source["name"],
        feed_url
    )

    try:
        response = requests.get(
            feed_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        feed = feedparser.parse(
            response.content
        )

        articles = []

        for entry in feed.entries[:MAX_ARTICLES_TO_COLLECT]:

            title = entry.get(
                "title",
                ""
            ).strip()

            link = entry.get(
                "link",
                ""
            ).strip()

            summary = entry.get(
                "summary",
                entry.get("description", "")
            )

            summary = BeautifulSoup(
                summary,
                "html.parser"
            ).get_text(
                " ",
                strip=True
            )

            if not title or not link:
                continue

            published = None

            for date_field in [
                "published",
                "updated",
                "created"
            ]:
                value = entry.get(
                    date_field
                )

                if value:
                    published = parse_date(
                        value
                    )

                    if published:
                        break

            articles.append({
                "title": title[:250],
                "link": link,
                "summary": summary[:1000],
                "published": published,
                "score": keyword_score(
                    title,
                    summary
                )
            })

        return articles

    except Exception as error:

        logger.warning(
            "RSS error for %s: %s",
            source["name"],
            error
        )

        return []


# ============================================================
# HTML FALLBACK
# ============================================================

def fetch_from_html(source):
    """
    Fallback pour les sites sans RSS exploitable.
    """

    logger.info(
        "Using HTML scraper for %s",
        source["name"]
    )

    try:
        response = requests.get(
            source["url"],
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        articles = []
        seen_links = set()

        selectors = [
            "article",
            "h1",
            "h2",
            "h3"
        ]

        for selector in selectors:

            elements = soup.select(
                selector
            )

            for element in elements:

                if len(articles) >= MAX_ARTICLES_TO_COLLECT:
                    break

                title = element.get_text(
                    " ",
                    strip=True
                )

                if len(title) < 20:
                    continue

                link_element = (
                    element.find_parent("a")
                    or element.find("a")
                )

                if not link_element:

                    article_parent = (
                        element.find_parent(
                            "article"
                        )
                    )

                    if article_parent:
                        link_element = (
                            article_parent.find("a")
                        )

                if not link_element:
                    continue

                href = link_element.get(
                    "href"
                )

                if not href:
                    continue

                absolute_url = urljoin(
                    source["url"],
                    href
                )

                if absolute_url in seen_links:
                    continue

                seen_links.add(
                    absolute_url
                )

                # Cherche un petit résumé éventuel.
                summary = ""

                parent = (
                    element.find_parent(
                        "article"
                    )
                )

                if parent:
                    summary = parent.get_text(
                        " ",
                        strip=True
                    )

                articles.append({
                    "title": title[:250],
                    "link": absolute_url,
                    "summary": summary[:1000],
                    "published": None,
                    "score": keyword_score(
                        title,
                        summary
                    )
                })

            if len(articles) >= MAX_ARTICLES_TO_COLLECT:
                break

        return articles

    except Exception as error:

        logger.warning(
            "HTML error for %s: %s",
            source["name"],
            error
        )

        return []


# ============================================================
# FETCH ONE SOURCE
# ============================================================

def fetch_news_from_source(source):
    """
    Récupère les articles d'une source puis
    garde uniquement les 3 plus récents pertinents.
    """

    logger.info(
        "Fetching %s...",
        source["name"]
    )

    # 1. Essayer de trouver un RSS.
    feed_url = discover_rss_feed(
        source["url"]
    )

    if feed_url:

        articles = fetch_from_rss(
            source,
            feed_url
        )

    else:

        logger.info(
            "No RSS found for %s",
            source["name"]
        )

        articles = fetch_from_html(
            source
        )

    logger.info(
        "%s: %d articles collected",
        source["name"],
        len(articles)
    )

    # ========================================================
    # FILTRE THÉMATIQUE
    # ========================================================

    relevant_articles = [
        article
        for article in articles
        if is_relevant(
            article["title"],
            article["summary"]
        )
    ]

    logger.info(
        "%s: %d relevant article(s)",
        source["name"],
        len(relevant_articles)
    )

    # ========================================================
    # TRI
    # ========================================================

    # Pour les RSS, on dispose normalement d'une vraie date.
    #
    # Pour le fallback HTML, les articles sont déjà récupérés
    # dans l'ordre du site, donc on conserve leur ordre
    # lorsqu'aucune date n'est disponible.

    articles_with_dates = [
        article
        for article in relevant_articles
        if article["published"] is not None
    ]

    articles_without_dates = [
        article
        for article in relevant_articles
        if article["published"] is None
    ]

    articles_with_dates.sort(
        key=lambda article: article["published"],
        reverse=True
    )

    selected_articles = (
        articles_with_dates
        + articles_without_dates
    )[:ARTICLES_TO_DISPLAY]

    return {
        "source": source["name"],
        "description": source["description"],
        "articles": selected_articles,
        "status": (
            "success"
            if selected_articles
            else "no relevant articles"
        )
    }


# ============================================================
# FETCH ALL SOURCES
# ============================================================

def fetch_all_news():

    all_news = []

    for source in TOP_NEWS_SOURCES:

        news_data = fetch_news_from_source(
            source
        )

        all_news.append(
            news_data
        )

    return all_news


# ============================================================
# FORMAT DATE
# ============================================================

def format_article_date(date):

    if not date:
        return ""

    paris_tz = pytz.timezone(
        "Europe/Paris"
    )

    paris_date = date.astimezone(
        paris_tz
    )

    return paris_date.strftime(
        "%d/%m/%Y"
    )


# ============================================================
# CREATE HTML
# ============================================================

def create_web_page(news_data):

    paris_tz = pytz.timezone(
        "Europe/Paris"
    )

    paris_time = datetime.now(
        paris_tz
    ).strftime(
        "%d/%m/%Y à %H:%M:%S"
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Central Asia Human Rights News</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Arial,
        sans-serif;

    background: #f4f6f8;
    color: #222;
}}

.header {{
    background:
        linear-gradient(
            135deg,
            #174a7c,
            #2474b5
        );

    color: white;
    padding: 45px 20px;
    text-align: center;
}}

.header h1 {{
    margin: 0 0 10px;
    font-size: 34px;
}}

.header p {{
    margin: 0;
    opacity: 0.9;
}}

.container {{
    max-width: 1000px;
    margin: 35px auto;
    padding: 0 20px;
}}

.source {{
    background: white;
    border-radius: 12px;
    padding: 25px;
    margin-bottom: 25px;

    box-shadow:
        0 3px 12px rgba(0, 0, 0, 0.08);
}}

.source h2 {{
    margin-top: 0;
    color: #174a7c;

    border-bottom:
        2px solid #e8edf2;

    padding-bottom: 12px;
}}

.description {{
    color: #777;
    font-size: 14px;
    margin-bottom: 20px;
}}

.article {{
    padding: 16px;
    margin-bottom: 12px;

    background: #f7f9fb;
    border-radius: 8px;

    border-left:
        4px solid #2474b5;
}}

.article a {{
    color: #174a7c;
    text-decoration: none;

    font-weight: 600;
    font-size: 17px;
}}

.article a:hover {{
    text-decoration: underline;
}}

.article-date {{
    color: #888;
    font-size: 12px;
    margin-top: 7px;
}}

.status {{
    color: #856404;
    background: #fff3cd;

    padding: 12px;
    border-radius: 6px;
}}

footer {{
    text-align: center;
    color: #777;

    padding: 35px 20px;
    font-size: 13px;
}}

@media (max-width: 600px) {{

    .header h1 {{
        font-size: 26px;
    }}

    .source {{
        padding: 18px;
    }}

}}

</style>

</head>

<body>

<header class="header">

<h1>
    📰 Central Asia Human Rights News
</h1>

<p>
    Dernière mise à jour :
    {escape(paris_time)}
    (Paris)
</p>

</header>

<main class="container">
"""

    for source_news in news_data:

        source_name = escape(
            source_news["source"]
        )

        description = escape(
            source_news["description"]
        )

        articles = source_news[
            "articles"
        ]

        status = source_news[
            "status"
        ]

        html += f"""

<section class="source">

<h2>
    🔗 {source_name}
</h2>

<div class="description">
    {description}
</div>
"""

        if articles:

            for index, article in enumerate(
                articles,
                1
            ):

                title = escape(
                    article["title"]
                )

                link = escape(
                    article["link"],
                    quote=True
                )

                article_date = (
                    format_article_date(
                        article["published"]
                    )
                )

                date_html = ""

                if article_date:
                    date_html = f"""
<div class="article-date">
    📅 {article_date}
</div>
"""

                html += f"""

<div class="article">

<a
    href="{link}"
    target="_blank"
    rel="noopener noreferrer"
>
    {index}. {title}
</a>

{date_html}

</div>
"""

        else:

            html += """

<div class="status">

⚠️ Aucun article récent correspondant
aux critères droits humains / dissidence
n'a été trouvé.

</div>
"""

        html += """

</section>
"""

    html += """

</main>

<footer>

Asia Central Human Rights News Scanner
·
Mise à jour automatique quotidienne

</footer>

</body>

</html>
"""

    with open(
        "index.html",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)

    logger.info(
        "Public HTML page generated: index.html"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info("=" * 60)

    logger.info(
        "Starting Central Asia Human Rights News Scanner"
    )

    logger.info("=" * 60)

    news_data = fetch_all_news()

    create_web_page(
        news_data
    )

    logger.info("=" * 60)

    logger.info(
        "News scan completed successfully"
    )

    logger.info("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as error:

        logger.exception(
            "Unexpected error: %s",
            error
        )

        raise
