#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Central Asia News Scanner

Pipeline:

    RSS / HTML
        ↓
    HTTP fetch
        ↓
    robust decoding
        ↓
    Unicode / mojibake repair
        ↓
    text cleaning
        ↓
    deduplication
        ↓
    simple deterministic scoring
        ↓
    full-body enrichment for top articles
        ↓
    final ranking
        ↓
    GitHub Pages HTML

Memory is intentionally optional and NEVER blocks the scan.
"""

from __future__ import annotations

import argparse
import html
import logging
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import (
    parse_qsl,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
)

import feedparser
import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# PROJECT IMPORTS
# ---------------------------------------------------------------------------

from sources import SOURCES
from scoring import classify_article
from memory import load_memory, save_memory
from html_template import create_web_page


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

MAX_FEED_ENTRIES = 100
MAX_HTML_ARTICLES = 100

# Number of articles shown on the final page.
ARTICLES_TO_DISPLAY = 20

# Number of promising articles for which we fetch the full article body.
ARTICLE_PAGE_FETCH_LIMIT = 80

REQUEST_TIMEOUT = 20

# Cache lifetime for normal scans.
CACHE_TTL_SECONDS = 60 * 60

# Title vocabulary.
TITLE_VOCAB_MIN_COUNT = 1
TITLE_VOCAB_MAX_WORDS = 300


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36 "
        "CentralAsiaNewsScanner/1.0"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,application/rss+xml;q=0.8,"
        "application/atom+xml;q=0.8,*/*;q=0.5"
    ),
    "Accept-Language": (
        "en-US,en;q=0.8,ru;q=0.7,fr;q=0.6"
    ),
    "Connection": "keep-alive",
}


# ---------------------------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------------------------

MOJIBAKE_MARKERS = (
    "Ã",
    "Â",
    "Ð",
    "Ñ",
    "ð",
    "ñ",
    "â",
    "�",
)


def repair_mojibake(text: Any) -> str:
    """
    Repairs common UTF-8 → Latin-1/Windows-1252 mojibake.

    Examples of corruption this targets:

        Рахмет → Рахмет        (already correct, untouched)
        ÐšÐ°Ð·Ð°Ñ…ÑÑ‚Ð°Ð½ → Казахстан
        Ã© → é
        â€™ → ’

    The repair is deliberately conservative.
    """

    if text is None:
        return ""

    text = str(text)

    if not text:
        return ""

    # Fast path: normal Unicode.
    if not any(marker in text for marker in MOJIBAKE_MARKERS):
        return text

    candidates = [text]

    # Latin-1 round-trip is the classic UTF-8 mojibake repair.
    try:
        candidates.append(
            text.encode("latin1").decode("utf-8")
        )
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    # Windows-1252 catches curly quotes and related corruption.
    try:
        candidates.append(
            text.encode("cp1252").decode("utf-8")
        )
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    def corruption_score(value: str) -> int:
        score = 0

        # Replacement character is strongly negative.
        score += value.count("�") * 20

        # Typical mojibake markers.
        for marker in MOJIBAKE_MARKERS:
            score += value.count(marker)

        # UTF-8 corruption often creates these sequences.
        for sequence in (
            "Ð°",
            "Ðµ",
            "Ð¾",
            "Ð¸",
            "Ð°",
            "Ñ‚",
            "Ñ‹",
            "ÑŒ",
            "Ñ‹",
            "â€™",
            "â€œ",
            "â€",
        ):
            score += value.count(sequence) * 2

        return score

    best = min(candidates, key=corruption_score)

    return best


def normalize_unicode(text: Any) -> str:
    """Normalize Unicode without destroying Cyrillic or accented characters."""

    if text is None:
        return ""

    text = repair_mojibake(text)

    try:
        text = unicodedata.normalize("NFKC", text)
    except (TypeError, ValueError):
        text = str(text)

    return text


def clean_text(text: Any) -> str:
    """
    Main text-cleaning pipeline.

    Important:
    We repair encoding BEFORE tokenization/scoring.
    """

    text = normalize_unicode(text)

    if not text:
        return ""

    # Decode HTML entities.
    text = html.unescape(text)

    # Normalize non-breaking spaces and invisible separators.
    text = (
        text.replace("\xa0", " ")
        .replace("\u200b", "")
        .replace("\u200c", "")
        .replace("\u200d", "")
        .replace("\ufeff", "")
    )

    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_title(text: Any) -> str:
    """Clean a title while preserving useful punctuation."""

    text = clean_text(text)

    # Titles should not contain trailing whitespace.
    return text.strip()


# ---------------------------------------------------------------------------
# RESPONSE DECODING
# ---------------------------------------------------------------------------

def _extract_charset_from_content_type(content_type: str) -> Optional[str]:
    """Extract charset=... from Content-Type."""

    if not content_type:
        return None

    match = re.search(
        r"charset\s*=\s*[\"']?\s*([A-Za-z0-9._:-]+)",
        content_type,
        flags=re.I,
    )

    if not match:
        return None

    return match.group(1).strip()


def _extract_charset_from_html(data: bytes) -> Optional[str]:
    """Look for a charset declaration inside HTML bytes."""

    if not data:
        return None

    sample = data[:10000].decode(
        "ascii",
        errors="ignore",
    )

    patterns = [
        r'<meta[^>]+charset=["\']?\s*([A-Za-z0-9._:-]+)',
        r'<meta[^>]+content=["\'][^"\']*charset\s*=\s*([A-Za-z0-9._:-]+)',
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            sample,
            flags=re.I,
        )
        if match:
            return match.group(1).strip()

    return None


def decode_response(response: requests.Response) -> str:
    """
    Decode response bytes robustly.

    Priority:

    1. explicit HTTP charset
    2. HTML meta charset
    3. UTF-8
    4. requests apparent encoding
    5. cp1251
    6. cp1252
    7. latin-1

    Then repair any remaining mojibake.
    """

    data = response.content

    if not data:
        return ""

    candidates: List[str] = []

    declared = _extract_charset_from_content_type(
        response.headers.get("Content-Type", "")
    )

    html_charset = _extract_charset_from_html(data)

    encodings: List[str] = []

    for encoding in (
        declared,
        html_charset,
        "utf-8",
        response.apparent_encoding,
        "cp1251",
        "cp1252",
        "latin-1",
    ):
        if not encoding:
            continue

        encoding = encoding.lower().strip()

        if encoding not in encodings:
            encodings.append(encoding)

    for encoding in encodings:
        try:
            decoded = data.decode(
                encoding,
                errors="strict",
            )
            candidates.append(decoded)
        except (LookupError, UnicodeDecodeError):
            continue

    if not candidates:
        decoded = data.decode(
            "utf-8",
            errors="replace",
        )
    else:

        def decode_quality(value: str) -> int:
            score = 0

            score += value.count("�") * 30

            # Penalize obvious mojibake.
            for marker in MOJIBAKE_MARKERS:
                score += value.count(marker)

            # Reward Cyrillic when it is actually present.
            cyrillic = sum(
                1
                for char in value
                if "CYRILLIC" in unicodedata.name(
                    char,
                    "",
                )
            )

            if cyrillic:
                score -= min(cyrillic, 50)

            return score

        decoded = min(
            candidates,
            key=decode_quality,
        )

    return repair_mojibake(decoded)


# ---------------------------------------------------------------------------
# HTTP FETCH
# ---------------------------------------------------------------------------

def fetch_url(
    url: str,
    source: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Fetch a URL and return structured result."""

    headers = dict(DEFAULT_HEADERS)

    if source:
        source_headers = source.get("headers", {})
        if isinstance(source_headers, dict):
            headers.update(source_headers)

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        text = decode_response(response)

        return {
            "ok": response.ok,
            "status": response.status_code,
            "url": response.url,
            "text": text,
            "error": None,
        }

    except requests.RequestException as exc:
        return {
            "ok": False,
            "status": None,
            "url": url,
            "text": "",
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# DATES
# ---------------------------------------------------------------------------

DATE_FORMATS = (
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%d/%m/%Y",
)


def parse_date(value: Any) -> Optional[datetime]:
    """Parse common RSS / HTML date formats."""

    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
    else:
        value = clean_text(value)

        if not value:
            return None

        # ISO 8601.
        try:
            normalized = value.replace(
                "Z",
                "+00:00",
            )

            dt = datetime.fromisoformat(normalized)

        except ValueError:

            dt = None

            for fmt in DATE_FORMATS:
                try:
                    dt = datetime.strptime(
                        value,
                        fmt,
                    )
                    break
                except ValueError:
                    continue

            if dt is None:
                return None

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc,
        )

    return dt.astimezone(timezone.utc)


