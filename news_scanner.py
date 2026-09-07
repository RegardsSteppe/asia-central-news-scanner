import logging
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

from sources import SOURCES
from keywords import (
    CENTRAL_ASIA_TERMS,
    CAUCASUS_TERMS,
    HUMAN_RIGHTS_TERMS,
    REPRESSION_TERMS,
    SPECIFIC_RIGHTS_TERMS,
    DOMESTIC_POLITICAL_TERMS,
    MAJOR_GEOPOLITICAL_TERMS,
    ROUTINE_GEO_TERMS,
    REGIONAL_ACTORS,
    HISTORICAL_TERMS,
    NON_NEWS_TERMS,
    NOISE_TERMS,
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
    """Fetch a URL and return its text."""
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
# TEXT HELPERS
# ============================================================

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", str(text))
    return text.strip()


def normalize_text(text):
    return clean_text(text).lower()


def phrase_present(text, phrase):
    """
    Word-boundary-aware keyword detection.

    This avoids, for example, matching 'sco' inside
    an unrelated word such as 'scooter'.
    """

    if not text or not phrase:
        return False

    phrase = phrase.strip().lower()

    if not phrase:
        return False

    pattern = (
        r"(?<!\w)"
        + re.escape(phrase)
        + r"(?!\w)"
    )

    return re.search(
        pattern,
        text.lower(),
    ) is not None


def find_terms(text, terms):
    found = []

    for term in terms:
        if phrase_present(text, term):
            found.append(term)

    return found


# ============================================================
# DATE HELPERS
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

    # ISO
    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
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
    """
    Extract the date only from the local article/card.

    We deliberately do NOT use a page-level date because
    that would give the same date to every article.
    """

    if not container:
        return None

    # <time datetime="">
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

    # Local metadata
    for element in container.find_all(
        ["meta", "span", "div", "p"],
        limit=30,
    ):
        classes = " ".join(
            element.get("class", [])
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
# URL HELPERS
# ============================================================

def absolute_url(base_url, href):
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

    if lowered.startswith(
        "javascript:"
    ):
        return False

    if lowered.startswith(
        "mailto:"
    ):
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
# RSS
# ============================================================

def parse_feed(feed_url, source):
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
            entry.get("title", "")
        )

        url = entry.get(
            "link",
            "",
        )

        if not title or not url:
            continue

        summary = clean_text(
            entry.get("summary", "")
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

                if parsed_time:
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
            {
                "title": title,
                "url": url,
                "summary": summary,
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
        )

    return articles


# ============================================================
# HTML ARTICLE CONTAINERS
# ============================================================

def find_article_containers(soup):
    """
    Find article/card containers without using the entire
    webpage as the context of every article.
    """

    containers = []

    # First: semantic <article>
    semantic_articles = soup.find_all(
        "article"
    )

    if semantic_articles:
        containers.extend(
            semantic_articles
        )

    # Second: common CMS classes
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
                    soup.select(selector)
                )

            except Exception:
                continue

    # Remove duplicate container objects
    unique = []
    seen_ids = set()

    for container in containers:
        identifier = id(container)

        if identifier in seen_ids:
            continue

        seen_ids.add(identifier)
        unique.append(container)

    return unique


def extract_article_from_container(
    container,
    base_url,
    source,
):
    """
    Extract exactly one article from one local container.
    """

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

    # Longest meaningful title.
    title, url, title_link = max(
        candidates,
        key=lambda item: len(
            item[0]
        ),
    )

    # Local paragraphs only.
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

    # Small local fallback.
    if not summary:
        local_text = clean_text(
            container.get_text(
                " ",
                strip=True,
            )
        )

        if len(local_text) > len(title):
            summary = local_text[
                :800
            ]

    date = extract_date_from_container(
        container
    )

    return {
        "title": title,
        "url": url,
        "summary": summary,
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
# HTML SOURCE
# ============================================================

def parse_html_source(url, source):
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
        article = (
            extract_article_from_container(
                container,
                url,
                source,
            )
        )

        if not article:
            continue

        article_url = article["url"]

        if article_url in seen_urls:
            continue

        seen_urls.add(article_url)
        articles.append(article)

        if len(articles) >= max_articles:
            break

    # Generic fallback.
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

            seen_urls.add(article_url)

            parent = link.parent

            summary = ""

            if parent:
                paragraphs = (
                    parent.find_all("p")
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
                {
                    "title": title,
                    "url": article_url,
                    "summary": summary,
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
            )

            if len(articles) >= max_articles:
                break

    return articles


# ============================================================
# ARTICLE PAGE ENRICHMENT
# ============================================================

def extract_article_body(url):
    """
    Fetch an article page and extract its main text.

    This is used only for classification confirmation.
    """

    raw = fetch_url(url)

    if not raw:
        return ""

    soup = BeautifulSoup(
        raw,
        "html.parser",
    )

    # Remove obvious noise.
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
                soup.select(selector)
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

        result.append(article)

    return result


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_article(
    article,
    body="",
):
    """
    Deterministic hierarchy:

    A = human rights / repression / serious political pressure
    B = domestic politics
    C = exceptional geopolitics
    D = everything else

    Generic geopolitics is NOT enough to become relevant.
    """

    title = article.get(
        "title",
        "",
    )

    summary = article.get(
        "summary",
        "",
    )

    headline_context = normalize_text(
        f"{title} {summary}"
    )

    full_context = normalize_text(
        f"{title} {summary} {body}"
    )

    # --------------------------------------------------------
    # Scope
    # --------------------------------------------------------

    central_asia = find_terms(
        headline_context,
        CENTRAL_ASIA_TERMS,
    )

    caucasus = find_terms(
        headline_context,
        CAUCASUS_TERMS,
    )

    has_scope = bool(
        central_asia
        or caucasus
    )

    # --------------------------------------------------------
    # Signals
    # --------------------------------------------------------

    human_rights = find_terms(
        full_context,
        HUMAN_RIGHTS_TERMS,
    )

    repression = find_terms(
        full_context,
        REPRESSION_TERMS,
    )

    specific_rights = find_terms(
        full_context,
        SPECIFIC_RIGHTS_TERMS,
    )

    domestic = find_terms(
        full_context,
        DOMESTIC_POLITICAL_TERMS,
    )

    major_geo = find_terms(
        full_context,
        MAJOR_GEOPOLITICAL_TERMS,
    )

    routine_geo = find_terms(
        full_context,
        ROUTINE_GEO_TERMS,
    )

    regional_actors = find_terms(
        full_context,
        REGIONAL_ACTORS,
    )

    historical = find_terms(
        full_context,
        HISTORICAL_TERMS,
    )

    non_news = find_terms(
        full_context,
        NON_NEWS_TERMS,
    )

    noise = find_terms(
        full_context,
        NOISE_TERMS,
    )

    # --------------------------------------------------------
    # Journalist pressure
    # --------------------------------------------------------

    journalist_terms = {
        "journalist",
        "journalists",
        "journalistes",
        "journalism",
        "reporter",
        "reporters",
    }

    journalist_pressure = (
        bool(
            set(human_rights)
            & journalist_terms
        )
        and bool(repression)
    )

    # --------------------------------------------------------
    # Activist + legal pressure
    # --------------------------------------------------------

    activist_terms = {
        "activist",
        "activists",
        "activiste",
        "activistes",
        "dissident",
        "dissidents",
        "opposition activist",
        "rights activist",
    }

    legal_pressure_terms = {
        "court",
        "courts",
        "convicted",
        "conviction",
        "sentenced",
        "sentence",
        "arrested",
        "arrest",
        "detained",
        "detention",
        "extradition",
        "prosecuted",
        "prosecution",
        "travel ban",
        "travel bans",
        "banned",
        "criminal case",
        "criminal cases",
        "case against",
        "charges",
        "charged",
    }

    activist_legal_pressure = (
        bool(
            set(human_rights)
            & activist_terms
        )
        and any(
            phrase_present(
                full_context,
                term,
            )
            for term in legal_pressure_terms
        )
    )

    # --------------------------------------------------------
    # Strong human rights
    # --------------------------------------------------------

    strong_rights = (
        bool(specific_rights)
        and bool(
            repression
            or domestic
            or human_rights
        )
    )

    strong_human_rights = (
        bool(repression)
        or journalist_pressure
        or activist_legal_pressure
        or strong_rights
    )

    # --------------------------------------------------------
    # Major geopolitics
    # --------------------------------------------------------

    major_event = bool(
        major_geo
    )

    # --------------------------------------------------------
    # SCO
    # --------------------------------------------------------

    has_sco = any(
        phrase_present(
            full_context,
            term,
        )
        for term in [
            "sco",
            "shanghai cooperation organization",
            "shanghai cooperation organisation",
            "sco summit",
        ]
    )

    # --------------------------------------------------------
    # Historical / non-news / noise
    # --------------------------------------------------------

    is_historical = bool(
        historical
    )

    is_non_news = bool(
        non_news
    )

    is_noise = bool(
        noise
    )

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = 0
    reasons = []

    if central_asia:
        score += 2
        reasons.append(
            "Asie centrale"
        )

    if caucasus:
        score += 2
        reasons.append(
            "Caucase"
        )

    if human_rights:
        score += 5
        reasons.append(
            "droits humains"
        )

    if repression:
        score += 7
        reasons.append(
            "répression / pression"
        )

    if specific_rights:
        score += 5
        reasons.append(
            "droit spécifique"
        )

    if domestic:
        score += 6
        reasons.append(
            "politique intérieure"
        )

    if major_geo:
        score += 10
        reasons.append(
            "géopolitique majeure"
        )

    if regional_actors:
        score += 1
        reasons.append(
            "acteur régional"
        )

    if routine_geo:
        score -= 5
        reasons.append(
            "géopolitique courante"
        )

    if historical:
        score -= 8
        reasons.append(
            "historique"
        )

    if non_news:
        score -= 12
        reasons.append(
            "non-news"
        )

    if noise:
        score -= 10
        reasons.append(
            "bruit / hors sujet"
        )

    # Journalist pressure bonus.
    if journalist_pressure:
        score += 6
        reasons.append(
            "journalistes sous pression"
        )

    # Activist legal pressure bonus.
    if activist_legal_pressure:
        score += 7
        reasons.append(
            "activiste sous pression judiciaire"
        )

    # SCO bonus.
    if has_sco:
        score += 8
        reasons.append(
            "Organisation de coopération de Shanghai"
        )

    # Clamp.
    score = max(
        0,
        min(
            20,
            score,
        ),
    )

    # --------------------------------------------------------
    # LEVEL
    # --------------------------------------------------------

    level = "D"

    # A = serious rights / repression.
    if (
        has_scope
        and strong_human_rights
    ):
        level = "A"

    # C = exceptional geopolitics.
    elif (
        has_scope
        and major_event
    ):
        level = "C"

    # B = domestic politics.
    elif (
        has_scope
        and domestic
    ):
        level = "B"

    # SCO always remains at least C,
    # unless it is already A.
    if (
        has_scope
        and has_sco
        and level != "A"
    ):
        level = "C"

    # --------------------------------------------------------
    # RELEVANCE GATE
    # --------------------------------------------------------

    relevant = level in {
        "A",
        "B",
        "C",
    }

    # Historical articles are filtered unless they contain
    # a genuine current rights/repression story.
    if (
        is_historical
        and not strong_human_rights
    ):
        level = "D"
        relevant = False

    # Non-news items remain in the audit but not selected.
    if is_non_news:
        level = "D"
        relevant = False
        score = min(
            score,
            8,
        )

    # Noise is filtered unless it is a strong rights story.
    if (
        is_noise
        and not strong_human_rights
    ):
        level = "D"
        relevant = False

    # --------------------------------------------------------
    # 20/20 FOR STRONG RIGHTS CASES
    # --------------------------------------------------------

    if (
        level == "A"
        and (
            journalist_pressure
            or activist_legal_pressure
            or (
                specific_rights
                and repression
            )
        )
        and not is_non_news
    ):
        score = 20

    # SCO stories should remain highly visible.
    if (
        level == "C"
        and has_sco
        and not is_non_news
    ):
        score = max(
            score,
            18,
        )

    return {
        "level": level,
        "score": score,
        "relevant": relevant,
        "reasons": reasons,
        "signals": {
            "central_asia": central_asia,
            "caucasus": caucasus,
            "human_rights": human_rights,
            "repression": repression,
            "specific_rights": specific_rights,
            "domestic": domestic,
            "major_geo": major_geo,
            "routine_geo": routine_geo,
            "regional_actors": regional_actors,
            "historical": historical,
            "non_news": non_news,
            "noise": noise,
        },
    }


# ============================================================
# SCAN ONE SOURCE
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

        # HTML fallback
        if (
            not articles
            and source.get("fallback")
        ):
            logger.info(
                "RSS unavailable for %s, using HTML fallback",
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

    # Ensure source metadata.
    for article in articles:
        article["source"] = source[
            "name"
        ]

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
# COLLECT ALL SOURCES
# ============================================================

def collect_articles():
    all_articles = []
    successful_sources = 0

    for source in SOURCES:

        try:
            articles = scan_source(
                source
            )

            if articles:
                successful_sources += 1

            all_articles.extend(
                articles
            )

        except Exception:
            logger.exception(
                "Source failed: %s",
                source.get("name"),
            )

    return (
        all_articles,
        successful_sources,
    )


# ============================================================
# CLASSIFY ALL ARTICLES
# ============================================================

def classify_articles(articles):
    """
    First pass:
        title + summary

    Second pass:
        fetch article body for the strongest candidates.
    """

    audit = []

    # --------------------------------------------------------
    # First pass
    # --------------------------------------------------------

    for article in articles:

        classification = classify_article(
            article
        )

        article["level"] = (
            classification["level"]
        )

        article["score"] = (
            classification["score"]
        )

        article["relevant"] = (
            classification["relevant"]
        )

        article["reasons"] = (
            classification["reasons"]
        )

        article["signals"] = (
            classification["signals"]
        )

        audit.append(article)

    # --------------------------------------------------------
    # Select strongest candidates for body fetch
    # --------------------------------------------------------

    minimum_date = (
        datetime.min.replace(
            tzinfo=timezone.utc
        )
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
    # Second pass
    # --------------------------------------------------------

    for article in audit:

        if article.get("url") not in candidate_urls:
            continue

        body = extract_article_body(
            article.get(
                "url",
                "",
            )
        )

        if not body:
            continue

        classification = classify_article(
            article,
            body,
        )

        article["level"] = (
            classification["level"]
        )

        article["score"] = (
            classification["score"]
        )

        article["relevant"] = (
            classification["relevant"]
        )

        article["reasons"] = (
            classification["reasons"]
        )

        article["signals"] = (
            classification["signals"]
        )

    return audit


# ============================================================
# SORTING
# ============================================================

LEVEL_PRIORITY = {
    "A": 4,
    "B": 3,
    "C": 2,
    "D": 1,
}


def sort_articles(articles):
    """
    Strongest score first, then level, then date.
    """

    minimum_date = (
        datetime.min.replace(
            tzinfo=timezone.utc
        )
    )

    return sorted(
        articles,
        key=lambda article: (
            article.get(
                "score",
                0,
            ),
            LEVEL_PRIORITY.get(
                article.get(
                    "level",
                    "D",
                ),
                0,
            ),
            article.get(
                "date"
            ) or minimum_date,
        ),
        reverse=True,
    )


# ============================================================
# STATISTICS
# ============================================================

def build_stats(
    audit,
    successful_sources,
):
    analyzed = len(audit)

    retained = [
        article
        for article in audit
        if article.get("relevant")
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

        # Format attendu par html_template.py
        "avg_score": round(
            avg_score,
            1,
        ),

        "levels": levels,

        # Conservés également pour compatibilité
        # avec d'éventuelles autres parties du template.
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
# MAIN
# ============================================================

def scan_news():
    logger.info(
        "Starting Asia Central News Scanner"
    )

    # --------------------------------------------------------
    # Collect
    # --------------------------------------------------------

    (
        raw_articles,
        successful_sources,
    ) = collect_articles()

    logger.info(
        "Raw articles collected: %d",
        len(raw_articles),
    )

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    articles = deduplicate_articles(
        raw_articles
    )

    logger.info(
        "Articles after deduplication: %d",
        len(articles),
    )

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    audit = classify_articles(
        articles
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    sorted_audit = sort_articles(
        audit
    )

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
    # Statistics
    # --------------------------------------------------------

    stats = build_stats(
        sorted_audit,
        successful_sources,
    )

    logger.info(
    "Dashboard: %d analyzed / %d retained / average score %.1f",
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
    # Log selected articles
    # --------------------------------------------------------

    for article in selected:
        logger.info(
            "[%s] %d/20 | %s | %s",
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
                "title",
                "",
            ),
        )

    # --------------------------------------------------------
    # Generate website
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
        file.write(html)

    logger.info(
        "Website generated: index.html"
    )

    return (
        selected,
        sorted_audit,
        stats,
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    scan_news()
