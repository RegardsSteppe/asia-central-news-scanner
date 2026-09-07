# news_scanner.py

import argparse
import logging
import re

from datetime import datetime, timezone
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

from sources import SOURCES
from scoring import classify_article
from memory import (
    load_memory,
    save_memory,
    is_source_cached,
    mark_source_scanned,
    save_articles,
    get_all_articles,
    get_memory_stats,
)
from html_template import create_web_page


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FEED_ENTRIES = 100
MAX_HTML_ARTICLES = 100

ARTICLES_TO_DISPLAY = 20
ARTICLE_PAGE_FETCH_LIMIT = 80

REQUEST_TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/128.0 Safari/537.36"
    )
}


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

def fetch_url(url):

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.text

    except Exception as exc:

        logger.warning(
            "Failed to fetch %s: %s",
            url,
            exc,
        )

        return None


# ============================================================
# TEXTE
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        str(text),
    )

    return text.strip()


def normalize_text(text):

    return clean_text(text).lower()


# ============================================================
# DATES
# ============================================================

def parse_date(value):

    if not value:
        return None

    if isinstance(value, datetime):

        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value

    value = str(value).strip()

    try:

        parsed = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed

    except Exception:
        pass

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(
                value,
                fmt,
            )

            return parsed.replace(
                tzinfo=timezone.utc
            )

        except Exception:
            continue

    return None


def extract_date_from_container(container):

    if not container:
        return None

    time_tag = container.find("time")

    if time_tag:

        value = (
            time_tag.get("datetime")
            or time_tag.get_text(
                " ",
                strip=True,
            )
        )

        parsed = parse_date(value)

        if parsed:
            return parsed

    for element in container.find_all(
        [
            "meta",
            "span",
            "div",
            "p",
        ],
        limit=30,
    ):

        classes = " ".join(
            element.get(
                "class",
                [],
            )
        )

        itemprop = element.get(
            "itemprop",
            "",
        )

        text = element.get_text(
            " ",
            strip=True,
        )

        marker = (
            f"{classes} {itemprop}"
        ).lower()

        if any(
            word in marker
            for word in [
                "date",
                "time",
                "published",
                "publish",
                "timestamp",
            ]
        ):

            parsed = parse_date(
                element.get("datetime")
                or element.get("content")
                or text
            )

            if parsed:
                return parsed

    return None


# ============================================================
# URL
# ============================================================

def absolute_url(
    base_url,
    href,
):

    if not href:
        return ""

    return urljoin(
        base_url,
        href.strip(),
    )


def is_probable_article_url(url):

    if not url:
        return False

    lowered = url.lower()

    if lowered.startswith("#"):
        return False

    if lowered.startswith("javascript:"):
        return False

    if lowered.startswith("mailto:"):
        return False

    ignored = [
        "/tag/",
        "/tags/",
        "/category/",
        "/categories/",
        "/author/",
        "/authors/",
        "/search",
        "/about",
        "/contact",
        "/login",
        "/subscribe",
        "/privacy",
        "/terms",
        "/donate",
    ]

    return not any(
        part in lowered
        for part in ignored
    )


# ============================================================
# ARTICLE
# ============================================================

def build_article(
    title,
    url,
    summary,
    date,
    source,
):

    return {
        "title": clean_text(title),
        "url": url,
        "summary": clean_text(summary),

        # Le body sera récupéré plus tard
        # uniquement pour les meilleurs candidats.
        "body": "",

        "date": date,

        "source": source["name"],

        "source_short": source.get(
            "short_name",
            source["name"],
        ),

        "source_profile": source.get(
            "profile",
            "",
        ),

        "source_label": source.get(
            "label",
            "",
        ),
    }


# ============================================================
# RSS
# ============================================================

