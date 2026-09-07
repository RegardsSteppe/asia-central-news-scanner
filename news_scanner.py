#!/usr/bin/env python3
"""
Asia Central Human Rights News Scanner

Collecte plusieurs dizaines d'articles par source, enrichit les candidats avec
le contenu des pages, filtre par géographie + droits humains/dissidence,
déduplique et publie les 3 articles les plus récents par source.
"""

import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape
from urllib.parse import urljoin, urlparse

import feedparser
import pytz
import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FEED_ENTRIES = 40
MAX_HTML_ARTICLES = 30
ARTICLES_TO_DISPLAY = 3
ARTICLE_PAGE_FETCH_LIMIT = 20
REQUEST_TIMEOUT = 20

TOP_NEWS_SOURCES = [
    {
        "name": "Eurasianet",
        "url": "https://eurasianet.org/",
        "description": "News and analysis from the Caucasus and Central Asia",
        "include_azerbaijan": True,
    },
    {
        "name": "Cabar.asia",
        "url": "https://cabar.asia/",
        "description": "Central Asia news portal",
        "include_azerbaijan": False,
    },
    {
        "name": "Azernews",
        "url": "https://www.azernews.az/",
        "description": "Azerbaijan news source",
        "include_azerbaijan": True,
    },
    {
        "name": "Radio Free Liberty",
        "url": "https://www.rferl.org/",
        "description": "Radio Free Europe / Radio Liberty",
        "include_azerbaijan": True,
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}


# ============================================================
# GÉOGRAPHIE
# ============================================================

CENTRAL_ASIA = {
    "Kazakhstan": [
        "kazakhstan",
        "kazakh",
        "kazakhstani",
    ],
    "Kyrgyzstan": [
        "kyrgyzstan",
        "kyrgyz",
        "kyrgyzstani",
    ],
    "Tajikistan": [
        "tajikistan",
        "tajik",
        "tajikistani",
    ],
    "Turkmenistan": [
        "turkmenistan",
        "turkmen",
    ],
    "Uzbekistan": [
        "uzbekistan",
        "uzbek",
        "uzbekistani",
    ],
}

AZERBAIJAN = [
    "azerbaijan",
    "azerbaijani",
    "azerbaïdjan",
    "azerbaïdjanais",
]


# ============================================================
# MOTS-CLÉS DROITS HUMAINS / DISSIDENCE
# ============================================================

STRONG_HR_TERMS = [
    "political prisoner",
    "political prisoners",
    "political detainee",
    "political detainees",
    "dissident",
    "dissidents",
    "opposition leader",
    "opposition figure",
    "opposition activist",
    "political activist",
    "human rights defender",
    "rights defender",
    "political persecution",
    "political repression",
    "politically motivated",
    "arbitrary detention",
    "arbitrarily detained",
    "enforced disappearance",
    "forced disappearance",
    "torture",
    "tortured",
    "transnational repression",
    "press freedom",
    "freedom of expression",
    "freedom of speech",
    "freedom of assembly",
    "freedom of religion",
    "religious freedom",
]


HR_CONTEXT_TERMS = [
    "human rights",
    "rights violation",
    "rights violations",
    "civil rights",
    "civil liberties",
    "independent media",
    "free media",
    "journalist",
    "journalists",
    "activist",
    "activists",
    "ngo",
    "civil society",
    "protest",
    "protests",
    "demonstration",
    "demonstrations",
    "arrested",
    "arrest",
    "detained",
    "detention",
    "imprisoned",
    "imprisonment",
    "jailed",
    "jail",
    "prison",
    "sentenced",
    "convicted",
    "trial",
    "court",
    "persecution",
    "repression",
    "censorship",
    "censored",
    "harassed",
    "harassment",
    "crackdown",
    "crackdowns",
    "political opposition",
    "opposition",
]


ACTION_TERMS = [
    "arrested",
    "arrest",
    "detained",
    "detention",
    "imprisoned",
    "imprisonment",
    "jailed",
    "sentenced",
    "convicted",
    "trial",
    "torture",
    "tortured",
    "killed",
    "threatened",
    "harassed",
    "harassment",
    "censored",
    "censorship",
    "crackdown",
    "repression",
    "persecution",
    "deported",
    "extradited",
    "disappeared",
]


# ============================================================
# SUJETS À PÉNALISER
# ============================================================

NEGATIVE_TERMS = [
    "energy",
    "oil",
    "gas",
    "pipeline",
    "trade",
    "investment",
    "economy",
    "economic",
    "business",
    "technology",
    "ai",
    "artificial intelligence",
    "sports",
    "football",
    "soccer",
    "tennis",
    "weather",
    "tourism",
    "tourist",
    "investment forum",
    "summit",
    "conference",
    "corridor",
    "railway",
    "rail",
    "transport",
    "logistics",
    "cargo",
    "exports",
    "imports",
    "mining",
    "uranium",
    "bank",
    "banking",
    "currency",
    "real estate",
    "agriculture",
    "harvest",
    "aviation",
]


FEED_GUESSES = [
    "rss.xml",
    "feed.xml",
    "rss",
    "feed",
    "atom.xml",
]


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("news_scanner.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


# ============================================================
# TEXTE
# ============================================================

def normalize_text(value):
    value = value or ""

    value = BeautifulSoup(
        str(value),
        "html.parser"
    ).get_text(" ", strip=True)

    value = value.lower()
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def contains_any(text, terms):
    text = normalize_text(text)

    return [
        term
        for term in terms
        if term in text
    ]


# ============================================================
# DATES
# ============================================================

def parse_date(value):
    if not value:
        return None

    if isinstance(value, datetime):
        dt = value

    else:
        value = str(value).strip()

        try:
            dt = parsedate_to_datetime(value)

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            try:
                dt = datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )

            except (
                TypeError,
                ValueError,
            ):
                return None

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return dt.astimezone(timezone.utc)


def format_date(dt):
    if not dt:
        return ""

    paris = dt.astimezone(
        pytz.timezone("Europe/Paris")
    )

    return paris.strftime("%d/%m/%Y")


# ============================================================
# GÉOGRAPHIE
# ============================================================

def geography_matches(
    text,
    include_azerbaijan=False,
):
    text = normalize_text(text)

    matches = []

    for country, terms in CENTRAL_ASIA.items():

        if any(
            term in text
            for term in terms
        ):
            matches.append(country)

    if (
        include_azerbaijan
        and any(
            term in text
            for term in AZERBAIJAN
        )
    ):
        matches.append("Azerbaijan")

    return matches


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_article(
    title,
    summary="",
    body="",
    include_azerbaijan=False,
):
    title_n = normalize_text(title)
    summary_n = normalize_text(summary)
    body_n = normalize_text(body)

    title_summary = (
        f"{title_n} {summary_n}"
    )

    full_text = (
        f"{title_n} "
        f"{summary_n} "
        f"{body_n}"
    )

    # --------------------------------------------------------
    # GÉOGRAPHIE
    # --------------------------------------------------------

    countries = geography_matches(
        title_summary,
        include_azerbaijan=include_azerbaijan,
    )

    # Si le pays n'est pas dans le titre/résumé,
    # on regarde le corps de l'article.
    if not countries:

        countries = geography_matches(
            full_text,
            include_azerbaijan=include_azerbaijan,
        )

    # --------------------------------------------------------
    # MOTS-CLÉS
    # --------------------------------------------------------

    strong_title = contains_any(
        title_n,
        STRONG_HR_TERMS,
    )

    strong_any = contains_any(
        full_text,
        STRONG_HR_TERMS,
    )

    context_title = contains_any(
        title_n,
        HR_CONTEXT_TERMS,
    )

    context_any = contains_any(
        full_text,
        HR_CONTEXT_TERMS,
    )

    actions = contains_any(
        full_text,
        ACTION_TERMS,
    )

    negatives = contains_any(
        title_summary,
        NEGATIVE_TERMS,
    )

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = 0
    reasons = []

    # Géographie
    if countries:

        score += 5

        reasons.append(
            "géographie: "
            + ", ".join(countries)
        )

    else:

        score -= 8

    # Thème fort
    if strong_title:

        score += 8

        reasons.append(
            "thème fort dans le titre"
        )

    elif strong_any:

        score += 5

        reasons.append(
            "thème droits humains/dissidence"
        )

    # Contexte droits humains dans le titre
    if context_title:

        score += 3

        reasons.append(
            "contexte droits humains dans le titre"
        )

    # Plusieurs signaux dans l'article
    if len(context_any) >= 2:

        score += 3

    # Action répressive
    if actions:

        score += 2

        reasons.append(
            "action répressive"
        )

    # --------------------------------------------------------
    # ÉVITER LES FAUX POSITIFS
    # --------------------------------------------------------

    weak_only_terms = {
        "journalist",
        "journalists",
        "activist",
        "activists",
        "opposition",
    }

    context_without_strong = (
        set(context_any)
        <= weak_only_terms
    )

    # "journalist" seul ne suffit pas.
    # "activist" seul ne suffit pas.
    # "opposition" seul ne suffit pas.
    if (
        context_without_strong
        and not strong_any
        and len(actions) == 0
    ):

        score -= 7

    # --------------------------------------------------------
    # PÉNALITÉ HORS SUJET
    # --------------------------------------------------------

    if (
        negatives
        and not strong_any
        and not actions
    ):

        score -= min(
            6,
            len(negatives) * 2,
        )

        reasons.append(
            "signaux hors sujet"
        )

    # Cas typiques comme :
    # "Armenia Courts Central Asia As TRIPP Corridor Takes Shape"
    if (
        any(
            term in title_n
            for term in [
                "corridor",
                "trade",
                "energy",
                "gas",
                "oil",
            ]
        )
        and not strong_title
        and len(actions) == 0
    ):

        score -= 5

    # --------------------------------------------------------
    # CRITÈRE FINAL
    # --------------------------------------------------------

    has_real_hr_signal = bool(
        strong_any
        or len(actions) >= 1
        or (
            len(context_any) >= 2
            and any(
                term in full_text
                for term in [
                    "human rights",
                    "rights violation",
                    "civil rights",
                    "civil liberties",
                    "press freedom",
                    "freedom of expression",
                    "political opposition",
                    "political repression",
                ]
            )
        )
    )

    relevant = bool(
        countries
        and has_real_hr_signal
        and score >= 7
    )

    return {
        "relevant": relevant,
        "score": score,
        "countries": countries,
        "reasons": reasons,
    }


# ============================================================
# DÉCOUVERTE DES FLUX RSS
# ============================================================

def discover_feed_urls(source_url):
    urls = []
    seen = set()

    try:

        response = requests.get(
            source_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.content,
            "html.parser",
        )

        for link in soup.find_all("link"):

            rel = link.get(
                "rel",
                [],
            )

            if isinstance(rel, list):
                rel_text = " ".join(rel).lower()
            else:
                rel_text = str(rel).lower()

            feed_type = str(
                link.get("type", "")
            ).lower()

            href = link.get("href")

            if not href:
                continue

            if (
                "alternate" in rel_text
                and (
                    "rss" in feed_type
                    or "atom" in feed_type
                    or "feed" in feed_type
                )
            ):

                absolute = urljoin(
                    source_url,
                    href,
                )

                if absolute not in seen:

                    seen.add(absolute)
                    urls.append(absolute)

    except Exception as error:

        logger.warning(
            "%s: feed discovery failed: %s",
            source_url,
            error,
        )

    base = (
        source_url.rstrip("/")
        + "/"
    )

    for guess in FEED_GUESSES:

        candidate = urljoin(
            base,
            guess,
        )

        if candidate not in seen:

            urls.append(candidate)

    return urls


# ============================================================
# LECTURE RSS
# ============================================================

def parse_feed(
    feed_url,
    source_name,
):
    try:

        response = requests.get(
            feed_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        parsed = feedparser.parse(
            response.content
        )

        if (
            getattr(parsed, "bozo", False)
            and not parsed.entries
        ):
            return []

        articles = []

        for entry in parsed.entries[
            :MAX_FEED_ENTRIES
        ]:

            title = entry.get(
                "title",
                "",
            ).strip()

            link = entry.get(
                "link",
                "",
            ).strip()

            if not title or not link:
                continue

            summary = (
                entry.get("summary")
                or entry.get("description")
                or ""
            )

            date_value = (
                entry.get("published")
                or entry.get("updated")
                or entry.get("created")
            )

            dt = parse_date(
                date_value
            )

            articles.append(
                {
                    "title": BeautifulSoup(
                        title,
                        "html.parser",
                    ).get_text(
                        " ",
                        strip=True,
                    ),
                    "summary": BeautifulSoup(
                        summary,
                        "html.parser",
                    ).get_text(
                        " ",
                        strip=True,
                    ),
                    "link": link,
                    "date": dt,
                    "source": source_name,
                }
            )

        if articles:

            logger.info(
                "%s: RSS %s -> %d article(s)",
                source_name,
                feed_url,
                len(articles),
            )

        return articles

    except Exception as error:

        logger.debug(
            "%s: RSS failed %s: %s",
            source_name,
            feed_url,
            error,
        )

        return []


# ============================================================
# FALLBACK HTML
# ============================================================

def extract_html_articles(source):
    try:

        response = requests.get(
            source["url"],
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.content,
            "html.parser",
        )

        articles = []
        seen = set()

        for tag in soup.find_all(
            [
                "article",
                "h1",
                "h2",
                "h3",
            ]
        ):

            title = ""

            if tag.name == "article":

                heading = tag.find(
                    [
                        "h1",
                        "h2",
                        "h3",
                    ]
                )

                if heading:
                    title = heading.get_text(
                        " ",
                        strip=True,
                    )

            else:

                title = tag.get_text(
                    " ",
                    strip=True,
                )

            if len(title) < 25:
                continue

            link = tag.find(
                "a",
                href=True,
            )

            if (
                not link
                and tag.parent
            ):

                link = tag.parent.find(
                    "a",
                    href=True,
                )

            if not link:
                continue

            href = link.get("href")

            absolute = urljoin(
                source["url"],
                href,
            )

            if absolute in seen:
                continue

            parsed = urlparse(
                absolute
            )

            source_host = urlparse(
                source["url"]
            ).netloc

            if (
                parsed.netloc
                and parsed.netloc
                != source_host
            ):
                continue

            seen.add(absolute)

            articles.append(
                {
                    "title": title[:300],
                    "summary": "",
                    "link": absolute,
                    "date": None,
                    "source": source["name"],
                }
            )

            if len(articles) >= MAX_HTML_ARTICLES:
                break

        logger.info(
            "%s: HTML fallback -> %d article(s)",
            source["name"],
            len(articles),
        )

        return articles

    except Exception as error:

        logger.warning(
            "%s: HTML fallback failed: %s",
            source["name"],
            error,
        )

        return []


# ============================================================
# ENRICHISSEMENT DES ARTICLES
# ============================================================

def extract_article_page(article):
    try:

        response = requests.get(
            article["link"],
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.content,
            "html.parser",
        )

        # ----------------------------------------------------
        # META DESCRIPTION
        # ----------------------------------------------------

        description = ""

        meta = soup.find(
            "meta",
            attrs={
                "name": re.compile(
                    "^description$",
                    re.I,
                )
            },
        )

        if meta:

            description = meta.get(
                "content",
                "",
            )

        # ----------------------------------------------------
        # PARAGRAPHES
        # ----------------------------------------------------

        paragraphs = []

        for p in soup.select(
            "article p, main p"
        ):

            text = p.get_text(
                " ",
                strip=True,
            )

            if len(text) >= 40:

                paragraphs.append(
                    text
                )

            if len(paragraphs) >= 8:
                break

        body = " ".join(
            paragraphs
        )

        # Fallback général
        if not body:

            for p in soup.find_all("p"):

                text = p.get_text(
                    " ",
                    strip=True,
                )

                if len(text) >= 40:

                    paragraphs.append(
                        text
                    )

                if len(paragraphs) >= 8:
                    break

            body = " ".join(
                paragraphs
            )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        if not article.get("date"):

            date_candidates = []

            selectors = [
                (
                    'meta[property="article:published_time"]',
                    "content",
                ),
                (
                    'meta[name="date"]',
                    "content",
                ),
                (
                    'meta[itemprop="datePublished"]',
                    "content",
                ),
            ]

            for selector, attr in selectors:

                node = soup.select_one(
                    selector
                )

                if (
                    node
                    and node.get(attr)
                ):

                    date_candidates.append(
                        node.get(attr)
                    )

            for value in date_candidates:

                dt = parse_date(value)

                if dt:

                    article["date"] = dt
                    break

        article["page_summary"] = description
        article["body"] = body

        return article

    except Exception as error:

        logger.debug(
            "Article page failed %s: %s",
            article["link"],
            error,
        )

        article["page_summary"] = ""
        article["body"] = ""

        return article


# ============================================================
# DÉDUPLICATION
# ============================================================

def canonical_link(url):
    parsed = urlparse(url)

    clean_path = (
        parsed.path.rstrip("/")
    )

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{clean_path}"
    )


def deduplicate_articles(articles):
    unique = {}

    for article in articles:

        key = canonical_link(
            article["link"]
        )

        if key not in unique:

            unique[key] = article

        else:

            old = unique[key]

            if len(
                article.get(
                    "summary",
                    "",
                )
            ) > len(
                old.get(
                    "summary",
                    "",
                )
            ):

                unique[key] = article

    return list(
        unique.values()
    )


# ============================================================
# TRAITEMENT D'UNE SOURCE
# ============================================================

def fetch_news_from_source(source):

    logger.info("=" * 60)

    logger.info(
        "Fetching %s",
        source["name"],
    )

    all_articles = []

    # --------------------------------------------------------
    # RSS
    # --------------------------------------------------------

    feed_urls = discover_feed_urls(
        source["url"]
    )

    for feed_url in feed_urls[:10]:

        all_articles.extend(
            parse_feed(
                feed_url,
                source["name"],
            )
        )

        if len(all_articles) >= (
            MAX_FEED_ENTRIES * 2
        ):
            break

    all_articles = deduplicate_articles(
        all_articles
    )

    # --------------------------------------------------------
    # FALLBACK HTML
    # --------------------------------------------------------

    if len(all_articles) < 5:

        all_articles.extend(
            extract_html_articles(
                source
            )
        )

        all_articles = deduplicate_articles(
            all_articles
        )

    # --------------------------------------------------------
    # TRI PAR DATE
    # --------------------------------------------------------

    all_articles.sort(
        key=lambda item:
            item.get("date")
            or datetime.min.replace(
                tzinfo=timezone.utc
            ),
        reverse=True,
    )

    candidates = all_articles[
        :ARTICLE_PAGE_FETCH_LIMIT
    ]

    relevant = []

    # --------------------------------------------------------
    # ANALYSE
    # --------------------------------------------------------

    for article in candidates:

        article = extract_article_page(
            article
        )

        full_summary = " ".join(
            [
                article.get(
                    "summary",
                    "",
                ),
                article.get(
                    "page_summary",
                    "",
                ),
            ]
        )

        classification = classify_article(
            article["title"],
            full_summary,
            article.get(
                "body",
                "",
            ),
            include_azerbaijan=source.get(
                "include_azerbaijan",
                False,
            ),
        )

        article.update(
            classification
        )

        logger.info(
            "%s | score=%d | relevant=%s | %s",
            article["title"][:100],
            article["score"],
            article["relevant"],
            "; ".join(
                article["reasons"]
            ),
        )

        if article["relevant"]:

            relevant.append(
                article
            )

    # --------------------------------------------------------
    # IMPORTANT :
    # LES ARTICLES LES PLUS RÉCENTS
    # --------------------------------------------------------

    relevant.sort(
        key=lambda item:
            item.get("date")
            or datetime.min.replace(
                tzinfo=timezone.utc
            ),
        reverse=True,
    )

    selected = relevant[
        :ARTICLES_TO_DISPLAY
    ]

    logger.info(
        "%s: %d relevant article(s), "
        "%d displayed",
        source["name"],
        len(relevant),
        len(selected),
    )

    return {
        "source": source["name"],
        "description": source["description"],
        "articles": selected,
        "status": "success",
        "scanned": len(all_articles),
        "relevant_count": len(relevant),
    }


# ============================================================
# TOUTES LES SOURCES
# ============================================================

def fetch_all_news():

    results = []

    for source in TOP_NEWS_SOURCES:

        results.append(
            fetch_news_from_source(
                source
            )
        )

    return results


# ============================================================
# GÉNÉRATION HTML
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
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Asia Central Human Rights News</title>

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
            opacity: .9;
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
                0 3px 12px
                rgba(0,0,0,.08);
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
            margin-bottom: 18px;
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
            line-height: 1.45;
        }}

        .article a:hover {{
            text-decoration: underline;
        }}

        .date {{
            color: #777;
            font-size: 13px;
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

    <h1>
        📰 Asia Central Human Rights News
    </h1>

    <p>
        Dernière mise à jour :
        {escape(paris_time)}
        (Paris)
    </p>

</header>

<main class="container">
"""

    # ========================================================
    # SOURCES
    # ========================================================

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

        html += f"""
    <section class="source">

        <h2>
            🔗 {source_name}
        </h2>

        <div class="description">
            {description}
        </div>
"""

        # ----------------------------------------------------
        # ARTICLES
        # ----------------------------------------------------

        if articles:

            for index, article in enumerate(
                articles,
                1,
            ):

                title = escape(
                    article["title"]
                )

                link = escape(
                    article["link"],
                    quote=True,
                )

                date = format_date(
                    article.get("date")
                )

                if date:

                    date_html = (
                        '<div class="date">'
                        f'📅 {escape(date)}'
                        '</div>'
                    )

                else:

                    date_html = ""

                html += f"""
        <div class="article">

            <a href="{link}"
               target="_blank"
               rel="noopener noreferrer">

                {index}. {title}

            </a>

            {date_html}

        </div>
"""

        # ----------------------------------------------------
        # AUCUN ARTICLE
        # ----------------------------------------------------

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

    # ========================================================
    # FIN
    # ========================================================

    html += """
</main>

<footer>

    Asia Central Human Rights News Scanner
    · Mise à jour automatique quotidienne

</footer>

</body>
</html>
"""

    with open(
        "index.html",
        "w",
        encoding="utf-8",
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
        "Starting Asia Central Human Rights News Scanner"
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
            error,
        )

        raise
