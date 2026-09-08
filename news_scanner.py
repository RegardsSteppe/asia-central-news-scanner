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

# Nombre maximum d'articles dont on récupère le body.
ARTICLE_PAGE_FETCH_LIMIT = 80

REQUEST_TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/128.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.8,fr;q=0.6",
    "Connection": "keep-alive",
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

def fetch_url(url, source=None):
    """
    Télécharge une URL.

    Retourne un dictionnaire afin de distinguer :
    - succès
    - erreur HTTP
    - timeout
    - erreur SSL
    - autre erreur
    """

    headers = dict(HEADERS)

    if source:
        custom_headers = source.get(
            "headers",
            {},
        )

        headers.update(custom_headers)

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

        return {
            "ok": True,
            "status": response.status_code,
            "url": response.url,
            "text": response.text,
            "error": "",
        }

    except requests.exceptions.HTTPError as exc:

        status = None

        if exc.response is not None:
            status = exc.response.status_code

        logger.warning(
            "Failed to fetch %s: HTTP %s",
            url,
            status or "?",
        )

        return {
            "ok": False,
            "status": status,
            "url": url,
            "text": "",
            "error": f"HTTP {status}" if status else str(exc),
        }

    except requests.exceptions.Timeout:

        logger.warning(
            "Failed to fetch %s: timeout",
            url,
        )

        return {
            "ok": False,
            "status": None,
            "url": url,
            "text": "",
            "error": "timeout",
        }

    except requests.exceptions.SSLError:

        logger.warning(
            "Failed to fetch %s: SSL error",
            url,
        )

        return {
            "ok": False,
            "status": None,
            "url": url,
            "text": "",
            "error": "SSL error",
        }

    except requests.exceptions.RequestException as exc:

        logger.warning(
            "Failed to fetch %s: %s",
            url,
            exc,
        )

        return {
            "ok": False,
            "status": None,
            "url": url,
            "text": "",
            "error": str(exc),
        }

    except Exception as exc:

        logger.warning(
            "Failed to fetch %s: %s",
            url,
            exc,
        )

        return {
            "ok": False,
            "status": None,
            "url": url,
            "text": "",
            "error": str(exc),
        }


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
# VOCABULAIRE DES TITRES
# ============================================================

TITLE_STOPWORDS = {
    # English
    "the",
    "and",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "from",
    "at",
    "by",
    "as",
    "is",
    "are",
    "was",
    "were",
    "a",
    "an",
    "this",
    "that",
    "these",
    "those",
    "after",
    "before",
    "into",
    "over",
    "under",
    "about",
    "amid",
    "new",
    "news",

    # Français
    "le",
    "la",
    "les",
    "un",
    "une",
    "des",
    "de",
    "du",
    "et",
    "ou",
    "à",
    "au",
    "aux",
    "en",
    "dans",
    "sur",
    "pour",
    "avec",
    "par",
    "ce",
    "cette",
    "ces",
    "après",
    "avant",
    "entre",
    "vers",
    "plus",
    "sans",

    # Russe
    "и",
    "в",
    "во",
    "на",
    "с",
    "со",
    "из",
    "по",
    "к",
    "ко",
    "для",
    "от",
    "до",
    "за",
    "что",
    "как",
    "не",
    "это",
    "а",
    "но",

    # Mots journalistiques très fréquents
    "says",
    "said",
    "report",
    "reports",
    "according",
    "latest",
    "update",
    "officials",
    "official",
}


def extract_title_words(title):
    """
    Extrait les mots significatifs d'un titre.

    - minuscules
    - conserve les lettres Unicode
    - supprime les chiffres
    - supprime la ponctuation
    - ignore les stopwords
    - ignore les mots d'une seule lettre
    """

    if not title:
        return []

    text = normalize_text(title)

    # Conserve les lettres Unicode.
    # Les chiffres et la ponctuation sont supprimés.
    words = re.findall(
        r"[^\W\d_]+",
        text,
        flags=re.UNICODE,
    )

    result = []

    for word in words:

        if len(word) < 2:
            continue

        if word in TITLE_STOPWORDS:
            continue

        result.append(word)

    return result