def extract_date_from_container(
    container: Any,
) -> Optional[datetime]:
    """Extract date from common HTML structures."""

    if container is None:
        return None

    # <time datetime="...">
    time_tag = container.find("time")

    if time_tag:
        for attr in (
            "datetime",
            "content",
        ):
            value = time_tag.get(attr)

            parsed = parse_date(value)

            if parsed:
                return parsed

        parsed = parse_date(
            time_tag.get_text(
                " ",
                strip=True,
            )
        )

        if parsed:
            return parsed

    # itemprop=datePublished etc.
    for tag in container.find_all(
        attrs={
            "itemprop": re.compile(
                r"datePublished|dateModified",
                re.I,
            )
        }
    ):
        for attr in (
            "content",
            "datetime",
        ):
            parsed = parse_date(
                tag.get(attr)
            )

            if parsed:
                return parsed

        parsed = parse_date(
            tag.get_text(
                " ",
                strip=True,
            )
        )

        if parsed:
            return parsed

    # Common class names.
    date_pattern = re.compile(
        r"(date|time|published|publish|created|timestamp)",
        re.I,
    )

    for tag in container.find_all(
        class_=date_pattern
    ):
        parsed = parse_date(
            tag.get_text(
                " ",
                strip=True,
            )
        )

        if parsed:
            return parsed

    return None


