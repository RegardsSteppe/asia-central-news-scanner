from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import feedparser
from bs4 import BeautifulSoup

from http_utils import (
    CACHE_TTL,
    HEADERS,
    REQUEST_TIMEOUT,
    fetch_url,
)
from text_utils import (
    clean_text,
    clean_title,
    normalize_url,
    parse_date,
)


def parse_rss(content: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    feed = feedparser.parse(content)

    articles: list[dict[str, Any]] = []

    for entry in feed.entries:
        title = clean_title(entry.get("title", ""))
        summary = clean_text(
            entry.get("summary")
            or entry.get("description")
            or ""
        )

        link = entry.get("link", "")
        if not title or not link:
            continue

        articles.append(
            build_article(
                source=source,
                title=title,
                summary=summary,
                url=link,
                published=entry.get("published")
                or entry.get("updated")
                or entry.get("created"),
            )
        )

    return articles


def extract_links_from_html(
    content: str,
    base_url: str,
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    soup = BeautifulSoup(content, "html.parser")
    articles: list[dict[str, Any]] = []

    for link in soup.find_all("a", href=True):
        href = urljoin(base_url, link.get("href", ""))
        title = clean_title(link.get_text(" ", strip=True))

        if not title or not href:
            continue

        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"}:
            continue

        articles.append(
            build_article(
                source=source,
                title=title,
                summary="",
                url=href,
                published=None,
            )
        )

    return articles


def extract_body(content: str, url: str) -> str:
    soup = BeautifulSoup(content, "html.parser")

    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "header",
            "footer",
        ]
    ):
        tag.decompose()

    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=lambda value: value and "article" in str(value).lower())
    )

    if main:
        text = main.get_text(" ", strip=True)
    else:
        text = soup.get_text(" ", strip=True)

    return clean_text(text)


def build_article(
    source: dict[str, Any],
    title: str,
    summary: str,
    url: str,
    published: Any,
) -> dict[str, Any]:
    return {
        "source": source.get("name", ""),
        "source_label": source.get("label") or source.get("name", ""),
        "title": clean_title(title),
        "summary": clean_text(summary),
        "url": normalize_url(url),
        "date": parse_date(published),
        "body": "",
    }


# ---------------------------------------------------------------------------
# DIAGNOSTICS
# ---------------------------------------------------------------------------

def diagnose_content(content: str) -> dict[str, Any]:
    """
    Retourne uniquement des informations de diagnostic.
    Ne modifie pas le contenu et ne change pas le comportement du scanner.
    """
    content = content or ""

    stripped = content.lstrip().lower()

    looks_like_xml = (
        stripped.startswith("<?xml")
        or "<rss" in stripped[:1000]
        or "<feed" in stripped[:1000]
    )

    looks_like_html = (
        "<html" in stripped[:2000]
        or "<!doctype html" in stripped[:2000]
    )

    return {
        "bytes": len(content.encode("utf-8", errors="ignore")),
        "characters": len(content),
        "looks_like_xml": looks_like_xml,
        "looks_like_html": looks_like_html,
        "has_title_tag": "<title" in stripped,
        "has_article_tag": "<article" in stripped,
        "has_main_tag": "<main" in stripped,
    }


def diagnose_rss(
    content: str,
    source: dict[str, Any],
) -> dict[str, Any]:
    """
    Analyse un flux RSS/Atom sans modifier parse_rss().
    """
    feed = feedparser.parse(content)

    bozo = bool(getattr(feed, "bozo", False))
    bozo_exception = getattr(feed, "bozo_exception", None)

    return {
        "source": source.get("name", ""),
        "entries": len(feed.entries),
        "bozo": bozo,
        "bozo_exception": (
            str(bozo_exception)
            if bozo_exception
            else ""
        ),
        "feed_title": str(
            feed.feed.get("title", "")
        ),
    }


def diagnose_html_links(
    content: str,
    base_url: str,
) -> dict[str, Any]:
    """
    Compte les liens HTML et donne quelques exemples.
    """
    soup = BeautifulSoup(content, "html.parser")

    all_links = soup.find_all("a", href=True)

    valid_links = []
    examples = []

    for link in all_links:
        href = urljoin(base_url, link.get("href", ""))
        title = clean_title(link.get_text(" ", strip=True))

        parsed = urlparse(href)

        if parsed.scheme not in {"http", "https"}:
            continue

        valid_links.append(href)

        if title and len(examples) < 5:
            examples.append(
                {
                    "title": title[:120],
                    "url": href,
                }
            )

    return {
        "all_links": len(all_links),
        "valid_links": len(valid_links),
        "examples": examples,
    }


def diagnose_source_content(
    source: dict[str, Any],
    content: str,
    url: str,
) -> None:
    """
    Affiche un diagnostic lisible d'une source déjà téléchargée.
    """
    name = source.get("name", "")

    content_info = diagnose_content(content)

    print(
        f"DIAG | {name} | "
        f"bytes={content_info['bytes']} | "
        f"html={content_info['looks_like_html']} | "
        f"xml={content_info['looks_like_xml']}"
    )

    if content_info["looks_like_xml"]:
        rss_info = diagnose_rss(content, source)

        print(
            f"DIAG RSS | {name} | "
            f"entries={rss_info['entries']} | "
            f"bozo={rss_info['bozo']}"
        )

        if rss_info["bozo_exception"]:
            print(
                f"DIAG RSS ERROR | {name} | "
                f"{rss_info['bozo_exception']}"
            )

    if content_info["looks_like_html"]:
        html_info = diagnose_html_links(content, url)

        print(
            f"DIAG HTML | {name} | "
            f"links={html_info['all_links']} | "
            f"valid={html_info['valid_links']}"
        )

        for example in html_info["examples"]:
            print(
                f"DIAG LINK | {name} | "
                f"{example['title']} | "
                f"{example['url']}"
            )