def build_title_word_list(
    articles,
    min_count=2,
    max_words=100,
):
    """
    Construit la liste des mots présents dans les titres.

    Retour :

    [
        {
            "word": "kazakhstan",
            "count": 42,
        },
        {
            "word": "uzbekistan",
            "count": 31,
        },
        ...
    ]

    min_count :
        nombre minimum d'apparitions d'un mot.

    max_words :
        nombre maximum de mots retournés.
    """

    counts = {}

    for article in articles:

        title = article.get(
            "title",
            "",
        )

        words = extract_title_words(
            title
        )

        for word in words:

            counts[word] = (
                counts.get(word, 0) + 1
            )

    vocabulary = [
        {
            "word": word,
            "count": count,
        }
        for word, count in counts.items()
        if count >= min_count
    ]

    vocabulary.sort(
        key=lambda item: (
            item["count"],
            item["word"],
        ),
        reverse=True,
    )

    return vocabulary[:max_words]


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
        "/page/",
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

        # Le body sera récupéré uniquement
        # pour les meilleurs candidats.
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

    result = fetch_url(
        feed_url,
        source,
    )

    if not result["ok"]:
        return [], result

    raw = result["text"]

    try:

        parsed = feedparser.parse(raw)

    except Exception as exc:

        logger.warning(
            "Failed to parse feed %s: %s",
            feed_url,
            exc,
        )

        return [], {
            "ok": False,
            "status": result.get("status"),
            "url": feed_url,
            "text": "",
            "error": f"feed parse: {exc}",
        }

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

    return articles, result


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

    result = fetch_url(
        url,
        source,
    )

    if not result["ok"]:
        return [], result

    raw = result["text"]

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
    # FALLBACK LINK EXTRACTION
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

    return articles, result


# ============================================================
# ARTICLE BODY
# ============================================================

def extract_article_body(
    url,
    source=None,
):

    result = fetch_url(
        url,
        source,
    )

    if not result["ok"]:
        return ""

    raw = result["text"]

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

    errors = []

    successful_fetch = False

    source_type = source.get(
        "type",
        "html",
    )

    # --------------------------------------------------------
    # RSS
    # --------------------------------------------------------

    if source_type == "rss":

        for feed_url in source.get(
            "feeds",
            [],
        ):

            feed_articles, result = parse_feed(
                feed_url,
                source,
            )

            if result.get("ok"):
                successful_fetch = True

            else:
                errors.append(
                    result.get(
                        "error",
                        "unknown error",
                    )
                )

            articles.extend(
                feed_articles
            )

            if len(articles) >= source.get(
                "max_articles",
                MAX_FEED_ENTRIES,
            ):
                break

        # ----------------------------------------------------
        # FALLBACKS RSS → HTML
        # ----------------------------------------------------

        if (
            not articles
            and source.get("fallbacks")
        ):

            for fallback in source.get(
                "fallbacks",
                [],
            ):

                logger.info(
                    "RSS unavailable for %s, "
                    "trying HTML fallback: %s",
                    source["name"],
                    fallback,
                )

                fallback_articles, result = (
                    parse_html_source(
                        fallback,
                        source,
                    )
                )

                if result.get("ok"):
                    successful_fetch = True

                else:
                    errors.append(
                        result.get(
                            "error",
                            "unknown error",
                        )
                    )

                articles.extend(
                    fallback_articles
                )

                if articles:
                    break

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    elif source_type == "html":

        urls = []

        if source.get("url"):
            urls.append(
                source["url"]
            )

        urls.extend(
            source.get(
                "fallbacks",
                [],
            )
        )

        for url in urls:

            html_articles, result = (
                parse_html_source(
                    url,
                    source,
                )
            )

            if result.get("ok"):
                successful_fetch = True

            else:
                errors.append(
                    result.get(
                        "error",
                        "unknown error",
                    )
                )

            articles.extend(
                html_articles
            )

            if articles:
                break

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

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

    articles = articles[
        :source.get(
            "max_articles",
            MAX_HTML_ARTICLES,
        )
    ]

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if articles:

        status = "success"

    elif successful_fetch:

        status = "empty"

    else:

        status = "error"

    error_text = ""

    if errors:
        error_text = "; ".join(
            dict.fromkeys(errors)
        )

    return {
        "articles": articles,
        "status": status,
        "error": error_text,
    }


# ============================================================
# COLLECTE AVEC CACHE
# ============================================================