# ---------------------------------------------------------------------------
# URL HELPERS
# ---------------------------------------------------------------------------

BAD_URL_PARTS = (
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
)


def absolute_url(
    base_url: str,
    url: str,
) -> str:
    """Make a URL absolute."""

    if not url:
        return ""

    return urljoin(
        base_url,
        url.strip(),
    )


def is_probable_article_url(
    url: str,
) -> bool:
    """Reject obvious non-article URLs."""

    if not url:
        return False

    lowered = url.lower()

    if lowered.startswith(
        (
            "javascript:",
            "mailto:",
            "#",
        )
    ):
        return False

    parsed = urlparse(url)

    if parsed.scheme not in (
        "http",
        "https",
    ):
        return False

    path = parsed.path.lower()

    if any(
        part in path
        for part in BAD_URL_PARTS
    ):
        return False

    # WordPress-style pagination.
    if re.search(
        r"/page/\d+/?$",
        path,
    ):
        return False

    return True


def normalize_url(url: str) -> str:
    """Normalize URLs for deduplication."""

    if not url:
        return ""

    parsed = urlparse(url)

    query = []

    for key, value in parse_qsl(
        parsed.query,
        keep_blank_values=True,
    ):
        key_lower = key.lower()

        if key_lower in {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
            "mc_cid",
            "mc_eid",
        }:
            continue

        query.append(
            (key, value)
        )

    normalized_query = urlencode(
        sorted(query)
    )

    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        fragment="",
        query=normalized_query,
    )

    return urlunparse(normalized).rstrip("/")


# ---------------------------------------------------------------------------
# ARTICLE OBJECT
# ---------------------------------------------------------------------------

