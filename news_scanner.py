from __future__ import annotations

import argparse
import html
import json
import os
import re
import ssl
import time
import unicodedata
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import feedparser

from sources import SOURCES
from scoring import classify_article
from html_template import create_web_page


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MEMORY_FILE = BASE_DIR / "memory.json"
OUTPUT_FILE = BASE_DIR / "index.html"

CACHE_TTL = 3600
ENRICH_LIMIT = 80
VOCABULARY_LIMIT = 300

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
# CACHE MÉMOIRE
# ============================================================

_MEMORY_CACHE: dict[str, tuple[float, Any]] = {}


def cache_get(key: str) -> Any | None:
    item = _MEMORY_CACHE.get(key)

    if not item:
        return None

    timestamp, value = item

    if time.time() - timestamp > CACHE_TTL:
        _MEMORY_CACHE.pop(key, None)
        return None

    return value


def cache_set(key: str, value: Any) -> None:
    _MEMORY_CACHE[key] = (time.time(), value)


# ============================================================
# MOJIBAKE / NORMALISATION
# ============================================================

def repair_mojibake(text: Any) -> str:
    """
    Répare les corruptions UTF-8 courantes :

        Ã©  -> é
        ÐšÐ° -> Ка
        вЂњ -> “
        вЂќ -> ”
        Гј -> ü
        Г– -> Ö

    Plusieurs passes sont possibles, mais on reste conservateur :
    on ne garde une transformation que si elle réduit les marqueurs
    de corruption.
    """

    if text is None:
        return ""

    text = str(text)

    if not text:
        return ""

    def corruption_score(value: str) -> int:
        score = 0

        score += value.count("�") * 50

        for marker in (
            "Ã",
            "Â",
            "Ð",
            "Ñ",
            "â",
            "ð",
            "Г",
            "Р",
            "С",
            "в",
        ):
            score += value.count(marker) * 2

        for sequence in (
            "вЂ",
            "в€™",
            "в€œ",
            "вЂќ",
            "вЂ“",
            "вЂ—",
            "Гј",
            "Г–",
            "Г©",
            "Г¤",
            "Г¶",
            "Г„",
        ):
            score += value.count(sequence) * 5

        return score

    current = text

    for _ in range(3):
        candidates = [current]

        try:
            candidates.append(
                current.encode("latin1").decode("utf-8")
            )
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

        try:
            candidates.append(
                current.encode("cp1252").decode("utf-8")
            )
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

        best = min(candidates, key=corruption_score)

        if corruption_score(best) < corruption_score(current):
            current = best
        else:
            break

    return current


def clean_text(text: Any) -> str:
    if text is None:
        return ""

    text = str(text)

    if not text:
        return ""

    text = repair_mojibake(text)

    try:
        text = unicodedata.normalize("NFKC", text)
    except (TypeError, ValueError):
        pass

    text = html.unescape(text)

    # Une seconde passe est utile pour les entités HTML qui
    # révélaient seulement ensuite le texte corrompu.
    text = repair_mojibake(text)

    text = (
        text.replace("\xa0", " ")
        .replace("\u200b", "")
        .replace("\u200c", "")
        .replace("\u200d", "")
        .replace("\ufeff", "")
    )

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_title(text: Any) -> str:
    text = clean_text(text)

    # Nettoyage léger des titres RSS/HTML.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# DATES
# ============================================================

