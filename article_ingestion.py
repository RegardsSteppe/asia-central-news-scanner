from __future__ import annotations

from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup
import feedparser

from text_utils import (
    clean_text,
    clean_title,
    normalize_url,
    parse_date,
)

from http_utils import fetch_url


# ============================================================
# CONFIGURATION HTTP
# ============================================================

CACHE_TTL = 3600

USER_AGENT = (
    "Mozilla/5.0 (compatible; CentralAsiaNewsScanner/1.0; "
    "+https://regardssteppe.github.io/asia-central-news-scanner/)"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": (
        "application/rss+xml, application/atom+xml, "
        "application/xml, text/xml, text/html;q=0.9, */*;q=0.8"
    ),
}

REQUEST_TIMEOUT = 25


# ============================================================
# EXTRACTION RSS
# ============================================================

def parse_rss(
    source: dict[str, Any],
    content: str,
) -> list[dict[str, Any]]:

    parsed = feedparser.parse(content)

    articles: list[dict[str, Any]] = []

    for entry in parsed.entries:
        title = clean_title(
            entry.get("title", "")
        )

        link = normalize_url(
            entry.get("link", ""),
            source.get("url", ""),
        )

        if not title or not link:
            continue

        summary = ""

        for key in (
            "summary",
            "description",
            "content",
        ):
            value = entry.get(key)

            if isinstance(value, list):
                parts = []

                for item in value:
                    if isinstance(item, dict):
                        parts.append(
                            item.get("value", "")
                        )
                    else:
                        parts.append(str(item))

                value = " ".join(parts)

            if value:
                summary = clean_text(value)
                break

        published = (
            parse_date(entry.get("published_parsed"))
            or parse_date(entry.get("updated_parsed"))
            or parse_date(entry.get("published"))
            or parse_date(entry.get("updated"))
        )

        articles.append(
            build_article(
                source=source,
                title=title,
                url=link,
                summary=summary,
                published=published,
            )
        )

    return articles


# ============================================================
# EXTRACTION HTML
# ============================================================

def extract_links_from_html(
    source: dict[str, Any],
    content: str,
) -> list[dict[str, Any]]:

    soup = BeautifulSoup(
        content,
        "html.parser",
    )

    articles: list[dict[str, Any]] = []

    selectors = source.get(
        "article_selector",
        "article a[href]",
    )

    try:
        links = soup.select(selectors)
    except Exception:
        links = soup.select("a[href]")

    seen_urls: set[str] = set()

    for link_tag in links:
        href = link_tag.get("href")

        if not href:
            continue

        url = normalize_url(
            href,
            source.get("url", ""),
        )

        if not url or url in seen_urls:
            continue

        title = clean_title(
            link_tag.get_text(
                " ",
                strip=True,
            )
        )

        if len(title) < 10:
            continue

        seen_urls.add(url)

        articles.append(
            build_article(
                source=source,
                title=title,
                url=url,
                summary="",
                published=None,
            )
        )

    return articles


# ============================================================
# BODY EXTRACTION
# ============================================================

def extract_body(
    url: str,
    source: dict[str, Any],
    force_refresh: bool = False,
) -> str:

    try:
        content = fetch_url(
            url,
            headers=HEADERS,
            request_timeout=REQUEST_TIMEOUT,
            cache_ttl=CACHE_TTL,
            force_refresh=force_refresh,
        )
    except Exception:
        return ""

    soup = BeautifulSoup(
        content,
        "html.parser",
    )

    # Suppression des éléments parasites.
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
            "header",
            "form",
            "aside",
        ]
    ):
        tag.decompose()

    selectors = []

    if source.get("body_selector"):
        selectors.append(
            source["body_selector"]
        )

    selectors.extend(
        [
            "article",
            "[itemprop='articleBody']",
            ".article-body",
            ".article-content",
            ".entry-content",
            ".post-content",
            "main",
        ]
    )

    body = ""

    for selector in selectors:
        try:
            node = soup.select_one(selector)
        except Exception:
            node = None

        if node:
            candidate = clean_text(
                node.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(candidate) > len(body):
                body = candidate

    if not body:
        body = clean_text(
            soup.get_text(
                " ",
                strip=True,
            )
        )

    return body


# ============================================================
# CONSTRUCTION ARTICLE
# ============================================================

def build_article(
    source: dict[str, Any],
    title: str,
    url: str,
    summary: str,
    published: datetime | None,
) -> dict[str, Any]:

    # IMPORTANT :
    # On conserve ici un datetime et NON une chaîne ISO.
    #
    # html_template.py appelle :
    #     date.strftime(...)
    #
    # C'est la correction principale du bug actuel.

    return {
        "source": clean_text(
            source.get("name", "Unknown")
        ),
        "source_url": normalize_url(
            source.get("url", "")
        ),
        "title": clean_title(title),
        "url": normalize_url(url),
        "summary": clean_text(summary),
        "body": "",
        "date": published,
        "score": 0,
        "level": "D",
        "priority": 0,
        "relevant": False,
        "signals": {},
    }