def build_article(
    *,
    title: str,
    url: str,
    summary: str = "",
    body: str = "",
    published: Optional[datetime] = None,
    source: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a normalized article object."""

    source = source or {}

    title = clean_title(title)
    summary = clean_text(summary)
    body = clean_text(body)

    return {
        "title": title,
        "url": normalize_url(url),
        "summary": summary,
        "body": body,
        "date": (
            published.isoformat()
            if published
            else None
        ),
        "source": source.get(
            "name",
            source.get("id", ""),
        ),
        "source_short": source.get(
            "short",
            "",
        ),
        "source_profile": source.get(
            "profile",
            "",
        ),
        "source_label": source.get(
            "label",
            source.get(
                "name",
                source.get("id", ""),
            ),
        ),
    }


# ---------------------------------------------------------------------------
# RSS / ATOM
# ---------------------------------------------------------------------------

def parse_feed(
    text: str,
    source: Dict[str, Any],
    base_url: str = "",
) -> List[Dict[str, Any]]:
    """Parse an RSS/Atom feed from already decoded text."""

    if not text:
        return []

    parsed = feedparser.parse(text)

    articles: List[Dict[str, Any]] = []

    for entry in parsed.entries[:MAX_FEED_ENTRIES]:

        title = clean_title(
            entry.get(
                "title",
                "",
            )
        )

        link = entry.get(
            "link",
            "",
        )

        link = absolute_url(
            base_url,
            link,
        )

        if not title or not link:
            continue

        if not is_probable_article_url(link):
            continue

        summary = (
            entry.get("summary")
            or entry.get("description")
            or ""
        )

        published = None

        for key in (
            "published_parsed",
            "updated_parsed",
        ):
            value = entry.get(key)

            if value:
                try:
                    published = datetime(
                        *value[:6],
                        tzinfo=timezone.utc,
                    )
                    break
                except (TypeError, ValueError):
                    pass

        if published is None:
            for key in (
                "published",
                "updated",
            ):
                published = parse_date(
                    entry.get(key)
                )

                if published:
                    break

        article = build_article(
            title=title,
            url=link,
            summary=summary,
            body="",
            published=published,
            source=source,
        )

        articles.append(article)

    return articles


# ---------------------------------------------------------------------------
# HTML PARSING
# ---------------------------------------------------------------------------

ARTICLE_CONTAINER_SELECTORS = (
    "article",
    "[itemtype*='Article']",
    "[itemtype*='NewsArticle']",
    ".article",
    ".article-card",
    ".post",
    ".post-card",
    ".story",
    ".story-card",
    ".news-item",
    ".news-card",
    ".item",
)


def extract_article_from_container(
    container: Any,
    source: Dict[str, Any],
    base_url: str,
) -> Optional[Dict[str, Any]]:
    """Extract one article candidate from an HTML container."""

    if container is None:
        return None

    links = container.find_all("a", href=True)

    candidates: List[Tuple[str, str]] = []

    for link in links:

        title = clean_title(
            link.get_text(
                " ",
                strip=True,
            )
        )

        href = absolute_url(
            base_url,
            link.get("href", ""),
        )

        if (
            len(title) >= 20
            and is_probable_article_url(href)
        ):
            candidates.append(
                (title, href)
            )

    if not candidates:
        return None

    # Prefer the longest meaningful title.
    title, url = max(
        candidates,
        key=lambda item: len(item[0]),
    )

    paragraphs = []

    for paragraph in container.find_all("p"):
        value = clean_text(
            paragraph.get_text(
                " ",
                strip=True,
            )
        )

        if len(value) >= 40:
            paragraphs.append(value)

    summary = " ".join(
        paragraphs[:3]
    )

    published = extract_date_from_container(
        container
    )

    return build_article(
        title=title,
        url=url,
        summary=summary,
        body="",
        published=published,
        source=source,
    )


def parse_html_source(
    text: str,
    source: Dict[str, Any],
    base_url: str,
) -> List[Dict[str, Any]]:
    """Parse an HTML source page."""

    if not text:
        return []

    soup = BeautifulSoup(
        text,
        "html.parser",
    )

    articles: List[Dict[str, Any]] = []

    seen_urls = set()

    containers = []

    for selector in ARTICLE_CONTAINER_SELECTORS:
        try:
            containers.extend(
                soup.select(selector)
            )
        except Exception:
            continue

    for container in containers:

        article = extract_article_from_container(
            container,
            source,
            base_url,
        )

        if not article:
            continue

        url = article["url"]

        if url in seen_urls:
            continue

        seen_urls.add(url)

        articles.append(article)

        if len(articles) >= MAX_HTML_ARTICLES:
            break

    # Fallback: scan links if article containers failed.
    if not articles:

        for link in soup.find_all(
            "a",
            href=True,
        ):

            title = clean_title(
                link.get_text(
                    " ",
                    strip=True,
                )
            )

            href = absolute_url(
                base_url,
                link.get("href", ""),
            )

            if (
                len(title) < 25
                or not is_probable_article_url(href)
            ):
                continue

            normalized = normalize_url(href)

            if normalized in seen_urls:
                continue

            seen_urls.add(normalized)

            articles.append(
                build_article(
                    title=title,
                    url=href,
                    summary="",
                    body="",
                    published=None,
                    source=source,
                )
            )

            if len(articles) >= MAX_HTML_ARTICLES:
                break

    return articles


# ---------------------------------------------------------------------------
# ARTICLE BODY EXTRACTION
# ---------------------------------------------------------------------------

REMOVE_SELECTORS = (
    "script",
    "style",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "noscript",
    "iframe",
    "svg",
    "button",
)


def extract_article_body(
    text: str,
) -> str:
    """
    Extract readable article text.

    This function intentionally does not attempt semantic interpretation.
    Its job is simply to feed clean text to scoring.py.
    """

    if not text:
        return ""

    soup = BeautifulSoup(
        text,
        "html.parser",
    )

    for selector in REMOVE_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()

    candidates = []

    # Strong semantic containers first.
    for selector in (
        "article",
        "main",
        "[role='main']",
    ):
        for container in soup.select(selector):

            paragraphs = []

            for paragraph in container.find_all("p"):
                value = clean_text(
                    paragraph.get_text(
                        " ",
                        strip=True,
                    )
                )

                if len(value) >= 30:
                    paragraphs.append(value)

            if paragraphs:
                candidates.append(
                    " ".join(paragraphs)
                )

    # Generic paragraph fallback.
    if not candidates:

        paragraphs = []

        for paragraph in soup.find_all("p"):
            value = clean_text(
                paragraph.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(value) >= 30:
                paragraphs.append(value)

        if paragraphs:
            candidates.append(
                " ".join(paragraphs)
            )

    if not candidates:
        return ""

    body = max(
        candidates,
        key=len,
    )

    # Prevent pathological pages.
    return body[:20000]


# ---------------------------------------------------------------------------
# DEDUPLICATION
# ---------------------------------------------------------------------------

def normalize_title_for_dedup(
    title: str,
) -> str:
    """Normalize titles for duplicate detection."""

    title = clean_title(title).lower()

    title = re.sub(
        r"[^\w\s]",
        " ",
        title,
        flags=re.UNICODE,
    )

    title = re.sub(
        r"\s+",
        " ",
        title,
    )

    return title.strip()


def deduplicate_articles(
    articles: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Deduplicate by URL and normalized title."""

    result = []

    seen_urls = set()
    seen_titles = set()

    for article in articles:

        if not isinstance(article, dict):
            continue

        url = normalize_url(
            article.get("url", "")
        )

        title = normalize_title_for_dedup(
            article.get("title", "")
        )

        if not title:
            continue

        if url and url in seen_urls:
            continue

        if title in seen_titles:
            continue

        if url:
            seen_urls.add(url)

        seen_titles.add(title)

        article["url"] = url
        article["title"] = clean_title(
            article.get("title", "")
        )
        article["summary"] = clean_text(
            article.get("summary", "")
        )
        article["body"] = clean_text(
            article.get("body", "")
        )

        result.append(article)

    return result


# ---------------------------------------------------------------------------
# SOURCE HANDLING
# ---------------------------------------------------------------------------

def source_is_enabled(
    source: Dict[str, Any],
) -> bool:
    """Check whether a source is enabled."""

    if source.get("enabled", True) is False:
        return False

    return True


def source_url(
    source: Dict[str, Any],
) -> str:
    """Get source URL from supported field names."""

    return (
        source.get("rss")
        or source.get("feed")
        or source.get("url")
        or source.get("homepage")
        or ""
    )


def source_type(
    source: Dict[str, Any],
) -> str:
    """Determine RSS vs HTML source."""

    value = (
        source.get("type")
        or source.get("format")
        or ""
    )

    return str(value).lower().strip()


# ---------------------------------------------------------------------------
# CACHE
# ---------------------------------------------------------------------------

_SOURCE_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}