def parse_feed(
    feed_url,
    source,
):

    logger.info(
        "Trying feed: %s",
        feed_url,
    )

    raw = fetch_url(feed_url)

    if not raw:
        return []

    try:

        parsed = feedparser.parse(raw)

    except Exception as exc:

        logger.warning(
            "Failed to parse feed %s: %s",
            feed_url,
            exc,
        )

        return []

    articles = []

    for entry in parsed.entries[
        :MAX_FEED_ENTRIES
    ]:

        title = clean_text(
            entry.get(
                "title",
                "",
            )
        )

        url = entry.get(
            "link",
            "",
        )

        if not title or not url:
            continue

        summary = clean_text(
            entry.get(
                "summary",
                "",
            )
            or entry.get(
                "description",
                "",
            )
        )

        published = (
            entry.get("published")
            or entry.get("updated")
            or entry.get("created")
            or ""
        )

        date = parse_date(
            published
        )

        if not date:

            for key in [
                "published_parsed",
                "updated_parsed",
                "created_parsed",
            ]:

                parsed_time = entry.get(
                    key
                )

                if not parsed_time:
                    continue

                try:

                    date = datetime(
                        parsed_time.tm_year,
                        parsed_time.tm_mon,
                        parsed_time.tm_mday,
                        parsed_time.tm_hour,
                        parsed_time.tm_min,
                        parsed_time.tm_sec,
                        tzinfo=timezone.utc,
                    )

                    break

                except Exception:
                    pass

        articles.append(
            build_article(
                title,
                url,
                summary,
                date,
                source,
            )
        )

    return articles


# ============================================================
# HTML CONTAINERS
# ============================================================

def find_article_containers(soup):

    containers = []

    semantic_articles = soup.find_all(
        "article"
    )

    if semantic_articles:

        containers.extend(
            semantic_articles
        )

    if not containers:

        selectors = [
            "div[class*='article']",
            "div[class*='post']",
            "div[class*='story']",
            "div[class*='card']",
            "div[class*='item']",
            "li[class*='article']",
            "li[class*='post']",
            "li[class*='story']",
            "li[class*='item']",
        ]

        for selector in selectors:

            try:

                containers.extend(
                    soup.select(
                        selector
                    )
                )

            except Exception:
                continue

    unique = []
    seen_ids = set()

    for container in containers:

        identifier = id(container)

        if identifier in seen_ids:
            continue

        seen_ids.add(identifier)

        unique.append(container)

    return unique


# ============================================================
# EXTRACTION HTML
# ============================================================

def extract_article_from_container(
    container,
    base_url,
    source,
):

    if not container:
        return None

    links = container.find_all(
        "a",
        href=True,
    )

    candidates = []

    for link in links:

        title = clean_text(
            link.get_text(
                " ",
                strip=True,
            )
        )

        if len(title) < 20:
            continue

        href = absolute_url(
            base_url,
            link.get("href"),
        )

        if not is_probable_article_url(
            href
        ):
            continue

        candidates.append(
            (
                title,
                href,
                link,
            )
        )

    if not candidates:
        return None

    title, url, _ = max(
        candidates,
        key=lambda item: len(
            item[0]
        ),
    )

    paragraphs = []

    for paragraph in container.find_all(
        "p"
    ):

        text = clean_text(
            paragraph.get_text(
                " ",
                strip=True,
            )
        )

        if len(text) >= 40:
            paragraphs.append(text)

    summary = " ".join(
        paragraphs[:3]
    )

    if not summary:

        local_text = clean_text(
            container.get_text(
                " ",
                strip=True,
            )
        )

        if len(local_text) > len(title):

            summary = local_text[:800]

    date = extract_date_from_container(
        container
    )

    return build_article(
        title,
        url,
        summary,
        date,
        source,
    )


# ============================================================
# HTML SOURCE
# ============================================================

