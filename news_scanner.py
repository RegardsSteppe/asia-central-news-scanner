#!/usr/bin/env python3
"""
Asia Central News Scanner

Fetches the latest news from selected Central Asian / Asian news sources
and generates a public index.html page for GitHub Pages.
"""

import logging
from datetime import datetime
from html import escape
from urllib.parse import urljoin

import pytz
import requests
from bs4 import BeautifulSoup


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
# NEWS SOURCES
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
        "name": "Stanradar",
        "url": "https://stanradar.com/",
        "description": "Central Asian news agency"
    },
    {
        "name": "Azernews",
        "url": "https://www.azernews.az/",
        "description": "Azerbaijan news source"
    },
    {
        "name": "Radio Free Liberty",
        "url": "https://www.rferl.org/",
        "description": "Radio"
]


# ============================================================
# HTTP CONFIGURATION
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}


# ============================================================
# FETCH NEWS FROM ONE SOURCE
# ============================================================

def fetch_news_from_source(source):
    """
    Fetch news headlines from a single source.

    Returns a dictionary containing:
    - source name
    - description
    - articles
    - status
    """

    try:
        logger.info("Fetching news from %s...", source["name"])

        response = requests.get(
            source["url"],
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        articles = []
        seen_links = set()

        # Common headline selectors
        selectors = [
            "article h1",
            "article h2",
            "article h3",
            "h1",
            "h2",
            "h3",
            '[class*="headline"]',
            '[class*="title"]'
        ]

        for selector in selectors:

            elements = soup.select(selector)

            for element in elements:

                if len(articles) >= 3:
                    break

                title = element.get_text(" ", strip=True)

                # Ignore very short or useless titles
                if len(title) < 20:
                    continue

                # Find the closest link
                link_element = element.find_parent("a")

                if not link_element:
                    link_element = element.find("a")

                if not link_element:
                    link_element = element.find_parent(
                        "article"
                    )

                    if link_element:
                        link_element = link_element.find("a")

                if not link_element:
                    continue

                href = link_element.get("href")

                if not href:
                    continue

                # Convert relative URLs to absolute URLs
                absolute_url = urljoin(
                    source["url"],
                    href
                )

                # Avoid duplicate articles
                if absolute_url in seen_links:
                    continue

                seen_links.add(absolute_url)

                articles.append({
                    "title": title[:200],
                    "link": absolute_url
                })

            if len(articles) >= 3:
                break

        logger.info(
            "%s: %d article(s) found",
            source["name"],
            len(articles)
        )

        return {
            "source": source["name"],
            "description": source["description"],
            "articles": articles[:3],
            "status": "success"
        }

    except requests.RequestException as error:
        logger.warning(
            "Network error for %s: %s",
            source["name"],
            error
        )

        return {
            "source": source["name"],
            "description": source["description"],
            "articles": [],
            "status": f"Network error: {error}"
        }

    except Exception as error:
        logger.warning(
            "Error fetching %s: %s",
            source["name"],
            error
        )

        return {
            "source": source["name"],
            "description": source["description"],
            "articles": [],
            "status": f"Error: {error}"
        }


# ============================================================
# FETCH ALL NEWS
# ============================================================

def fetch_all_news():
    """
    Fetch news from all configured sources.
    """

    all_news = []

    for source in TOP_NEWS_SOURCES:

        news_data = fetch_news_from_source(source)

        all_news.append(news_data)

    return all_news


# ============================================================
# CREATE HTML PAGE
# ============================================================

def create_web_page(news_data):
    """
    Create the public HTML page.
    """

    paris_tz = pytz.timezone("Europe/Paris")

    paris_time = datetime.now(paris_tz).strftime(
        "%d/%m/%Y à %H:%M:%S"
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Asia Central News Digest</title>

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
            font-size: 36px;
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
                font-size: 27px;
            }}

            .source {{
                padding: 18px;
            }}

        }}

    </style>
</head>

<body>

<header class="header">

    <h1>📰 Asia Central News Digest</h1>

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

        articles = source_news["articles"]

        status = source_news["status"]

        html += f"""
    <section class="source">

        <h2>🔗 {source_name}</h2>

        <div class="description">
            {description}
        </div>
"""

        if status == "success" and articles:

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

                html += f"""
        <div class="article">

            <a
                href="{link}"
                target="_blank"
                rel="noopener noreferrer"
            >
                {index}. {title}
            </a>

        </div>
"""

        else:

            html += f"""
        <div class="status">

            ⚠️ Impossible de récupérer cette source.

            <br>

            <small>
                {escape(status)}
            </small>

        </div>
"""

        html += """
    </section>
"""

    html += """
</main>

<footer>

    Asia Central News Scanner
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
    """
    Main program.

    GitHub Actions launches this function once per workflow run.
    """

    logger.info("=" * 60)
    logger.info("Starting Asia Central News Scanner")
    logger.info("=" * 60)

    # Fetch news
    news_data = fetch_all_news()

    # Always create the web page
    create_web_page(news_data)

    logger.info("=" * 60)
    logger.info("News scan completed successfully")
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