def collect_articles(memory):

    all_articles = []

    stats = {
        "attempted": 0,
        "successful": 0,
        "empty": 0,
        "errors": 0,
        "cached": 0,
        "articles": 0,
        "sources": [],
    }

    for source in SOURCES:

        # ----------------------------------------------------
        # CACHE
        # ----------------------------------------------------

        if is_source_cached(
            memory,
            source,
        ):

            stats["cached"] += 1

            logger.info(
                "CACHE: %s -> scan ignoré (< 1h)",
                source["name"],
            )

            stats["sources"].append({
                "name": source["name"],
                "status": "cached",
                "articles": 0,
                "error": "",
            })

            continue

        stats["attempted"] += 1

        # ----------------------------------------------------
        # SCAN
        # ----------------------------------------------------

        try:

            result = scan_source(
                source
            )

            articles = result[
                "articles"
            ]

            status = result[
                "status"
            ]

            error = result.get(
                "error",
                "",
            )

            all_articles.extend(
                articles
            )

            if status == "success":
                stats["successful"] += 1

            elif status == "empty":
                stats["empty"] += 1

            else:
                stats["errors"] += 1

            stats["articles"] += len(
                articles
            )

            stats["sources"].append({
                "name": source["name"],
                "status": status,
                "articles": len(articles),
                "error": error,
            })

            mark_source_scanned(
                memory,
                source,
                len(articles),
            )

            if status == "success":

                logger.info(
                    "[OK] %s -> %d articles",
                    source["name"],
                    len(articles),
                )

            elif status == "empty":

                logger.warning(
                    "[EMPTY] %s -> "
                    "site accessible, "
                    "aucun article extrait",
                    source["name"],
                )

            else:

                logger.warning(
                    "[ERROR] %s -> %s",
                    source["name"],
                    error or "unknown error",
                )

        except Exception:

            stats["errors"] += 1

            logger.exception(
                "Source failed: %s",
                source.get("name"),
            )

            stats["sources"].append({
                "name": source["name"],
                "status": "error",
                "articles": 0,
                "error": "unexpected exception",
            })

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    logger.info(
        "Sources: %d tentées | "
        "%d OK | %d vides | %d erreurs | "
        "%d cache",
        stats["attempted"],
        stats["successful"],
        stats["empty"],
        stats["errors"],
        stats["cached"],
    )

    logger.info(
        "Articles collectés: %d",
        stats["articles"],
    )

    # --------------------------------------------------------
    # SOURCE DETAILS
    # --------------------------------------------------------

    for item in stats["sources"]:

        if item["status"] == "cached":
            continue

        if item["status"] == "success":

            logger.info(
                "SOURCE %-30s %3d articles",
                item["name"],
                item["articles"],
            )

        elif item["status"] == "empty":

            logger.info(
                "SOURCE %-30s EMPTY",
                item["name"],
            )

        else:

            logger.info(
                "SOURCE %-30s ERROR: %s",
                item["name"],
                item["error"],
            )

    return (
        all_articles,
        stats,
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

    source_lookup = {
        source["name"]: source
        for source in SOURCES
    }

    for article in audit:

        if article.get(
            "url"
        ) not in candidate_urls:
            continue

        source = source_lookup.get(
            article.get("source")
        )

        body = extract_article_body(
            article.get(
                "url",
                "",
            ),
            source,
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
    source_stats,
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

        "level_a": levels["A"],
        "level_b": levels["B"],
        "level_c": levels["C"],
        "level_d": levels["D"],

        # ----------------------------------------------------
        # SOURCES
        # ----------------------------------------------------

        "sources_successful": source_stats[
            "successful"
        ],

        "sources_total": len(
            SOURCES
        ),

        "sources_attempted": source_stats[
            "attempted"
        ],

        "sources_empty": source_stats[
            "empty"
        ],

        "sources_errors": source_stats[
            "errors"
        ],

        "sources_skipped_cache": source_stats[
            "cached"
        ],

        "source_details": source_stats[
            "sources"
        ],

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
        source_stats,
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
    # VOCABULAIRE DES TITRES
    # --------------------------------------------------------

    title_words = build_title_word_list(
        audit,
        min_count=2,
        max_words=100,
    )

    logger.info(
        "Vocabulaire des titres: %d mots",
        len(title_words),
    )

    for item in title_words[:20]:

        logger.info(
            "WORD %-25s %d",
            item["word"],
            item["count"],
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
        source_stats,
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
        title_words,
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

    if args.memory:

        show_memory()

        return

    scan_news()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