def parse_html_source(
    url,
    source,
):

    logger.info(
        "Scanning HTML: %s",
        url,
    )

    raw = fetch_url(url)

    if not raw:
        return []

    soup = BeautifulSoup(
        raw,
        "html.parser",
    )

    articles = []
    seen_urls = set()

    containers = find_article_containers(
        soup
    )

    max_articles = min(
        source.get(
            "max_articles",
            MAX_HTML_ARTICLES,
        ),
        MAX_HTML_ARTICLES,
    )

    for container in containers:

        article = extract_article_from_container(
            container,
            url,
            source,
        )

        if not article:
            continue

        article_url = article["url"]

        if article_url in seen_urls:
            continue

        seen_urls.add(
            article_url
        )

        articles.append(
            article
        )

        if len(articles) >= max_articles:
            break

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not articles:

        for link in soup.find_all(
            "a",
            href=True,
        ):

            title = clean_text(
                link.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(title) < 25:
                continue

            article_url = absolute_url(
                url,
                link.get("href"),
            )

            if not is_probable_article_url(
                article_url
            ):
                continue

            if article_url in seen_urls:
                continue

            seen_urls.add(
                article_url
            )

            parent = link.parent

            summary = ""

            if parent:

                paragraphs = parent.find_all(
                    "p"
                )

                summary = " ".join(
                    clean_text(
                        p.get_text(
                            " ",
                            strip=True,
                        )
                    )
                    for p in paragraphs[:2]
                )

            date = extract_date_from_container(
                parent
            )

            articles.append(
                build_article(
                    title,
                    article_url,
                    summary,
                    date,
                    source,
                )
            )

            if len(articles) >= max_articles:
                break

    return articles


# ============================================================
# ARTICLE BODY
# ============================================================

def extract_article_body(url):

    raw = fetch_url(url)

    if not raw:
        return ""

    soup = BeautifulSoup(
        raw,
        "html.parser",
    )

    for tag in soup.find_all(
        [
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
            "form",
            "noscript",
            "iframe",
        ]
    ):

        tag.decompose()

    candidates = []

    for selector in [
        "article",
        "main",
        "[role='main']",
    ]:

        try:

            candidates.extend(
                soup.select(
                    selector
                )
            )

        except Exception:
            pass

    if not candidates:
        candidates = [soup]

    best_text = ""

    for candidate in candidates:

        paragraphs = []

        for paragraph in candidate.find_all(
            "p"
        ):

            text = clean_text(
                paragraph.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(text) >= 30:
                paragraphs.append(text)

        text = " ".join(
            paragraphs
        )

        if len(text) > len(best_text):
            best_text = text

    return best_text[:20000]


# ============================================================
# DEDUPLICATION
# ============================================================

def normalize_url_for_dedup(url):

    if not url:
        return ""

    url = url.strip().lower()

    url = re.sub(
        r"#.*$",
        "",
        url,
    )

    url = re.sub(
        r"[?&](utm_[^=&]+|fbclid|gclid)=[^&]*",
        "",
        url,
    )

    return url.rstrip("/")


def deduplicate_articles(articles):

    result = []

    seen_urls = set()
    seen_titles = set()

    for article in articles:

        normalized_url = (
            normalize_url_for_dedup(
                article.get(
                    "url",
                    "",
                )
            )
        )

        normalized_title = normalize_text(
            article.get(
                "title",
                "",
            )
        )

        if (
            normalized_url
            and normalized_url in seen_urls
        ):
            continue

        if (
            normalized_title
            and normalized_title in seen_titles
        ):
            continue

        if normalized_url:
            seen_urls.add(
                normalized_url
            )

        if normalized_title:
            seen_titles.add(
                normalized_title
            )

        result.append(
            article
        )

    return result


# ============================================================
# SOURCE SCANNER
# ============================================================

def scan_source(source):

    logger.info(
        "Scanning %s",
        source["name"],
    )

    articles = []

    if source.get("type") == "rss":

        for feed_url in source.get(
            "feeds",
            [],
        ):

            feed_articles = parse_feed(
                feed_url,
                source,
            )

            articles.extend(
                feed_articles
            )

            if len(articles) >= source.get(
                "max_articles",
                MAX_FEED_ENTRIES,
            ):
                break

        if (
            not articles
            and source.get("fallback")
        ):

            logger.info(
                "RSS unavailable for %s, "
                "using HTML fallback",
                source["name"],
            )

            articles = parse_html_source(
                source["fallback"],
                source,
            )

    elif source.get("type") == "html":

        if source.get("url"):

            articles = parse_html_source(
                source["url"],
                source,
            )

    for article in articles:

        article["source"] = source["name"]

        article["source_short"] = source.get(
            "short_name",
            source["name"],
        )

        article["source_profile"] = source.get(
            "profile",
            "",
        )

        article["source_label"] = source.get(
            "label",
            "",
        )

    return articles[
        :source.get(
            "max_articles",
            MAX_HTML_ARTICLES,
        )
    ]


# ============================================================
# COLLECTE AVEC CACHE
# ============================================================

def collect_articles(memory):

    all_articles = []

    successful_sources = 0
    skipped_sources = 0

    for source in SOURCES:

        # ----------------------------------------------------
        # CACHE 1 HEURE
        # ----------------------------------------------------

        if is_source_cached(
            memory,
            source,
        ):

            skipped_sources += 1

            logger.info(
                "CACHE: %s -> scan ignoré (< 1h)",
                source["name"],
            )

            continue

        # ----------------------------------------------------
        # SCAN
        # ----------------------------------------------------

        try:

            articles = scan_source(
                source
            )

            if articles:
                successful_sources += 1

            all_articles.extend(
                articles
            )

            mark_source_scanned(
                memory,
                source,
                len(articles),
            )

        except Exception:

            logger.exception(
                "Source failed: %s",
                source.get("name"),
            )

    logger.info(
        "Sources scannées: %d | "
        "sources ignorées par cache: %d",
        successful_sources,
        skipped_sources,
    )

    return (
        all_articles,
        successful_sources,
        skipped_sources,
    )


# ============================================================
# SCORING
# ============================================================

def classify_articles(articles):

    audit = []

    # --------------------------------------------------------
    # PREMIER PASS
    # --------------------------------------------------------

    for article in articles:

        article["body"] = ""

        classify_article(
            article
        )

        audit.append(
            article
        )

    # --------------------------------------------------------
    # MEILLEURS CANDIDATS
    # --------------------------------------------------------

    minimum_date = datetime.min.replace(
        tzinfo=timezone.utc
    )

    candidates = sorted(
        audit,
        key=lambda article: (
            article.get(
                "score",
                0,
            ),
            article.get(
                "date"
            ) or minimum_date,
        ),
        reverse=True,
    )

    candidates = candidates[
        :ARTICLE_PAGE_FETCH_LIMIT
    ]

    candidate_urls = {
        article.get("url")
        for article in candidates
    }

    # --------------------------------------------------------
    # SECOND PASS AVEC BODY
    # --------------------------------------------------------

    for article in audit:

        if article.get(
            "url"
        ) not in candidate_urls:
            continue

        body = extract_article_body(
            article.get(
                "url",
                "",
            )
        )

        if not body:
            continue

        article["body"] = body

        classify_article(
            article
        )

    return audit


# ============================================================
# TRI
# ============================================================

LEVEL_PRIORITY = {
    "A": 4,
    "B": 3,
    "C": 2,
    "D": 1,
}


def sort_articles(articles):

    minimum_date = datetime.min.replace(
        tzinfo=timezone.utc
    )

    return sorted(
        articles,
        key=lambda article: (
            LEVEL_PRIORITY.get(
                article.get(
                    "level",
                    "D",
                ),
                0,
            ),

            article.get(
                "score",
                0,
            ),

            article.get(
                "date"
            ) or minimum_date,
        ),
        reverse=True,
    )


# ============================================================
# STATISTIQUES
# ============================================================

def build_stats(
    audit,
    successful_sources,
    skipped_sources=0,
):

    analyzed = len(audit)

    retained = [
        article
        for article in audit
        if article.get(
            "relevant"
        )
    ]

    scores = [
        article.get(
            "score",
            0,
        )
        for article in audit
    ]

    avg_score = (
        sum(scores) / len(scores)
        if scores
        else 0
    )

    levels = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    }

    for article in audit:

        level = article.get(
            "level",
            "D",
        )

        if level not in levels:
            level = "D"

        levels[level] += 1

    return {
        "analyzed": analyzed,
        "retained": len(retained),

        "avg_score": round(
            avg_score,
            1,
        ),

        "levels": levels,

        # Compatibilité HTML
        "level_a": levels["A"],
        "level_b": levels["B"],
        "level_c": levels["C"],
        "level_d": levels["D"],

        "sources_successful": (
            successful_sources
        ),

        "sources_total": len(
            SOURCES
        ),

        "sources_skipped_cache": (
            skipped_sources
        ),

        "relevance_rate": round(
            (
                len(retained)
                / analyzed
                * 100
            )
            if analyzed
            else 0,
            1,
        ),
    }


# ============================================================
# CONSULTATION MÉMOIRE
# ============================================================

def show_memory():

    memory = load_memory()

    articles = get_all_articles(
        memory
    )

    stats = get_memory_stats(
        memory
    )

    print()
    print("=" * 70)
    print(" MÉMOIRE DU ASIA CENTRAL NEWS SCANNER")
    print("=" * 70)
    print()

    print(
        f"Articles mémorisés : {stats['articles']}"
    )

    print(
        f"Sources mémorisées  : {stats['sources']}"
    )

    print()

    print("Niveaux :")

    print(
        f"  A : {stats['levels']['A']}"
    )

    print(
        f"  B : {stats['levels']['B']}"
    )

    print(
        f"  C : {stats['levels']['C']}"
    )

    print(
        f"  D : {stats['levels']['D']}"
    )

    print()
    print("-" * 70)
    print(" DERNIERS ARTICLES")
    print("-" * 70)

    # Trier la mémoire par dernière apparition
    articles = sorted(
        articles,
        key=lambda article: (
            article.get(
                "last_seen",
                "",
            )
        ),
        reverse=True,
    )

    for article in articles[:30]:

        level = article.get(
            "level",
            "D",
        )

        score = article.get(
            "score",
            0,
        )

        source = article.get(
            "source_short"
        ) or article.get(
            "source",
            "",
        )

        title = article.get(
            "title",
            "",
        )

        theme = article.get(
            "theme",
            "",
        )

        print()

        print(
            f"[{level}] {score}/100 | "
            f"{source}"
        )

        print(
            f"    {theme}"
        )

        print(
            f"    {title}"
        )

    print()
    print("=" * 70)
    print()


# ============================================================
# SCAN PRINCIPAL
# ============================================================

def scan_news():

    logger.info(
        "Starting Asia Central News Scanner"
    )

    # --------------------------------------------------------
    # MÉMOIRE
    # --------------------------------------------------------

    memory = load_memory()

    memory_stats = get_memory_stats(
        memory
    )

    logger.info(
        "Mémoire: %d articles | %d sources",
        memory_stats["articles"],
        memory_stats["sources"],
    )

    # --------------------------------------------------------
    # COLLECTE
    # --------------------------------------------------------

    (
        raw_articles,
        successful_sources,
        skipped_sources,
    ) = collect_articles(
        memory
    )

    logger.info(
        "Articles collectés: %d",
        len(raw_articles),
    )

    # --------------------------------------------------------
    # DÉDOUBLONNAGE
    # --------------------------------------------------------

    articles = deduplicate_articles(
        raw_articles
    )

    logger.info(
        "Après déduplication: %d",
        len(articles),
    )

    # --------------------------------------------------------
    # SCORING
    # --------------------------------------------------------

    audit = classify_articles(
        articles
    )

    # --------------------------------------------------------
    # MÉMOIRE
    # --------------------------------------------------------

    save_articles(
        memory,
        audit,
    )

    save_memory(
        memory
    )

    logger.info(
        "Mémoire sauvegardée"
    )

    # --------------------------------------------------------
    # TRI
    # --------------------------------------------------------

    sorted_audit = sort_articles(
        audit
    )

    # --------------------------------------------------------
    # SÉLECTION
    # --------------------------------------------------------

    selected = [
        article
        for article in sorted_audit
        if article.get(
            "relevant"
        )
    ]

    selected = selected[
        :ARTICLES_TO_DISPLAY
    ]

    # --------------------------------------------------------
    # STATS
    # --------------------------------------------------------

    stats = build_stats(
        sorted_audit,
        successful_sources,
        skipped_sources,
    )

    logger.info(
        "Dashboard: %d analyzed / "
        "%d retained / "
        "average score %.1f",
        stats["analyzed"],
        stats["retained"],
        stats["avg_score"],
    )

    logger.info(
        "Levels: A=%d B=%d C=%d D=%d",
        stats["levels"]["A"],
        stats["levels"]["B"],
        stats["levels"]["C"],
        stats["levels"]["D"],
    )

    # --------------------------------------------------------
    # LOG ARTICLES
    # --------------------------------------------------------

    for article in selected:

        logger.info(
            "[%s] %d/100 | %s | %s | %s",
            article.get(
                "level",
                "D",
            ),

            article.get(
                "score",
                0,
            ),

            article.get(
                "source_short",
                "",
            ),

            article.get(
                "theme",
                "",
            ),

            article.get(
                "title",
                "",
            ),
        )

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    html = create_web_page(
        selected,
        sorted_audit,
        stats,
    )

    with open(
        "index.html",
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            html
        )

    logger.info(
        "Website generated: index.html"
    )

    return (
        selected,
        sorted_audit,
        stats,
    )


# ============================================================
# COMMAND LINE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Asia Central News Scanner"
        )
    )

    parser.add_argument(
        "--memory",
        action="store_true",
        help=(
            "Consulter la mémoire "
            "sans scanner les sites"
        ),
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help=(
            "Forcer un scan des sources"
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # CONSULTATION MÉMOIRE
    # --------------------------------------------------------

    if args.memory:

        show_memory()

        return

    # --------------------------------------------------------
    # SCAN
    # --------------------------------------------------------

    scan_news()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
