import argparse
import logging
import re
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, parse_qsl, urlencode, urlunparse

import feedparser
import requests
from bs4 import BeautifulSoup

from sources import SOURCES
from keyword import classify_article
from memory import (
    load_memory,
    save_memory,
    mark_source_scanned,
)
from html_template import create_web_page


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FEED_ENTRIES = 100
MAX_HTML_ARTICLES = 100

# Nombre d'articles affichés sur la page
ARTICLES_TO_DISPLAY = 20

# Nombre maximum d'articles dont on récupère le corps complet
ARTICLE_PAGE_FETCH_LIMIT = 80

REQUEST_TIMEOUT = 20

# Vocabulaire découvert dans les titres
TITLE_WORD_MIN_COUNT = 1
TITLE_WORD_MAX = 300

TITLE_PHRASE_MIN_COUNT = 1
TITLE_PHRASE_MAX = 200

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,text/plain;q=0.8,*/*;q=0.7"
    ),
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8,ru;q=0.7",
}


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("central-asia-scanner")


# ============================================================
# STOPWORDS POUR LE VOCABULAIRE DES TITRES
# ============================================================

TITLE_STOPWORDS = {
    # English
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on",
    "at", "for", "from", "with", "without", "by", "as", "into",
    "after", "before", "over", "under", "about", "against",
    "between", "through", "during", "amid", "while", "than",
    "this", "that", "these", "those", "their", "they", "them",
    "his", "her", "its", "our", "your", "you", "we", "he", "she",
    "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "will", "would", "can", "could",
    "may", "might", "should", "must",
    "says", "said", "say", "new", "latest", "news",
    "how", "why", "what", "when", "where", "who",
    "all", "more", "most", "some", "many", "one", "two",
    "first", "last", "now", "also", "just",

    # Journalism / generic
    "report", "reports", "reported", "according",
    "video", "photos", "photo", "live", "update", "updates",
    "story", "stories", "article", "read", "explained",
    "week", "weekly", "month", "monthly", "year", "years",
    "day", "days", "today", "yesterday", "tomorrow",

    # Français
    "le", "la", "les", "un", "une", "des", "du", "de", "et",
    "ou", "mais", "dans", "sur", "pour", "avec", "sans",
    "par", "entre", "après", "avant", "contre", "chez",
    "ce", "cet", "cette", "ces", "son", "sa", "ses",
    "leur", "leurs", "qui", "que", "quoi", "dont",
    "est", "sont", "être", "avoir", "a", "ont", "été",
    "sera", "seront", "plus", "moins", "très", "aussi",
    "nouveau", "nouvelle", "nouvelles", "actualité",
    "aujourd", "hui",

    # Russe — mots grammaticaux courants
    "и", "или", "но", "а", "в", "во", "на", "с", "со",
    "к", "ко", "из", "от", "до", "по", "за", "для",
    "о", "об", "обо", "у", "не", "ни", "да",
    "это", "этот", "эта", "эти", "тот", "та", "те",
    "как", "что", "кто", "где", "когда", "почему",
    "его", "ее", "их", "ему", "ей", "им",
    "он", "она", "они", "мы", "вы", "я",
    "быть", "был", "была", "были", "есть",
    "будет", "будут", "стал", "стала", "стали",
    "также", "уже", "еще", "ещё", "только",
    "новый", "новая", "новые", "новости",
    "сегодня", "вчера", "завтра",

    # Termes éditoriaux russes
    "сообщает", "сообщили", "сообщил", "заявил",
    "заявила", "заявили", "рассказал", "рассказала",
    "президент",  # volontairement retiré ? NON : important pour analyse
}


# On garde certains mots qui peuvent être importants
# même s'ils sont fréquents dans le journalisme.
TITLE_STOPWORDS.discard("president")


# ============================================================
# TEXTE / ENCODAGE
# ============================================================

def repair_mojibake(text):
    """
    Répare les cas classiques où du UTF-8 a été décodé en latin-1.

    Exemple :
        "ÐšÐ°Ð·Ð°Ñ…" -> "Каза…"

    On ne force la conversion que si des marqueurs typiques
    de mojibake sont détectés.
    """
    if not text:
        return ""

    text = str(text)

    bad_markers = (
        "Ã",
        "Â",
        "Ð",
        "Ñ",
        "ð",
        "ñ",
        "â",
    )

    if not any(marker in text for marker in bad_markers):
        return text

    try:
        repaired = text.encode("latin1").decode("utf-8")

        # On n'accepte la réparation que si elle semble réellement
        # meilleure que le texte initial.
        if repaired != text:
            return repaired

    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    return text


def clean_text(text):
    if not text:
        return ""

    text = repair_mojibake(text)

    text = BeautifulSoup(str(text), "html.parser").get_text(
        " ",
        strip=True,
    )

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_text(text):
    text = clean_text(text)
    return text.lower().strip()


# ============================================================
# VOCABULAIRE DES TITRES
# ============================================================

def extract_title_tokens(title):
    """
    Extrait les tokens Unicode d'un titre.

    Fonctionne avec :
      - anglais
      - français
      - russe/cyrillique
      - autres alphabets Unicode
    """
    title = repair_mojibake(title)

    text = normalize_text(title)

    tokens = re.findall(
        r"[^\W\d_]+",
        text,
        flags=re.UNICODE,
    )

    result = []

    for token in tokens:
        token = token.strip()

        if len(token) < 2:
            continue

        if token in TITLE_STOPWORDS:
            continue

        result.append(token)

    return result


def extract_title_words(title):
    """
    Alias simple pour compatibilité.
    """
    return extract_title_tokens(title)


def build_title_word_list(
    articles,
    min_count=TITLE_WORD_MIN_COUNT,
    max_words=TITLE_WORD_MAX,
):
    """
    Construit le vocabulaire des mots présents dans les titres.

    Important :
    ce vocabulaire est DESCRIPTIF.
    Il n'est pas injecté automatiquement dans le scoring.
    """
    counter = Counter()

    for article in articles:
        title = article.get("title", "")

        for word in extract_title_tokens(title):
            counter[word] += 1

    words = [
        {
            "word": word,
            "count": count,
        }
        for word, count in counter.items()
        if count >= min_count
    ]

    words.sort(
        key=lambda item: (
            -item["count"],
            item["word"],
        )
    )

    return words[:max_words]


# ============================================================
# PHRASES 2-3 MOTS
# ============================================================

def build_title_phrases(
    articles,
    min_count=TITLE_PHRASE_MIN_COUNT,
    max_phrases=TITLE_PHRASE_MAX,
):
    """
    Extrait des bigrammes et trigrammes des titres.

    Exemple :
        human rights
        political prisoner
        activist detained
        journalist arrested
        forced labor

    Les phrases sont plus utiles que les mots isolés
    pour améliorer ensuite keyword.py.
    """

    phrase_counter = Counter()

    for article in articles:
        title = article.get("title", "")

        tokens = extract_title_tokens(title)

        if len(tokens) < 2:
            continue

        # Bigrams
        for i in range(len(tokens) - 1):
            phrase = f"{tokens[i]} {tokens[i + 1]}"
            phrase_counter[phrase] += 1

        # Trigrams
        for i in range(len(tokens) - 2):
            phrase = (
                f"{tokens[i]} "
                f"{tokens[i + 1]} "
                f"{tokens[i + 2]}"
            )
            phrase_counter[phrase] += 1

    phrases = [
        {
            "phrase": phrase,
            "count": count,
        }
        for phrase, count in phrase_counter.items()
        if count >= min_count
    ]

    phrases.sort(
        key=lambda item: (
            -item["count"],
            item["phrase"],
        )
    )

    return phrases[:max_phrases]


# ============================================================
# HTTP
# ============================================================

def fetch_url(url, source=None):
    headers = dict(HEADERS)

    if source:
        source_headers = source.get("headers", {})
        headers.update(source_headers)

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        return {
            "ok": response.ok,
            "status": response.status_code,
            "url": response.url,
            "text": response.text,
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


# ============================================================
# DATES
# ============================================================

def parse_date(value):
    if not value:
        return None

    value = str(value).strip()

    # ISO 8601
    try:
        value_iso = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(value_iso)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except ValueError:
        pass

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def extract_container_date(container):
    # <time datetime="...">
    time_tag = container.find("time")

    if time_tag:
        value = (
            time_tag.get("datetime")
            or time_tag.get_text(" ", strip=True)
        )

        dt = parse_date(value)

        if dt:
            return dt

    # Classes / itemprop fréquents
    selectors = [
        '[itemprop="datePublished"]',
        '[itemprop="dateCreated"]',
        ".date",
        ".published",
        ".publish-date",
        ".post-date",
        ".article-date",
        ".timestamp",
        ".time",
    ]

    for selector in selectors:
        node = container.select_one(selector)

        if not node:
            continue

        value = (
            node.get("datetime")
            or node.get("content")
            or node.get_text(" ", strip=True)
        )

        dt = parse_date(value)

        if dt:
            return dt

    return None


# ============================================================
# URL
# ============================================================

def absolute_url(base_url, href):
    if not href:
        return ""

    return urljoin(base_url, href)


def is_probable_article_url(url):
    if not url:
        return False

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False

    path = parsed.path.lower()

    rejected = (
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
    )

    if any(part in path for part in rejected):
        return False

    return True


def normalize_url(url):
    if not url:
        return ""

    parsed = urlparse(url)

    query = [
        (key, value)
        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        )
        if key.lower() not in {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
        }
    ]

    normalized = parsed._replace(
        fragment="",
        query=urlencode(query),
    )

    return urlunparse(normalized).lower().rstrip("/")


# ============================================================
# ARTICLES
# ============================================================

def build_article(
    title,
    url,
    summary="",
    body="",
    date=None,
    source=None,
):
    source = source or {}

    return {
        "title": clean_text(title),
        "url": url,
        "summary": clean_text(summary),
        "body": clean_text(body),
        "date": date,
        "source": source.get("name", ""),
        "source_short": source.get(
            "short_name",
            source.get("name", ""),
        ),
        "source_profile": source.get(
            "profile",
            "",
        ),
        "source_label": source.get(
            "label",
            source.get("name", ""),
        ),
    }


# ============================================================
# RSS
# ============================================================

def parse_feed(text, base_url, source):
    feed = feedparser.parse(text)

    articles = []

    for entry in feed.entries[:MAX_FEED_ENTRIES]:
        title = clean_text(
            entry.get("title", "")
        )

        url = entry.get("link", "")

        if not title or not url:
            continue

        url = absolute_url(base_url, url)

        if not is_probable_article_url(url):
            continue

        summary = (
            entry.get("summary")
            or entry.get("description")
            or ""
        )

        date = None

        for field in (
            "published",
            "updated",
            "created",
        ):
            date = parse_date(entry.get(field))
            if date:
                break

        articles.append(
            build_article(
                title=title,
                url=url,
                summary=summary,
                date=date,
                source=source,
            )
        )

    return articles


# ============================================================
# HTML
# ============================================================

def extract_article_from_container(
    container,
    base_url,
    source,
):
    links = container.find_all("a", href=True)

    candidates = []

    for link in links:
        title = clean_text(
            link.get_text(" ", strip=True)
        )

        href = absolute_url(
            base_url,
            link.get("href"),
        )

        if (
            len(title) >= 20
            and is_probable_article_url(href)
        ):
            candidates.append(
                (len(title), title, href)
            )

    if not candidates:
        return None

    _, title, url = max(
        candidates,
        key=lambda item: item[0],
    )

    paragraphs = []

    for paragraph in container.find_all("p"):
        text = clean_text(
            paragraph.get_text(" ", strip=True)
        )

        if len(text) >= 40:
            paragraphs.append(text)

    summary = " ".join(
        paragraphs[:3]
    )

    date = extract_container_date(container)

    return build_article(
        title=title,
        url=url,
        summary=summary,
        date=date,
        source=source,
    )


def parse_html_source(text, base_url, source):
    soup = BeautifulSoup(
        text,
        "html.parser",
    )

    selectors = [
        "article",
        ".article",
        ".post",
        ".story",
        ".news-item",
        ".news-card",
        ".post-item",
        ".card",
        ".item",
        "li",
    ]

    containers = []

    for selector in selectors:
        containers.extend(
            soup.select(selector)
        )

    # Déduplication des containers par id Python
    seen = set()
    unique_containers = []

    for container in containers:
        marker = id(container)

        if marker in seen:
            continue

        seen.add(marker)
        unique_containers.append(container)

    articles = []

    for container in unique_containers:
        article = extract_article_from_container(
            container,
            base_url,
            source,
        )

        if article:
            articles.append(article)

        if len(articles) >= MAX_HTML_ARTICLES:
            break

    # Fallback : scan direct des liens
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

            href = absolute_url(
                base_url,
                link.get("href"),
            )

            if (
                len(title) >= 20
                and is_probable_article_url(href)
            ):
                articles.append(
                    build_article(
                        title=title,
                        url=href,
                        source=source,
                    )
                )

            if len(articles) >= MAX_HTML_ARTICLES:
                break

    return articles


# ============================================================
# CORPS D'ARTICLE
# ============================================================

def extract_article_body(text):
    if not text:
        return ""

    soup = BeautifulSoup(
        text,
        "html.parser",
    )

    for tag in soup(
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

    article_tags = soup.find_all(
        "article"
    )

    if article_tags:
        candidates.extend(article_tags)

    main_tags = soup.find_all(
        "main"
    )

    if main_tags:
        candidates.extend(main_tags)

    role_main = soup.select(
        '[role="main"]'
    )

    candidates.extend(role_main)

    if not candidates:
        candidates = [
            soup.body
        ] if soup.body else []

    best_text = ""

    for candidate in candidates:
        paragraphs = []

        for p in candidate.find_all("p"):
            value = clean_text(
                p.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(value) >= 40:
                paragraphs.append(value)

        candidate_text = " ".join(
            paragraphs
        )

        if len(candidate_text) > len(best_text):
            best_text = candidate_text

    return best_text[:20000]


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_articles(articles):
    unique = []

    seen_urls = set()
    seen_titles = set()

    for article in articles:
        url = normalize_url(
            article.get("url", "")
        )

        title = normalize_text(
            article.get("title", "")
        )

        if url and url in seen_urls:
            continue

        if title and title in seen_titles:
            continue

        if url:
            seen_urls.add(url)

        if title:
            seen_titles.add(title)

        unique.append(article)

    return unique


# ============================================================
# COLLECTE
# ============================================================

def collect_articles(
    cache,
    force=False,
):
    articles = []

    stats = {
        "attempted": 0,
        "successful": 0,
        "empty": 0,
        "errors": 0,
        "cached": 0,
    }

    for source in SOURCES:
        name = source.get(
            "name",
            "Unknown",
        )

        url = source.get(
            "url",
            "",
        )

        if not url:
            continue

        stats["attempted"] += 1

        # Cache
        cached_articles = None

        if not force:
            cached_articles = cache.get(
                name
            )

        if cached_articles:
            logger.info(
                "CACHE | %s | %d articles",
                name,
                len(cached_articles),
            )

            articles.extend(
                cached_articles
            )

            stats["cached"] += 1
            continue

        result = fetch_url(
            url,
            source,
        )

        if not result["ok"]:
            logger.warning(
                "ERROR | %s | status=%s | %s",
                name,
                result["status"],
                result["error"] or "",
            )

            stats["errors"] += 1

            mark_source_scanned(
                name
            )

            continue

        html = result["text"]

        if not html.strip():
            logger.warning(
                "EMPTY | %s",
                name,
            )

            stats["empty"] += 1

            mark_source_scanned(
                name
            )

            continue

        source_type = source.get(
            "type",
            "html",
        )

        if source_type == "rss":
            parsed = parse_feed(
                html,
                result["url"],
                source,
            )
        else:
            parsed = parse_html_source(
                html,
                result["url"],
                source,
            )

        if parsed:
            logger.info(
                "OK | %s | %d articles",
                name,
                len(parsed),
            )

            articles.extend(parsed)
            stats["successful"] += 1

        else:
            logger.warning(
                "EMPTY | %s | no articles",
                name,
            )

            stats["empty"] += 1

        mark_source_scanned(
            name
        )

    return articles, stats


# ============================================================
# SCORING
# ============================================================

def classify_articles(articles):
    """
    Premier passage :
        titre + résumé uniquement

    Puis :
        récupération du corps complet pour les meilleurs candidats.

    Cela évite de télécharger inutilement tous les articles.
    """

    audit = []

    # --------------------------------------------------------
    # PASS 1 : titre + résumé
    # --------------------------------------------------------

    for article in articles:
        result = classify_article(
            article
        )

        article["score"] = result.get(
            "score",
            0,
        )

        article["level"] = result.get(
            "level",
            "D",
        )

        article["reasons"] = result.get(
            "reasons",
            [],
        )

        audit.append(article)

    # --------------------------------------------------------
    # Tri intermédiaire
    # --------------------------------------------------------

    audit.sort(
        key=lambda item: (
            -item.get("score", 0),
            item.get("date") or datetime.min.replace(
                tzinfo=timezone.utc
            ),
        )
    )

    # --------------------------------------------------------
    # PASS 2 : corps complet des meilleurs
    # --------------------------------------------------------

    candidates = audit[
        :ARTICLE_PAGE_FETCH_LIMIT
    ]

    for article in candidates:
        url = article.get(
            "url",
            "",
        )

        if not url:
            continue

        result = fetch_url(
            url
        )

        if not result["ok"]:
            continue

        body = extract_article_body(
            result["text"]
        )

        if not body:
            continue

        article["body"] = body

        rescored = classify_article(
            article
        )

        article["score"] = rescored.get(
            "score",
            0,
        )

        article["level"] = rescored.get(
            "level",
            "D",
        )

        article["reasons"] = rescored.get(
            "reasons",
            [],
        )

    return audit


# ============================================================
# TRI
# ============================================================

LEVEL_ORDER = {
    "A": 0,
    "B": 1,
    "C": 2,
    "D": 3,
}


def sort_articles(articles):
    return sorted(
        articles,
        key=lambda article: (
            LEVEL_ORDER.get(
                article.get("level", "D"),
                3,
            ),
            -article.get("score", 0),
            -(
                article.get("date").timestamp()
                if article.get("date")
                else 0
            ),
        ),
    )


# ============================================================
# STATISTIQUES
# ============================================================

def build_stats(
    articles,
    source_stats,
):
    analyzed = len(articles)

    levels = Counter(
        article.get(
            "level",
            "D",
        )
        for article in articles
    )

    scores = [
        article.get(
            "score",
            0,
        )
        for article in articles
    ]

    avg_score = (
        sum(scores) / len(scores)
        if scores
        else 0
    )

    retained = sum(
        1
        for article in articles
        if article.get(
            "level",
            "D",
        ) in {"A", "B", "C"}
    )

    relevance_rate = (
        retained / analyzed * 100
        if analyzed
        else 0
    )

    return {
        "analyzed": analyzed,
        "retained": retained,
        "avg_score": round(
            avg_score,
            1,
        ),
        "levels": {
            "A": levels.get("A", 0),
            "B": levels.get("B", 0),
            "C": levels.get("C", 0),
            "D": levels.get("D", 0),
        },
        "sources": source_stats,
        "relevance_rate": round(
            relevance_rate,
            1,
        ),
    }


# ============================================================
# MÉMOIRE
# ============================================================

def show_memory(memory):
    if not memory:
        logger.info(
            "MEMORY | aucune donnée"
        )
        return

    logger.info(
        "MEMORY | %d articles connus",
        len(memory),
    )

    for article in memory[-10:]:
        logger.info(
            "  %s | %s",
            article.get("level", "?"),
            article.get("title", ""),
        )


# ============================================================
# SCAN PRINCIPAL
# ============================================================

def scan_news(
    force=False,
):
    logger.info(
        "=================================================="
    )

    logger.info(
        "CENTRAL ASIA NEWS SCANNER"
    )

    logger.info(
        "=================================================="
    )

    memory = load_memory()

    show_memory(memory)

    # --------------------------------------------------------
    # COLLECTE
    # --------------------------------------------------------

    articles, source_stats = collect_articles(
        memory,
        force=force,
    )

    logger.info(
        "COLLECT | %d articles bruts",
        len(articles),
    )

    # --------------------------------------------------------
    # DEDUP
    # --------------------------------------------------------

    articles = deduplicate_articles(
        articles
    )

    logger.info(
        "DEDUP | %d articles uniques",
        len(articles),
    )

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    audit = classify_articles(
        articles
    )

    # --------------------------------------------------------
    # VOCABULAIRE DES TITRES
    # --------------------------------------------------------

    title_words = build_title_word_list(
        audit,
        min_count=TITLE_WORD_MIN_COUNT,
        max_words=TITLE_WORD_MAX,
    )

    title_phrases = build_title_phrases(
        audit,
        min_count=TITLE_PHRASE_MIN_COUNT,
        max_phrases=TITLE_PHRASE_MAX,
    )

    logger.info(
        "TITLE VOCABULARY | %d words",
        len(title_words),
    )

    logger.info(
        "TITLE PHRASES | %d phrases",
        len(title_phrases),
    )

    logger.info(
        "TOP WORDS:"
    )

    for item in title_words[:20]:
        logger.info(
            "  %-30s %d",
            item["word"],
            item["count"],
        )

    logger.info(
        "TOP PHRASES:"
    )

    for item in title_phrases[:20]:
        logger.info(
            "  %-45s %d",
            item["phrase"],
            item["count"],
        )

    # --------------------------------------------------------
    # MÉMOIRE
    # --------------------------------------------------------

    save_memory(
        audit
    )

    # --------------------------------------------------------
    # TRI FINAL
    # --------------------------------------------------------

    sorted_audit = sort_articles(
        audit
    )

    # Articles réellement retenus
    selected = [
        article
        for article in sorted_audit
        if article.get(
            "level",
            "D",
        ) in {"A", "B", "C"}
    ]

    selected = selected[
        :ARTICLES_TO_DISPLAY
    ]

    # --------------------------------------------------------
    # STATS
    # --------------------------------------------------------

    stats = build_stats(
        audit,
        source_stats,
    )

    logger.info(
        "STATS | analyzed=%d | retained=%d | avg=%.1f/100",
        stats["analyzed"],
        stats["retained"],
        stats["avg_score"],
    )

    logger.info(
        "LEVELS | A=%d B=%d C=%d D=%d",
        stats["levels"]["A"],
        stats["levels"]["B"],
        stats["levels"]["C"],
        stats["levels"]["D"],
    )

    # --------------------------------------------------------
    # PAGE WEB
    # --------------------------------------------------------

    create_web_page(
        selected,
        sorted_audit,
        stats,
        title_words,
        title_phrases,
    )

    logger.info(
        "WEB | index.html généré"
    )

    return {
        "articles": sorted_audit,
        "selected": selected,
        "stats": stats,
        "title_words": title_words,
        "title_phrases": title_phrases,
    }


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Central Asia News Scanner"
        )
    )

    parser.add_argument(
        "--memory",
        action="store_true",
        help="Afficher la mémoire récente",
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help="Lancer un scan",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Ignorer le cache et rescanner "
            "toutes les sources"
        ),
    )

    args = parser.parse_args()

    if args.memory:
        memory = load_memory()
        show_memory(memory)

    if args.scan or not args.memory:
        scan_news(
            force=args.force
        )


if __name__ == "__main__":
    main()