def get_cached_source(
    key: str,
) -> Optional[List[Dict[str, Any]]]:
    """Return cached source if still valid."""

    cached = _SOURCE_CACHE.get(key)

    if not cached:
        return None

    timestamp, articles = cached

    if time.time() - timestamp > CACHE_TTL_SECONDS:
        return None

    return articles


def set_cached_source(
    key: str,
    articles: List[Dict[str, Any]],
) -> None:
    """Cache source results."""

    _SOURCE_CACHE[key] = (
        time.time(),
        articles,
    )


# ---------------------------------------------------------------------------
# SOURCE SCANNING
# ---------------------------------------------------------------------------

def collect_from_source(
    source: Dict[str, Any],
    force_refresh: bool = False,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Collect articles from one source."""

    name = source.get(
        "name",
        source.get("id", "unknown"),
    )

    url = source_url(source)

    stats = {
        "source": name,
        "attempted": 0,
        "success": 0,
        "articles": 0,
        "error": None,
        "cached": False,
    }

    if not url:
        stats["error"] = "No URL configured"
        return [], stats

    cache_key = normalize_url(url)

    if not force_refresh:
        cached = get_cached_source(
            cache_key
        )

        if cached is not None:
            stats["cached"] = True
            stats["success"] = 1
            stats["articles"] = len(cached)
            return list(cached), stats

    stats["attempted"] = 1

    result = fetch_url(
        url,
        source=source,
    )

    if not result["ok"]:
        stats["error"] = result.get(
            "error"
        ) or f"HTTP {result.get('status')}"

        logging.warning(
            "SOURCE | %s | ERROR | %s",
            name,
            stats["error"],
        )

        return [], stats

    text = result.get(
        "text",
        "",
    )

    if not text:
        stats["error"] = "Empty response"

        logging.warning(
            "SOURCE | %s | EMPTY",
            name,
        )

        return [], stats

    source_kind = source_type(
        source
    )

    if (
        source_kind in {
            "rss",
            "atom",
            "feed",
            "xml",
        }
        or "rss" in url.lower()
        or "feed" in url.lower()
        or "atom" in url.lower()
    ):
        articles = parse_feed(
            text,
            source,
            result.get("url", url),
        )

    else:
        articles = parse_html_source(
            text,
            source,
            result.get("url", url),
        )

    set_cached_source(
        cache_key,
        articles,
    )

    stats["success"] = 1
    stats["articles"] = len(articles)

    logging.info(
        "SOURCE | %s | %d articles",
        name,
        len(articles),
    )

    return articles, stats


def collect_articles(
    force_refresh: bool = False,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Collect all enabled sources."""

    all_articles: List[Dict[str, Any]] = []
    source_stats: List[Dict[str, Any]] = []

    enabled_sources = [
        source
        for source in SOURCES
        if isinstance(source, dict)
        and source_is_enabled(source)
    ]

    logging.info(
        "SOURCES | %d sources actives",
        len(enabled_sources),
    )

    for source in enabled_sources:

        articles, stats = collect_from_source(
            source,
            force_refresh=force_refresh,
        )

        all_articles.extend(
            articles
        )

        source_stats.append(stats)

    logging.info(
        "COLLECT | %d articles avant déduplication",
        len(all_articles),
    )

    return (
        all_articles,
        source_stats,
    )


# ---------------------------------------------------------------------------
# TITLE VOCABULARY
# ---------------------------------------------------------------------------

TITLE_STOPWORDS = {
    # English
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "for",
    "with",
    "from",
    "into",
    "after",
    "before",
    "over",
    "under",
    "about",
    "between",
    "against",
    "amid",
    "says",
    "said",
    "new",
    "latest",
    "report",
    "reports",
    "news",

    # French
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
    "dans",
    "sur",
    "pour",
    "avec",
    "après",
    "avant",
    "entre",
    "contre",
    "nouveau",
    "nouvelle",
    "nouvelles",

    # Russian
    "и",
    "или",
    "в",
    "во",
    "на",
    "с",
    "со",
    "для",
    "по",
    "из",
    "от",
    "до",
    "после",
    "как",
    "что",
    "это",
    "новый",
    "новая",
    "новые",
    "новости",
    "сообщает",
    "сообщили",
}


def extract_title_words(
    title: str,
) -> List[str]:
    """
    Unicode-aware word tokenizer.

    Important:
    This works with Latin AND Cyrillic.
    """

    title = clean_title(title)

    if not title:
        return []

    words = re.findall(
        r"[^\W\d_]+(?:['’\-][^\W\d_]+)*",
        title,
        flags=re.UNICODE,
    )

    result = []

    for word in words:

        word = word.strip(
            "'’-"
        ).lower()

        if not word:
            continue

        if word in TITLE_STOPWORDS:
            continue

        # Ignore extremely short fragments.
        if len(word) < 2:
            continue

        result.append(word)

    return result


def build_title_word_list(
    articles: Iterable[Dict[str, Any]],
    min_count: int = TITLE_VOCAB_MIN_COUNT,
    max_words: int = TITLE_VOCAB_MAX_WORDS,
) -> List[Dict[str, Any]]:
    """
    Build a vocabulary from article titles.

    This is diagnostic/discovery only.
    It does NOT modify scoring.
    """

    counts: Dict[str, int] = {}

    for article in articles:

        if not isinstance(article, dict):
            continue

        title = article.get(
            "title",
            "",
        )

        # clean_title repairs mojibake before tokenization.
        words = extract_title_words(
            title
        )

        for word in words:
            counts[word] = (
                counts.get(word, 0) + 1
            )

    items = [
        {
            "word": word,
            "count": count,
        }
        for word, count in counts.items()
        if count >= min_count
    ]

    items.sort(
        key=lambda item: (
            -item["count"],
            item["word"],
        )
    )

    return items[:max_words]


# ---------------------------------------------------------------------------
# SCORING
# ---------------------------------------------------------------------------

def prepare_article_for_scoring(
    article: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Make sure scoring.py receives clean Unicode.

    We intentionally do not alter the scoring logic here.
    """

    article["title"] = clean_title(
        article.get("title", "")
    )

    article["summary"] = clean_text(
        article.get("summary", "")
    )

    article["body"] = clean_text(
        article.get("body", "")
    )

    return article


def score_articles(
    articles: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Apply deterministic scoring."""

    scored = []

    for article in articles:

        article = prepare_article_for_scoring(
            article
        )

        try:
            article = classify_article(
                article
            )
        except Exception:
            logging.exception(
                "SCORING ERROR | %s",
                article.get(
                    "title",
                    "(sans titre)",
                ),
            )

            # Do not kill the complete scan because
            # one malformed article failed.
            article["score"] = 0
            article["level"] = "D"
            article["relevant"] = False

        scored.append(article)

    return scored


# ---------------------------------------------------------------------------
# FULL ARTICLE ENRICHMENT
# ---------------------------------------------------------------------------

def article_needs_body(
    article: Dict[str, Any],
) -> bool:
    """Determine whether full-body fetching is worthwhile."""

    score = article.get(
        "score",
        0,
    )

    try:
        score = float(score)
    except (TypeError, ValueError):
        score = 0

    return score > 0


def enrich_article_body(
    article: Dict[str, Any],
) -> Dict[str, Any]:
    """Fetch and extract the full article body."""

    url = article.get(
        "url",
        "",
    )

    if not url:
        return article

    source_name = article.get(
        "source",
        "",
    )

    result = fetch_url(
        url
    )

    if not result["ok"]:
        logging.debug(
            "ARTICLE | body fetch failed | %s | %s",
            source_name,
            url,
        )

        return article

    body = extract_article_body(
        result.get(
            "text",
            "",
        )
    )

    if body:
        article["body"] = body

    return prepare_article_for_scoring(
        article
    )


def enrich_top_articles(
    articles: List[Dict[str, Any]],
    limit: int = ARTICLE_PAGE_FETCH_LIMIT,
) -> List[Dict[str, Any]]:
    """
    Fetch full bodies only for the most promising articles.

    First-pass scoring uses title + summary.
    Then top candidates receive full-body scoring.
    """

    ranked = sorted(
        articles,
        key=lambda article: (
            float(
                article.get(
                    "score",
                    0,
                ) or 0
            ),
            article.get(
                "date",
                "",
            ) or "",
        ),
        reverse=True,
    )

    candidates = [
        article
        for article in ranked
        if article_needs_body(article)
    ][:limit]

    logging.info(
        "ENRICH | %d articles avec body complet",
        len(candidates),
    )

    candidate_ids = {
        id(article)
        for article in candidates
    }

    for index, article in enumerate(
        candidates,
        start=1,
    ):

        logging.info(
            "ENRICH | %d/%d | %s",
            index,
            len(candidates),
            article.get(
                "title",
                "(sans titre)",
            )[:100],
        )

        enrich_article_body(
            article
        )

    # Re-score everything because enriched candidates changed.
    return score_articles(
        articles
    )


# ---------------------------------------------------------------------------
# RANKING
# ---------------------------------------------------------------------------

LEVEL_ORDER = {
    "A": 0,
    "B": 1,
    "C": 2,
    "D": 3,
}


def article_date_timestamp(
    article: Dict[str, Any],
) -> float:
    """Return publication timestamp for sorting."""

    value = article.get(
        "date"
    )

    parsed = parse_date(value)

    if not parsed:
        return 0

    return parsed.timestamp()


def sort_articles(
    articles: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Sort by level, score, then freshness."""

    return sorted(
        articles,
        key=lambda article: (
            LEVEL_ORDER.get(
                article.get(
                    "level",
                    "D",
                ),
                3,
            ),
            -float(
                article.get(
                    "score",
                    0,
                ) or 0
            ),
            -article_date_timestamp(
                article
            ),
        ),
    )


# ---------------------------------------------------------------------------
# STATISTICS
# ---------------------------------------------------------------------------

def build_stats(
    articles: List[Dict[str, Any]],
    source_stats: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build dashboard statistics."""

    scores = []

    levels = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    }

    relevant = 0

    for article in articles:

        try:
            score = float(
                article.get(
                    "score",
                    0,
                ) or 0
            )
        except (TypeError, ValueError):
            score = 0

        scores.append(score)

        level = article.get(
            "level",
            "D",
        )

        if level in levels:
            levels[level] += 1

        if article.get(
            "relevant",
            False,
        ):
            relevant += 1

    average_score = (
        sum(scores) / len(scores)
        if scores
        else 0
    )

    return {
        "analyzed": len(articles),
        "retained": relevant,
        "avg_score": round(
            average_score,
            1,
        ),
        "levels": levels,
        "source_stats": source_stats,
        "relevance_rate": round(
            (
                relevant / len(articles) * 100
                if articles
                else 0
            ),
            1,
        ),
    }


# ---------------------------------------------------------------------------
# MEMORY
# ---------------------------------------------------------------------------

def show_memory(
    memory: Any,
) -> None:
    """
    Memory is optional.

    Empty memory is completely normal.
    No memory-related error can stop the scanner.
    """

    if not memory:
        logging.info(
            "MEMORY | vide — ignorée"
        )
        return

    if isinstance(memory, list):
        articles = memory

    elif isinstance(memory, dict):
        articles = (
            memory.get("articles")
            or memory.get("items")
            or memory.get("history")
            or []
        )

    else:
        logging.warning(
            "MEMORY | format inattendu (%s) — ignorée",
            type(memory).__name__,
        )
        return

    if not isinstance(
        articles,
        list,
    ) or not articles:

        logging.info(
            "MEMORY | vide — ignorée"
        )
        return

    logging.info(
        "MEMORY | %d articles connus",
        len(articles),
    )

    for article in articles[-10:]:

        if not isinstance(
            article,
            dict,
        ):
            continue

        logging.info(
            "  • %s | score=%s",
            article.get(
                "title",
                "(sans titre)",
            )[:100],
            article.get(
                "score",
                "?",
            ),
        )


def safe_load_memory() -> Any:
    """
    Load memory without ever making it a hard dependency.

    If the memory module/file is broken, scanning continues.
    """

    try:
        memory = load_memory()
    except Exception:
        logging.exception(
            "MEMORY | impossible à charger — scan poursuivi"
        )
        return {}

    if memory is None:
        return {}

    return memory


def safe_save_memory(
    articles: List[Dict[str, Any]],
) -> None:
    """
    Save memory if available.

    Failure is logged but does not kill the scan.
    """

    try:
        save_memory(
            articles
        )
    except Exception:
        logging.exception(
            "MEMORY | sauvegarde impossible — scan terminé malgré tout"
        )


# ---------------------------------------------------------------------------
# RELEVANCE
# ---------------------------------------------------------------------------

def is_relevant_article(
    article: Dict[str, Any],
) -> bool:
    """Final relevance check."""

    if article.get(
        "relevant",
        False,
    ):
        return True

    score = article.get(
        "score",
        0,
    )

    try:
        score = float(score)
    except (TypeError, ValueError):
        score = 0

    return (
        score >= 40
        and not article.get(
            "non_news",
            False,
        )
        and not article.get(
            "noise",
            False,
        )
    )


# ---------------------------------------------------------------------------
# MAIN SCAN
# ---------------------------------------------------------------------------

def scan_news(
    force_refresh: bool = False,
    memory_enabled: bool = True,
) -> Dict[str, Any]:

    logging.info("=" * 50)
    logging.info(
        "CENTRAL ASIA NEWS SCANNER"
    )
    logging.info("=" * 50)

    # ---------------------------------------------------------------
    # MEMORY
    # ---------------------------------------------------------------

    memory = {}

    if memory_enabled:
        memory = safe_load_memory()
        show_memory(memory)
    else:
        logging.info(
            "MEMORY | désactivée"
        )

    # ---------------------------------------------------------------
    # COLLECTION
    # ---------------------------------------------------------------

    articles, source_stats = collect_articles(
        force_refresh=force_refresh
    )

    logging.info(
        "COLLECT | %d articles récupérés",
        len(articles),
    )

    # ---------------------------------------------------------------
    # DEDUP
    # ---------------------------------------------------------------

    articles = deduplicate_articles(
        articles
    )

    logging.info(
        "DEDUP | %d articles uniques",
        len(articles),
    )

    if not articles:
        logging.warning(
            "SCAN | aucun article récupéré"
        )

        stats = build_stats(
            [],
            source_stats,
        )

        try:
            create_web_page(
                [],
                [],
                stats,
                [],
            )
        except Exception:
            logging.exception(
                "HTML | génération impossible"
            )

        return {
            "articles": [],
            "audit": [],
            "stats": stats,
        }

    # ---------------------------------------------------------------
    # FIRST PASS SCORING
    # ---------------------------------------------------------------

    logging.info(
        "SCORING | première passe title + summary"
    )

    articles = score_articles(
        articles
    )

    first_pass = sort_articles(
        articles
    )

    # ---------------------------------------------------------------
    # FULL BODY FOR TOP CANDIDATES
    # ---------------------------------------------------------------

    articles = enrich_top_articles(
        articles,
        limit=ARTICLE_PAGE_FETCH_LIMIT,
    )

    # ---------------------------------------------------------------
    # FINAL SORT
    # ---------------------------------------------------------------

    sorted_audit = sort_articles(
        articles
    )

    # ---------------------------------------------------------------
    # RELEVANT SELECTION
    # ---------------------------------------------------------------

    relevant_articles = [
        article
        for article in sorted_audit
        if is_relevant_article(
            article
        )
    ]

    selected = relevant_articles[
        :ARTICLES_TO_DISPLAY
    ]

    # ---------------------------------------------------------------
    # STATISTICS
    # ---------------------------------------------------------------

    stats = build_stats(
        sorted_audit,
        source_stats,
    )

    logging.info(
        "STATS | analyzed=%d | retained=%d | avg=%.1f/100",
        stats["analyzed"],
        stats["retained"],
        stats["avg_score"],
    )

    logging.info(
        "LEVELS | A=%d B=%d C=%d D=%d",
        stats["levels"]["A"],
        stats["levels"]["B"],
        stats["levels"]["C"],
        stats["levels"]["D"],
    )

    # ---------------------------------------------------------------
    # TITLE VOCABULARY
    # ---------------------------------------------------------------

    title_words = build_title_word_list(
        sorted_audit,
        min_count=TITLE_VOCAB_MIN_COUNT,
        max_words=TITLE_VOCAB_MAX_WORDS,
    )

    logging.info(
        "VOCABULARY | %d mots de titres",
        len(title_words),
    )

    # ---------------------------------------------------------------
    # MEMORY
    # ---------------------------------------------------------------

    if memory_enabled:
        # For now we keep this deliberately conservative.
        # The memory system is not part of scoring.
        safe_save_memory(
            selected
        )

    # ---------------------------------------------------------------
    # HTML
    # ---------------------------------------------------------------

    try:
        create_web_page(
            selected,
            sorted_audit,
            stats,
            title_words,
        )

        logging.info(
            "HTML | page générée"
        )

    except Exception:
        logging.exception(
            "HTML | erreur pendant la génération"
        )

    logging.info(
        "SCAN | terminé | %d articles sélectionnés",
        len(selected),
    )

    return {
        "articles": selected,
        "audit": sorted_audit,
        "stats": stats,
        "title_words": title_words,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Central Asia News Scanner"
        )
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help=(
            "Force un scan frais des sources"
        ),
    )

    parser.add_argument(
        "--memory",
        action="store_true",
        help=(
            "Active la mémoire optionnelle"
        ),
    )

    parser.add_argument(
        "--no-memory",
        action="store_true",
        help=(
            "Désactive complètement la mémoire"
        ),
    )

    return parser


def main() -> None:

    parser = build_parser()
    args = parser.parse_args()

    # ---------------------------------------------------------------
    # MEMORY MODE
    # ---------------------------------------------------------------

    if args.no_memory:
        memory_enabled = False

    elif args.memory:
        memory_enabled = True

    else:
        # Default: memory remains optional.
        # It may be loaded if the project has one, but an empty
        # memory is harmless.
        memory_enabled = True

    # ---------------------------------------------------------------
    # REFRESH MODE
    # ---------------------------------------------------------------

    # Explicit --scan means:
    # do not use the one-hour source cache.
    force_refresh = bool(
        args.scan
    )

    try:
        scan_news(
            force_refresh=force_refresh,
            memory_enabled=memory_enabled,
        )

    except KeyboardInterrupt:
        logging.warning(
            "SCAN | interrompu"
        )
        sys.exit(130)

    except Exception:
        logging.exception(
            "SCAN | erreur fatale"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