def parse_date(value: Any) -> datetime | None:
    """
    Convertit différentes représentations de date en datetime UTC.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    if hasattr(value, "tm_year"):
        try:
            return datetime(
                value.tm_year,
                value.tm_mon,
                value.tm_mday,
                value.tm_hour,
                value.tm_min,
                value.tm_sec,
                tzinfo=timezone.utc,
            )
        except Exception:
            pass

    value = str(value).strip()

    if not value:
        return None

    # ISO 8601
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)
    except ValueError:
        pass

    # RFC 2822 / RSS
    try:
        dt = parsedate_to_datetime(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass

    return None


def article_date_timestamp(article: dict[str, Any]) -> float:
    """
    Compatible avec :
      - datetime
      - ancienne chaîne ISO
      - None
    """

    value = article.get("date")

    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = parse_date(value)

    if not parsed:
        return 0

    return parsed.timestamp()


# ============================================================
# URL
# ============================================================

def normalize_url(url: Any, base_url: str = "") -> str:
    url = clean_text(url)

    if not url:
        return ""

    if base_url:
        url = urljoin(base_url, url)

    parsed = urlparse(url)

    if not parsed.scheme:
        return ""

    # Suppression de fragments.
    parsed = parsed._replace(fragment="")

    return parsed.geturl().strip()


# ============================================================
# HTTP
# ============================================================

def fetch_url(url: str, force_refresh: bool = False) -> str:
    if not force_refresh:
        cached = cache_get(url)

        if cached is not None:
            return cached

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

        # requests détecte généralement correctement l'encodage.
        # On utilise apparent_encoding uniquement si nécessaire.
        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            apparent = getattr(response, "apparent_encoding", None)

            if apparent:
                response.encoding = apparent

        content = response.text

        cache_set(url, content)

        return content

    except requests.exceptions.SSLError as exc:
        raise RuntimeError(f"SSL/TLS error: {exc}") from exc

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"HTTP error: {exc}") from exc


# ============================================================
# EXTRACTION RSS
# ============================================================

def parse_rss(source: dict[str, Any], content: str) -> list[dict[str, Any]]:
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
                        parts.append(item.get("value", ""))
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
    soup = BeautifulSoup(content, "html.parser")

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
            link_tag.get_text(" ", strip=True)
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
            force_refresh=force_refresh,
        )
    except Exception:
        return ""

    soup = BeautifulSoup(content, "html.parser")

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
        selectors.append(source["body_selector"])

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
                node.get_text(" ", strip=True)
            )

            if len(candidate) > len(body):
                body = candidate

    if not body:
        body = clean_text(
            soup.get_text(" ", strip=True)
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


# ============================================================
# DÉDUPLICATION
# ============================================================

def canonical_article_key(article: dict[str, Any]) -> str:
    url = normalize_url(article.get("url", ""))

    if url:
        parsed = urlparse(url)

        return (
            parsed.netloc.lower()
            + parsed.path.rstrip("/").lower()
        )

    title = clean_title(article.get("title", "")).lower()

    title = re.sub(r"[^\w\s]", " ", title)
    title = re.sub(r"\s+", " ", title)

    return title.strip()


def deduplicate(
    articles: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    result = []
    seen = set()

    for article in articles:
        key = canonical_article_key(article)

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        result.append(article)

    return result


# ============================================================
# VOCABULAIRE DES TITRES
# ============================================================

def build_title_vocabulary(
    articles: list[dict[str, Any]],
    limit: int = VOCABULARY_LIMIT,
) -> list[dict[str, Any]]:

    counts: dict[str, int] = {}

    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "are",
        "has",
        "have",
        "into",
        "about",
        "after",
        "before",
        "their",
        "they",
        "will",
        "you",
        "your",
        "how",
        "why",
        "what",
        "who",
        "new",
        "central",
        "asia",
        "the",
        "что",
        "как",
        "для",
        "это",
        "после",
        "перед",
        "из",
        "в",
        "на",
        "и",
        "с",
        "по",
        "не",
        "к",
        "о",
    }

    for article in articles:
        title = clean_title(
            article.get("title", "")
        ).lower()

        words = re.findall(
            r"[^\W\d_][\w'-]{2,}",
            title,
            flags=re.UNICODE,
        )

        for word in words:
            word = word.strip("-'")

            if not word:
                continue

            if word in stopwords:
                continue

            counts[word] = counts.get(word, 0) + 1

    vocabulary = [
        {
            "word": word,
            "count": count,
        }
        for word, count in counts.items()
    ]

    vocabulary.sort(
        key=lambda item: (
            -item["count"],
            item["word"],
        )
    )

    return vocabulary[:limit]


# ============================================================
# MÉMOIRE OPTIONNELLE
# ============================================================

def safe_load_memory() -> dict[str, Any]:
    if not MEMORY_FILE.exists():
        return {}

    try:
        with MEMORY_FILE.open(
            "r",
            encoding="utf-8",
        ) as handle:
            data = json.load(handle)

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {}


def safe_save_memory(
    memory: dict[str, Any],
) -> None:
    try:
        with MEMORY_FILE.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                memory,
                handle,
                ensure_ascii=False,
                indent=2,
            )

    except Exception:
        pass


def show_memory() -> dict[str, Any]:
    memory = safe_load_memory()

    if not memory:
        print("MEMORY | vide — ignorée")
    else:
        print(
            f"MEMORY | {len(memory)} éléments"
        )

    return memory


# ============================================================
# ENRICHISSEMENT
# ============================================================

def enrich_articles(
    articles: list[dict[str, Any]],
    force_refresh: bool = False,
) -> None:

    ranked = sorted(
        articles,
        key=lambda article: (
            article.get("score", 0),
            article_date_timestamp(article),
        ),
        reverse=True,
    )

    selected = ranked[:ENRICH_LIMIT]

    print(
        f"ENRICH | {len(selected)} articles avec body complet"
    )

    for index, article in enumerate(selected, 1):
        body = extract_body(
            article["url"],
            next(
                (
                    source
                    for source in SOURCES
                    if source.get("name")
                    == article.get("source")
                ),
                {},
            ),
            force_refresh=force_refresh,
        )

        if body:
            article["body"] = body

        # Re-score après enrichissement.
        classify_article(article)

        if index % 10 == 0:
            print(
                f"ENRICH | {index}/{len(selected)}"
            )


# ============================================================
# STATISTIQUES
# ============================================================

def build_stats(
    articles: list[dict[str, Any]],
) -> dict[str, Any]:

    scores = [
        float(article.get("score", 0) or 0)
        for article in articles
    ]

    levels = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    }

    relevant = 0

    for article in articles:
        level = article.get("level", "D")

        if level in levels:
            levels[level] += 1

        if article.get("relevant"):
            relevant += 1

    average = (
        sum(scores) / len(scores)
        if scores
        else 0
    )

    return {
        "analyzed": len(articles),
        "retained": relevant,
        "avg_score": round(average, 1),
        "level_a": levels["A"],
        "level_b": levels["B"],
        "level_c": levels["C"],
        "level_d": levels["D"],
    }


# ============================================================
# AUDIT
# ============================================================

def build_audit(
    articles: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    audit = []

    for article in articles:
        audit.append(
            {
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "score": article.get("score", 0),
                "level": article.get("level", "D"),
                "relevant": article.get(
                    "relevant",
                    False,
                ),
                "signals": article.get(
                    "signals",
                    {},
                ),
            }
        )

    return audit


# ============================================================
# SCAN
# ============================================================

def run_scan(
    force_refresh: bool = False,
) -> list[dict[str, Any]]:

    show_memory()

    print(
        f"SOURCES | {len(SOURCES)} sources actives"
    )

    all_articles: list[dict[str, Any]] = []

    for source in SOURCES:
        name = source.get(
            "name",
            "Unknown",
        )

        url = source.get("url", "")

        if not url:
            print(
                f"WARNING | {name} | URL absente"
            )
            continue

        try:
            content = fetch_url(
                url,
                force_refresh=force_refresh,
            )

            source_type = str(
                source.get("type", "rss")
            ).lower()

            if source_type in {
                "rss",
                "feed",
                "atom",
            }:
                articles = parse_rss(
                    source,
                    content,
                )
            else:
                articles = extract_links_from_html(
                    source,
                    content,
                )

            print(
                f"SOURCE | {name} | "
                f"{len(articles)} articles"
            )

            all_articles.extend(articles)

        except Exception as exc:
            print(
                f"WARNING | {name} | ERROR | {exc}"
            )

    print(
        f"COLLECT | {len(all_articles)} articles avant déduplication"
    )

    all_articles = deduplicate(all_articles)

    print(
        f"COLLECT | {len(all_articles)} articles récupérés"
    )

    print(
        f"DEDUP | {len(all_articles)} articles uniques"
    )

    # --------------------------------------------------------
    # Première passe : titre + résumé uniquement
    # --------------------------------------------------------

    print(
        "SCORING | première passe title + summary"
    )

    for article in all_articles:
        article["body"] = ""
        classify_article(article)

    # --------------------------------------------------------
    # Vocabulaire
    # --------------------------------------------------------

    vocabulary = build_title_vocabulary(
        all_articles
    )

    print(
        f"VOCABULARY | {len(vocabulary)} mots de titres"
    )

    # --------------------------------------------------------
    # Deuxième passe : body sur les meilleurs
    # --------------------------------------------------------

    enrich_articles(
        all_articles,
        force_refresh=force_refresh,
    )

    # --------------------------------------------------------
    # Tri final
    # --------------------------------------------------------

    all_articles.sort(
        key=lambda article: (
            bool(article.get("relevant")),
            article.get("score", 0),
            article_date_timestamp(article),
        ),
        reverse=True,
    )

    # --------------------------------------------------------
    # Stats
    # --------------------------------------------------------

    stats = build_stats(
        all_articles
    )

    audit = build_audit(
        all_articles
    )

    print(
        "STATS | "
        f"analyzed={stats['analyzed']} | "
        f"retained={stats['retained']} | "
        f"avg={stats['avg_score']}/100"
    )

    print(
        "LEVELS | "
        f"A={stats['level_a']} "
        f"B={stats['level_b']} "
        f"C={stats['level_c']} "
        f"D={stats['level_d']}"
    )

    # --------------------------------------------------------
    # Génération HTML
    # --------------------------------------------------------

    print("HTML | génération de index.html")

    try:
        html_output = create_web_page(
            articles=all_articles,
            audit=audit,
            stats=stats,
            title_words=vocabulary,
        )

        if not isinstance(html_output, str):
            raise TypeError(
                "create_web_page() n'a pas retourné une chaîne HTML"
            )

        OUTPUT_FILE.write_text(
            html_output,
            encoding="utf-8",
        )

        if OUTPUT_FILE.exists():
            size = OUTPUT_FILE.stat().st_size

            print(
                f"HTML | index.html créé | {size} octets"
            )
        else:
            print(
                "ERROR | index.html n'a pas été créé"
            )

    except Exception as exc:
        print(
            f"ERROR | HTML | {type(exc).__name__}: {exc}"
        )

        # On relance l'erreur pour que le workflow GitHub
        # ne masque pas le problème.
        raise

    return all_articles


# ============================================================
# CLI
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Central Asia News Scanner"
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help="Force une nouvelle récupération des sources.",
    )

    args = parser.parse_args()

    try:
        articles = run_scan(
            force_refresh=args.scan
        )

        selected = [
            article
            for article in articles
            if article.get("relevant")
        ]

        print(
            f"SCAN | terminé | "
            f"{len(selected)} articles sélectionnés"
        )

    except Exception as exc:
        print(
            f"SCAN | erreur fatale | "
            f"{type(exc).__name__}: {exc}"
        )

        raise


if __name__ == "__main__":
    main()
