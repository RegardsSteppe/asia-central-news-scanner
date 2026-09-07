import html
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FEED_ENTRIES = 50
MAX_HTML_ARTICLES = 50
ARTICLES_TO_DISPLAY = 10
REQUEST_TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AsiaCentralNewsScanner/3.2; "
        "+https://github.com/RegardsSteppe/asia-central-news-scanner)"
    )
}


# Source-specific configuration.
#
# IMPORTANT:
# We no longer guess rss.xml / feed.xml / atom.xml.
# Each source has either known feeds or an HTML page.

TOP_NEWS_SOURCES = [
    {
        "name": "Eurasianet",
        "url": "https://eurasianet.org/latest",
        "feeds": [],
    },
    {
        "name": "Cabar.asia",
        "url": "https://cabar.asia/en/",
        "feeds": [
            "https://cabar.asia/en/feed",
        ],
    },
    {
        "name": "Radio Free Europe / Radio Liberty",
        "url": "https://www.rferl.org/p/5549.html",
        "feeds": [
            # Kazakhstan
            "https://www.rferl.org/api/zriiml-vomx-tpeogm_",
            # Kyrgyzstan
            "https://www.rferl.org/api/zqii_l-vomx-tpeigmy",
            # Tajikistan
            "https://www.rferl.org/api/z_iiol-vomx-tpevgmi",
            # Turkmenistan
            "https://www.rferl.org/api/ztiiml-vomx-tpekgm_",
            # Uzbekistan
            "https://www.rferl.org/api/ztukmrl-vomx-tpeki-mo",
        ],
    },
    {
        "name": "Azernews",
        "url": "https://www.azernews.az/latest/",
        "feeds": [],
    },
]


# ============================================================
# KEYWORDS
# ============================================================

CENTRAL_ASIA_TERMS = [
    "central asia",
    "central asian",
    "центральная азия",
    "центральной азии",
    "центральную азию",
    "центральноазиат",

    "kazakhstan",
    "kazakh",
    "kazakhstani",
    "казахстан",
    "казахстана",
    "казахстане",
    "казахстанский",
    "казах",

    "kyrgyzstan",
    "kyrgyz",
    "киргизия",
    "киргизии",
    "киргизстан",
    "кыргызстан",
    "кыргызский",
    "кыргыз",

    "tajikistan",
    "tajik",
    "таджикистан",
    "таджикистане",
    "таджикский",
    "таджик",

    "turkmenistan",
    "turkmen",
    "туркменистан",
    "туркменистане",
    "туркменский",
    "туркмен",

    "uzbekistan",
    "uzbek",
    "узбекистан",
    "узбекистана",
    "узбекистане",
    "узбекский",
    "узбек",

    "tashkent",
    "ташкент",
    "astana",
    "астана",
    "almaty",
    "алматы",
    "bishkek",
    "бишкек",
    "dushanbe",
    "душанбе",
    "ashgabat",
    "ашхабад",
    "ashkhabad",
    "samarkand",
    "самарканд",
]


STRONG_HR_TERMS = [
    "human rights",
    "human rights violation",
    "human rights violations",
    "rights violation",
    "rights violations",
    "political prisoner",
    "political prisoners",
    "political arrest",
    "political arrests",
    "arrested activist",
    "arrested activists",
    "detained activist",
    "detained activists",
    "dissident",
    "dissidents",
    "dissidence",
    "torture",
    "tortured",
    "torture allegations",
    "forced disappearance",
    "forced disappearances",
    "enforced disappearance",
    "enforced disappearances",
    "freedom of the press",
    "press freedom",
    "journalist arrested",
    "journalists arrested",
    "journalist detained",
    "journalists detained",
    "journalist persecuted",
    "journalists persecuted",
    "media repression",
    "media crackdown",
    "crackdown on media",
    "opposition crackdown",
    "opposition figure arrested",
    "opposition figures arrested",
    "opposition leader arrested",
    "opposition leaders arrested",
    "activist arrested",
    "activists arrested",
    "activist detained",
    "activists detained",
    "protesters arrested",
    "protesters detained",
    "protest crackdown",
    "protests repressed",

    "права человека",
    "нарушение прав человека",
    "нарушения прав человека",
    "политический заключенный",
    "политические заключенные",
    "политзаключенный",
    "политзаключенные",
    "политический арест",
    "политические аресты",
    "арест активиста",
    "арест активистов",
    "задержание активиста",
    "задержание активистов",
    "диссидент",
    "диссиденты",
    "диссидентство",
    "пытки",
    "пытка",
    "насильственное исчезновение",
    "исчезновение",
    "свобода прессы",
    "свобода слова",
    "журналист арестован",
    "журналисты арестованы",
    "журналист задержан",
    "журналисты задержаны",
    "репрессии",
    "репрессии против СМИ",
    "давление на СМИ",
    "разгон протестов",
    "протестующие задержаны",
    "оппозиционер арестован",
    "оппозиционеры арестованы",
]


SECONDARY_HR_TERMS = [
    "activist",
    "activists",
    "civil society",
    "human rights defender",
    "human rights defenders",
    "rights defender",
    "rights defenders",
    "free speech",
    "freedom of speech",
    "freedom of expression",
    "independent media",
    "censorship",
    "censored",
    "crackdown",
    "repression",
    "repressed",
    "persecution",
    "persecuted",
    "political persecution",
    "political opposition",
    "opposition",
    "dissident",
    "lawyer",
    "rights group",
    "rights groups",

    "активист",
    "активисты",
    "гражданское общество",
    "правозащитник",
    "правозащитники",
    "защитник прав",
    "свобода слова",
    "свобода выражения",
    "независимые СМИ",
    "цензура",
    "цензур",
    "репрессия",
    "репрессии",
    "преследование",
    "преследования",
    "политическое преследование",
    "политическая оппозиция",
    "оппозиция",
]


DOMESTIC_POLITICAL_TERMS = [
    "election",
    "elections",
    "presidential election",
    "parliamentary election",
    "parliamentary elections",
    "vote",
    "voting",
    "ballot",
    "constitution",
    "constitutional reform",
    "constitutional amendments",
    "presidential transition",
    "presidential succession",
    "new president",
    "president resigns",
    "president resigned",
    "president steps down",
    "opposition party",
    "opposition parties",
    "opposition leader",
    "opposition leaders",
    "political opposition",
    "political reform",
    "political reforms",
    "political crisis",
    "government crisis",
    "cabinet reshuffle",
    "parliament",
    "parliamentary",
    "political corruption",
    "corruption scandal",
    "anti-corruption",
    "anti-corruption campaign",
    "political party",
    "political parties",

    "выборы",
    "президентские выборы",
    "парламентские выборы",
    "голосование",
    "конституция",
    "конституционная реформа",
    "конституционные поправки",
    "смена президента",
    "отставка президента",
    "новый президент",
    "оппозиционная партия",
    "оппозиционные партии",
    "лидер оппозиции",
    "политическая оппозиция",
    "политическая реформа",
    "политический кризис",
    "правительственный кризис",
    "перестановки в правительстве",
    "парламент",
    "политическая коррупция",
    "коррупционный скандал",
    "борьба с коррупцией",
    "политическая партия",
]


MAJOR_REGIONAL_EVENTS = [
    "shanghai cooperation organization",
    "sco summit",
    "sco meeting",
    "sco leaders",
    "sco declaration",
    "sco summit kicks off",
    "sco summit begins",
    "sco summit ends",
    "shanghai grouping",

    "major conflict",
    "armed conflict",
    "military conflict",
    "border conflict",
    "border clashes",
    "major sanctions",
    "new sanctions",
    "sanctions regime",
    "major diplomatic crisis",
    "diplomatic crisis",
    "strategic shift",
    "strategic realignment",
    "security crisis",
    "regional security crisis",

    "шанхайская организация сотрудничества",
    "саммит шос",
    "саммит шанхайской организации сотрудничества",
    "шанхайская группа",
    "вооруженный конфликт",
    "военный конфликт",
    "пограничный конфликт",
    "пограничные столкновения",
    "крупные санкции",
    "новые санкции",
    "дипломатический кризис",
    "стратегический сдвиг",
    "стратегическая переориентация",
    "кризис безопасности",
]


ROUTINE_GEO_TERMS = [
    "trade",
    "trading",
    "exports",
    "imports",
    "investment",
    "investments",
    "business",
    "economic cooperation",
    "economic partnership",
    "trade agreement",
    "trade corridor",
    "transport corridor",
    "railway",
    "railroad",
    "logistics",
    "gas",
    "oil",
    "uranium",
    "electricity",
    "power line",
    "pipeline",
    "energy cooperation",
    "energy project",
    "gas deal",
    "oil deal",
    "investment agreement",
    "business forum",
    "economic forum",
    "summit",
    "meeting",
    "visit",
    "talks",
    "cooperation",
    "roadmap",

    "торговля",
    "экспорт",
    "импорт",
    "инвестиции",
    "бизнес",
    "экономическое сотрудничество",
    "экономическое партнерство",
    "торговое соглашение",
    "торговый коридор",
    "транспортный коридор",
    "железная дорога",
    "логистика",
    "газ",
    "нефть",
    "уран",
    "электроэнергия",
    "линия электропередачи",
    "трубопровод",
    "энергетическое сотрудничество",
    "энергетический проект",
    "газовое соглашение",
    "нефтяное соглашение",
    "инвестиционное соглашение",
    "бизнес-форум",
    "экономический форум",
    "саммит",
    "встреча",
    "визит",
    "переговоры",
    "сотрудничество",
    "дорожная карта",
]


REGIONAL_ACTORS = [
    "russia",
    "russian",
    "kremlin",
    "putin",
    "china",
    "chinese",
    "beijing",
    "afghanistan",
    "afghan",
    "iran",
    "iranian",
    "turkey",
    "turkish",
    "azerbaijan",
    "azerbaijani",
    "armenia",
    "armenian",
    "georgia",
    "georgian",
    "united states",
    "washington",
    "european union",
    "eu",
    "brussels",

    "россия",
    "российский",
    "кремль",
    "путин",
    "китай",
    "китайский",
    "пекин",
    "афганистан",
    "афганский",
    "иран",
    "иранский",
    "турция",
    "турецкий",
    "азербайджан",
    "армения",
    "грузия",
    "сша",
    "вашингтон",
    "евросоюз",
    "брюссель",
]


BUSINESS_SPORTS_TECH_TERMS = [
    "football",
    "soccer",
    "basketball",
    "tennis",
    "match",
    "championship",
    "tournament",
    "olympics",
    "athlete",
    "coach",
    "goal",
    "scored",
    "startup",
    "start-up",
    "software",
    "smartphone",
    "app",
    "artificial intelligence",
    "ai model",
    "technology expo",
    "gaming",
    "restaurant",
    "hotel",
    "tourism",
    "travel guide",
]


# ============================================================
# HELPERS
# ============================================================

def normalize_text(text):
    if not text:
        return ""

    text = html.unescape(str(text))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def phrase_present(text, phrase):
    if not text or not phrase:
        return False

    pattern = r"(?<!\w)" + re.escape(
        phrase.lower()
    ) + r"(?!\w)"

    return re.search(
        pattern,
        text.lower(),
    ) is not None


def find_terms(text, terms):
    text = normalize_text(text).lower()

    return [
        term
        for term in terms
        if phrase_present(text, term)
    ]


def canonical_url(url):
    if not url:
        return ""

    parsed = urlparse(url)

    if not parsed.scheme:
        return url

    clean = parsed._replace(
        query="",
        fragment="",
    )

    return clean.geturl().rstrip("/")


def is_valid_url(url):
    if not url:
        return False

    parsed = urlparse(url)

    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
    )


def fetch_url(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as exc:
        print(
            f"[WARN] Failed to fetch {url}: {exc}"
        )

        return None


# ============================================================
# RSS
# ============================================================

def parse_feed(feed_url, source_name):
    raw = fetch_url(feed_url)

    if not raw:
        return []

    try:
        feed = feedparser.parse(raw)

    except Exception as exc:
        print(
            f"[WARN] Could not parse feed {feed_url}: {exc}"
        )
        return []

    articles = []

    for entry in feed.entries[:MAX_FEED_ENTRIES]:
        title = normalize_text(
            entry.get("title", "")
        )

        link = entry.get("link", "")

        if not title or not is_valid_url(link):
            continue

        summary = normalize_text(
            entry.get("summary", "")
            or entry.get("description", "")
        )

        published = (
            entry.get("published")
            or entry.get("updated")
            or ""
        )

        published_parsed = (
            entry.get("published_parsed")
            or entry.get("updated_parsed")
        )

        published_dt = None

        if published_parsed:
            try:
                published_dt = datetime(
                    *published_parsed[:6],
                    tzinfo=timezone.utc,
                )

            except Exception:
                pass

        articles.append(
            {
                "source": source_name,
                "title": title,
                "url": canonical_url(link),
                "summary": summary,
                "published": published,
                "published_dt": published_dt,
                "body": "",
            }
        )

    return articles


# ============================================================
# HTML EXTRACTION
# ============================================================

def extract_html_articles(
    source_url,
    source_name,
):
    page = fetch_url(source_url)

    if not page:
        return []

    soup = BeautifulSoup(
        page,
        "html.parser",
    )

    for tag in soup.find_all(
        [
            "script",
            "style",
            "noscript",
            "nav",
            "header",
            "footer",
            "aside",
            "form",
        ]
    ):
        tag.decompose()

    articles = []
    seen_urls = set()

    for item in soup.find_all(
        [
            "article",
            "h1",
            "h2",
            "h3",
        ]
    ):
        if len(articles) >= MAX_HTML_ARTICLES:
            break

        if item.name == "article":
            heading = item.find(
                [
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                ]
            )

            link_tag = item.find(
                "a",
                href=True,
            )

            if not heading or not link_tag:
                continue

            title = normalize_text(
                heading.get_text(
                    " ",
                    strip=True,
                )
            )

            url = urljoin(
                source_url,
                link_tag.get("href", ""),
            )

            text = normalize_text(
                item.get_text(
                    " ",
                    strip=True,
                )
            )

        else:
            title = normalize_text(
                item.get_text(
                    " ",
                    strip=True,
                )
            )

            link_tag = item.find(
                "a",
                href=True,
            )

            if not link_tag:
                parent = item.find_parent(
                    "a",
                    href=True,
                )

                link_tag = parent

            if not link_tag:
                continue

            url = urljoin(
                source_url,
                link_tag.get("href", ""),
            )

            text = title

        if not title or len(title) < 15:
            continue

        if not is_valid_url(url):
            continue

        url = canonical_url(url)

        if url in seen_urls:
            continue

        if title.lower() in {
            "latest",
            "news",
            "more news",
            "read more",
            "latest news",
        }:
            continue

        seen_urls.add(url)

        articles.append(
            {
                "source": source_name,
                "title": title,
                "url": url,
                "summary": text,
                "published": "",
                "published_dt": None,
                "body": "",
            }
        )

    return articles


# ============================================================
# ARTICLE BODY
# ============================================================

def extract_article_body(url):
    page = fetch_url(url)

    if not page:
        return ""

    soup = BeautifulSoup(
        page,
        "html.parser",
    )

    for tag in soup.find_all(
        [
            "script",
            "style",
            "noscript",
            "nav",
            "header",
            "footer",
            "aside",
            "form",
            "iframe",
        ]
    ):
        tag.decompose()

    candidates = []

    for selector in [
        "article",
        "[class*='article-body']",
        "[class*='article-content']",
        "[class*='story-body']",
        "[class*='story-content']",
        "[class*='post-content']",
        "[class*='entry-content']",
        "main",
    ]:
        for node in soup.select(selector):
            text = normalize_text(
                node.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(text) >= 200:
                candidates.append(text)

    if not candidates:
        paragraphs = []

        for p in soup.find_all("p"):
            text = normalize_text(
                p.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(text) >= 50:
                paragraphs.append(text)

        candidates.append(
            " ".join(paragraphs)
        )

    if not candidates:
        return ""

    return max(
        candidates,
        key=len,
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_article(article):
    title = normalize_text(
        article.get("title", "")
    )

    summary = normalize_text(
        article.get("summary", "")
    )

    body = normalize_text(
        article.get("body", "")
    )

    headline_text = (
        f"{title} {summary}"
    ).strip()

    geography = find_terms(
        headline_text,
        CENTRAL_ASIA_TERMS,
    )

    strong_hr = find_terms(
        headline_text,
        STRONG_HR_TERMS,
    )

    secondary_hr = find_terms(
        headline_text,
        SECONDARY_HR_TERMS,
    )

    domestic_politics = find_terms(
        headline_text,
        DOMESTIC_POLITICAL_TERMS,
    )

    major_events = find_terms(
        headline_text,
        MAJOR_REGIONAL_EVENTS,
    )

    routine_geo = find_terms(
        headline_text,
        ROUTINE_GEO_TERMS,
    )

    regional_actors = find_terms(
        headline_text,
        REGIONAL_ACTORS,
    )

    negative = find_terms(
        headline_text,
        BUSINESS_SPORTS_TECH_TERMS,
    )

    # --------------------------------------------------------
    # Body confirmation
    # --------------------------------------------------------

    confirmation_hr = []
    confirmation_politics = []
    confirmation_events = []

    potentially_relevant = (
        bool(geography)
        and (
            bool(strong_hr)
            or bool(secondary_hr)
            or bool(domestic_politics)
            or bool(major_events)
        )
    )

    if potentially_relevant and not body:
        body = extract_article_body(
            article.get("url", "")
        )

        article["body"] = body

    if body:
        confirmation_hr = find_terms(
            body,
            STRONG_HR_TERMS,
        )

        confirmation_politics = find_terms(
            body,
            DOMESTIC_POLITICAL_TERMS,
        )

        confirmation_events = find_terms(
            body,
            MAJOR_REGIONAL_EVENTS,
        )

    # --------------------------------------------------------
    # CLASSIFICATION HIERARCHY
    #
    # A = Human rights / repression
    # C = Exceptional regional geopolitics
    # B = Domestic politics
    #
    # C deliberately comes BEFORE B so that an SCO summit
    # cannot become "politique intérieure" just because the
    # article contains the word "politics".
    # --------------------------------------------------------

    if geography and (
        strong_hr
        or confirmation_hr
    ):
        level = "A"
        classification = (
            "Droits humains / dissidence"
        )

    elif geography and (
        major_events
        or confirmation_events
    ):
        level = "C"
        classification = (
            "Géopolitique majeure"
        )

    elif geography and (
        domestic_politics
        or confirmation_politics
    ):
        level = "B"
        classification = (
            "Politique intérieure"
        )

    else:
        level = "D"
        classification = "Filtré"

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = 0

    if geography:
        score += 2

    if strong_hr:
        score += 10

    if confirmation_hr:
        score += 3

    if secondary_hr:
        score += 4

    if domestic_politics:
        score += 6

    if confirmation_politics:
        score += 2

    if major_events:
        score += 10

    if confirmation_events:
        score += 3

    if regional_actors:
        score += 1

    if routine_geo:
        score -= 4

    if negative:
        score -= 10

    score = max(
        0,
        min(score, 20),
    )

    relevant = level in {
        "A",
        "B",
        "C",
    }

    reasons = []

    if geography:
        reasons.append(
            "géographie: "
            + ", ".join(geography[:8])
        )

    if strong_hr:
        reasons.append(
            "droits humains/dissidence: "
            + ", ".join(strong_hr[:5])
        )

    if secondary_hr and not strong_hr:
        reasons.append(
            "droits humains/dissidence: "
            + ", ".join(secondary_hr[:5])
        )

    if domestic_politics:
        reasons.append(
            "politique: "
            + ", ".join(domestic_politics[:5])
        )

    if major_events:
        reasons.append(
            "événement régional: "
            + ", ".join(major_events[:5])
        )

    if regional_actors:
        reasons.append(
            "acteur régional: "
            + ", ".join(regional_actors[:5])
        )

    if routine_geo:
        reasons.append(
            "économie/géopolitique courante: "
            + ", ".join(routine_geo[:5])
        )

    if negative:
        reasons.append(
            "hors sujet probable: "
            + ", ".join(negative[:5])
        )

    if confirmation_hr:
        reasons.append(
            "confirmation article: droits humains"
        )

    if confirmation_politics:
        reasons.append(
            "confirmation article: politique"
        )

    if confirmation_events:
        reasons.append(
            "confirmation article: événement régional"
        )

    article["level"] = level
    article["classification"] = classification
    article["score"] = score
    article["relevant"] = relevant
    article["reasons"] = reasons

    return article


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_articles(articles):
    seen = set()
    result = []

    for article in articles:
        url = canonical_url(
            article.get("url", "")
        )

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)
        result.append(article)

    return result


def article_timestamp(article):
    dt = article.get("published_dt")

    if dt:
        return dt

    return datetime.min.replace(
        tzinfo=timezone.utc
    )


# ============================================================
# SCANNER
# ============================================================

def scan_news():
    raw_articles = []
    source_status = []

    for source in TOP_NEWS_SOURCES:
        name = source["name"]
        source_url = source["url"]
        feeds = source.get("feeds", [])

        print(
            f"[INFO] Scanning {name}"
        )

        source_articles = []

        # ----------------------------------------------------
        # Known RSS feeds only.
        # ----------------------------------------------------

        for feed_url in feeds:
            print(
                f"[INFO] Trying known feed: {feed_url}"
            )

            parsed = parse_feed(
                feed_url,
                name,
            )

            if parsed:
                source_articles.extend(parsed)

        # ----------------------------------------------------
        # HTML fallback.
        # ----------------------------------------------------

        if not source_articles:
            print(
                f"[INFO] Using HTML source for {name}"
            )

            source_articles = (
                extract_html_articles(
                    source_url,
                    name,
                )
            )

        if source_articles:
            source_status.append(
                {
                    "name": name,
                    "status": "success",
                    "count": len(source_articles),
                }
            )

        else:
            source_status.append(
                {
                    "name": name,
                    "status": "failed",
                    "count": 0,
                }
            )

        raw_articles.extend(
            source_articles
        )

    print(
        "[INFO] Raw articles collected: "
        f"{len(raw_articles)}"
    )

    articles = deduplicate_articles(
        raw_articles
    )

    print(
        "[INFO] Articles after deduplication: "
        f"{len(articles)}"
    )

    classified_articles = []

    for article in articles:
        try:
            classified_articles.append(
                classify_article(article)
            )

        except Exception as exc:
            print(
                "[WARN] Classification failed for "
                f"{article.get('title', '')}: {exc}"
            )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    analyzed_count = len(
        classified_articles
    )

    retained_articles = [
        article
        for article in classified_articles
        if article.get("relevant")
    ]

    levels = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    }

    total_score = 0

    for article in classified_articles:
        level = article.get(
            "level",
            "D",
        )

        if level not in levels:
            level = "D"

        levels[level] += 1
        total_score += article.get(
            "score",
            0,
        )

    average_score = (
        round(
            total_score / analyzed_count,
            1,
        )
        if analyzed_count
        else 0
    )

    relevance_rate = (
        round(
            len(retained_articles)
            / analyzed_count
            * 100,
            1,
        )
        if analyzed_count
        else 0
    )

    successful_sources = sum(
        1
        for source in source_status
        if source["status"] == "success"
    )

    stats = {
        "raw": len(raw_articles),
        "analyzed": analyzed_count,
        "retained": len(retained_articles),
        "average_score": average_score,
        "levels": levels,
        "sources_success": successful_sources,
        "sources_total": len(
            TOP_NEWS_SOURCES
        ),
        "relevance_rate": relevance_rate,
    }

    # --------------------------------------------------------
    # Selected articles: newest first
    # --------------------------------------------------------

    retained_articles.sort(
        key=article_timestamp,
        reverse=True,
    )

    selected = retained_articles[
        :ARTICLES_TO_DISPLAY
    ]

    print(
        "[INFO] Dashboard: "
        f"{analyzed_count} analyzed / "
        f"{len(retained_articles)} retained / "
        f"average score {average_score}"
    )

    print(
        "[INFO] Levels: "
        f"A={levels['A']} "
        f"B={levels['B']} "
        f"C={levels['C']} "
        f"D={levels['D']}"
    )

    return {
        "articles": selected,
        "all_articles": classified_articles,
        "stats": stats,
        "source_status": source_status,
    }


# ============================================================
# HTML HELPERS
# ============================================================

def format_date(article):
    dt = article.get(
        "published_dt"
    )

    if dt:
        return dt.strftime(
            "%Y-%m-%d %H:%M UTC"
        )

    published = article.get(
        "published",
        "",
    )

    if published:
        return html.escape(
            published
        )

    return "Date inconnue"


def level_badge(level):
    labels = {
        "A": "🟥 Niveau A",
        "B": "🟧 Niveau B",
        "C": "🟦 Niveau C",
        "D": "⚪ Niveau D",
    }

    return labels.get(
        level,
        "⚪ Niveau D",
    )


# ============================================================
# MAIN WEB PAGE
# ============================================================

def create_web_page(scan_result):
    articles = scan_result["articles"]
    all_articles = scan_result[
        "all_articles"
    ]
    stats = scan_result["stats"]

    scan_time = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    # --------------------------------------------------------
    # Selected article cards
    # --------------------------------------------------------

    cards = []

    for article in articles:
        title = html.escape(
            article.get(
                "title",
                "Sans titre",
            )
        )

        source = html.escape(
            article.get(
                "source",
                "Source inconnue",
            )
        )

        url = html.escape(
            article.get(
                "url",
                "#",
            ),
            quote=True,
        )

        summary = html.escape(
            article.get(
                "summary",
                "",
            )
        )

        if len(summary) > 500:
            summary = (
                summary[:500].rstrip()
                + "…"
            )

        score = article.get(
            "score",
            0,
        )

        level = article.get(
            "level",
            "D",
        )

        classification = html.escape(
            article.get(
                "classification",
                "Filtré",
            )
        )

        reasons = article.get(
            "reasons",
            [],
        )

        reason_html = ""

        if reasons:
            reason_html = (
                "<div class='reasons'>"
                "<strong>Raisons :</strong> "
                + " • ".join(
                    html.escape(reason)
                    for reason in reasons
                )
                + "</div>"
            )

        cards.append(
            f"""
            <article class="article-card level-{level}">
                <div class="article-meta">
                    <span>{source}</span>
                    <span>{format_date(article)}</span>
                </div>

                <div class="article-heading">
                    <h2>
                        <a href="{url}"
                           target="_blank"
                           rel="noopener">
                            {title}
                        </a>
                    </h2>

                    <span class="level-badge">
                        {level_badge(level)}
                    </span>
                </div>

                <div class="score-line">
                    <strong>
                        Score : {score}/20
                    </strong>

                    <span>
                        {classification}
                    </span>
                </div>

                <p>{summary}</p>

                {reason_html}
            </article>
            """
        )

    articles_html = "\n".join(
        cards
    )

    if not articles_html:
        articles_html = """
        <div class="empty">
            Aucun article retenu pour ce scan.
        </div>
        """

    # --------------------------------------------------------
    # Full audit table
    # --------------------------------------------------------

    audit_articles = sorted(
        all_articles,
        key=lambda article: (
            article.get(
                "score",
                0,
            ),
            article_timestamp(article),
        ),
        reverse=True,
    )

    table_rows = []

    for article in audit_articles:
        title = html.escape(
            article.get(
                "title",
                "Sans titre",
            )
        )

        source = html.escape(
            article.get(
                "source",
                "",
            )
        )

        url = html.escape(
            article.get(
                "url",
                "#",
            ),
            quote=True,
        )

        level = article.get(
            "level",
            "D",
        )

        score = article.get(
            "score",
            0,
        )

        status = (
            "Retenu"
            if article.get("relevant")
            else "Filtré"
        )

        status_class = (
            "status-retained"
            if article.get("relevant")
            else "status-filtered"
        )

        table_rows.append(
            f"""
            <tr>
                <td>
                    <a href="{url}"
                       target="_blank"
                       rel="noopener">
                        {title}
                    </a>
                </td>

                <td>{source}</td>

                <td>
                    {format_date(article)}
                </td>

                <td class="score-cell">
                    <strong>{score}/20</strong>
                </td>

                <td>
                    <span class="table-level level-{level}">
                        {level_badge(level)}
                    </span>
                </td>

                <td>
                    <span class="{status_class}">
                        {status}
                    </span>
                </td>
            </tr>
            """
        )

    audit_table = "\n".join(
        table_rows
    )

    if not audit_table:
        audit_table = """
        <tr>
            <td colspan="6">
                Aucun article analysé.
            </td>
        </tr>
        """

    levels = stats["levels"]

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Central Asia News Scanner</title>

    <style>

        :root {{
            --bg: #f5f7fa;
            --card: #ffffff;
            --text: #1f2937;
            --muted: #6b7280;
            --border: #e5e7eb;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            background: var(--bg);
            color: var(--text);
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                Helvetica,
                Arial,
                sans-serif;
        }}

        .container {{
            max-width: 1250px;
            margin: auto;
            padding: 32px 20px 60px;
        }}

        header {{
            margin-bottom: 28px;
        }}

        h1 {{
            margin: 0 0 8px;
            font-size: 2rem;
        }}

        .subtitle {{
            margin: 0;
            color: var(--muted);
            line-height: 1.5;
        }}

        .scan-time {{
            margin-top: 10px;
            color: var(--muted);
            font-size: .9rem;
        }}

        /* ================= DASHBOARD ================= */

        .dashboard {{
            margin: 28px 0 34px;
        }}

        .dashboard-title {{
            margin: 0 0 14px;
            font-size: 1.2rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(145px, 1fr));
            gap: 12px;
        }}

        .stat {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            min-height: 95px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        .stat-value {{
            font-size: 1.65rem;
            font-weight: 750;
            line-height: 1.1;
            margin-bottom: 6px;
        }}

        .stat-label {{
            color: var(--muted);
            font-size: .85rem;
        }}

        .dashboard-note {{
            margin-top: 12px;
            color: var(--muted);
            font-size: .82rem;
        }}

        /* ================= ARTICLES ================= */

        .articles {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .article-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }}

        .article-card.level-A {{
            border-left: 5px solid #b91c1c;
        }}

        .article-card.level-B {{
            border-left: 5px solid #c2410c;
        }}

        .article-card.level-C {{
            border-left: 5px solid #2563eb;
        }}

        .article-meta {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 12px;
            color: var(--muted);
            font-size: .82rem;
        }}

        .article-heading {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
        }}

        h2 {{
            margin: 0;
            font-size: 1.25rem;
            line-height: 1.35;
        }}

        h2 a {{
            color: var(--text);
            text-decoration: none;
        }}

        h2 a:hover {{
            text-decoration: underline;
        }}

        .level-badge {{
            flex-shrink: 0;
            padding: 6px 9px;
            border-radius: 8px;
            background: #f3f4f6;
            font-size: .78rem;
            white-space: nowrap;
        }}

        .score-line {{
            display: flex;
            gap: 14px;
            align-items: center;
            margin: 12px 0;
            font-size: .9rem;
        }}

        .score-line span {{
            color: var(--muted);
        }}

        .article-card p {{
            margin: 0;
            line-height: 1.55;
            color: #374151;
        }}

        .reasons {{
            margin-top: 14px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
            color: var(--muted);
            font-size: .78rem;
            line-height: 1.5;
        }}

        /* ================= AUDIT TABLE ================= */

        .audit {{
            margin-top: 48px;
        }}

        .audit h2 {{
            margin-bottom: 8px;
            font-size: 1.35rem;
        }}

        .audit-description {{
            margin: 0 0 16px;
            color: var(--muted);
            font-size: .88rem;
        }}

        .table-wrapper {{
            overflow-x: auto;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 900px;
        }}

        th,
        td {{
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            text-align: left;
            font-size: .85rem;
            vertical-align: middle;
        }}

        th {{
            background: #f9fafb;
            color: var(--muted);
            font-weight: 650;
            position: sticky;
            top: 0;
        }}

        tbody tr:last-child td {{
            border-bottom: 0;
        }}

        tbody tr:hover {{
            background: #fafafa;
        }}

        td:first-child {{
            min-width: 350px;
        }}

        td a {{
            color: var(--text);
            text-decoration: none;
            font-weight: 600;
        }}

        td a:hover {{
            text-decoration: underline;
        }}

        .score-cell {{
            white-space: nowrap;
        }}

        .table-level {{
            display: inline-block;
            padding: 5px 7px;
            border-radius: 7px;
            background: #f3f4f6;
            font-size: .75rem;
            white-space: nowrap;
        }}

        .status-retained {{
            display: inline-block;
            padding: 5px 8px;
            border-radius: 7px;
            background: #ecfdf5;
            color: #047857;
            font-size: .75rem;
            font-weight: 650;
        }}

        .status-filtered {{
            display: inline-block;
            padding: 5px 8px;
            border-radius: 7px;
            background: #f3f4f6;
            color: #6b7280;
            font-size: .75rem;
        }}

        .empty {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            color: var(--muted);
        }}

        footer {{
            margin-top: 35px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
            color: var(--muted);
            font-size: .8rem;
        }}

        @media (max-width: 700px) {{

            .container {{
                padding: 22px 14px 40px;
            }}

            h1 {{
                font-size: 1.6rem;
            }}

            .article-heading {{
                flex-direction: column;
            }}

            .article-meta {{
                flex-direction: column;
                gap: 4px;
            }}

            .level-badge {{
                white-space: normal;
            }}
        }}

    </style>
</head>

<body>

<main class="container">

    <header>

        <h1>
            Central Asia News Scanner
        </h1>

        <p class="subtitle">
            Actualités récentes d’Asie centrale —
            politique, droits humains, dissidence,
            sécurité, géopolitique et événements régionaux.
        </p>

        <div class="scan-time">
            Dernier scan : {scan_time}
        </div>

    </header>


    <!-- ================= DASHBOARD ================= -->

    <section class="dashboard">

        <h2 class="dashboard-title">
            Tableau de bord
        </h2>

        <div class="stats-grid">

            <div class="stat">
                <div class="stat-value">
                    {stats["analyzed"]}
                </div>

                <div class="stat-label">
                    📰 Articles analysés
                </div>
            </div>


            <div class="stat">
                <div class="stat-value">
                    {stats["retained"]}
                </div>

                <div class="stat-label">
                    🎯 Articles retenus
                </div>
            </div>


            <div class="stat">
                <div class="stat-value">
                    {stats["average_score"]}/20
                </div>

                <div class="stat-label">
                    📊 Score moyen
                </div>
            </div>


            <div class="stat">
                <div class="stat-value">
                    {stats["sources_success"]}/{stats["sources_total"]}
                </div>

                <div class="stat-label">
                    📡 Sources analysées
                </div>
            </div>


            <div class="stat">
                <div class="stat-value">
                    {levels["A"]}
                </div>

                <div class="stat-label">
                    🟥 Niveau A
                </div>
            </div>


            <div class="stat">
                <div class="stat-value">
                    {levels["B"]}
                </div>

                <div class="stat-label">
                    🟧 Niveau B
                </div>
            </div>


            <div class="stat">
                <div class="stat-value">
                    {levels["C"]}
                </div>

                <div class="stat-label">
                    🟦 Niveau C
                </div>
            </div>


            <div class="stat">
                <div class="stat-value">
                    {levels["D"]}
                </div>

                <div class="stat-label">
                    ⚪ Niveau D
                </div>
            </div>


            <div class="stat">
                <div class="stat-value">
                    {stats["relevance_rate"]}%
                </div>

                <div class="stat-label">
                    📈 Taux de pertinence
                </div>
            </div>

        </div>

        <div class="dashboard-note">
            Le score moyen est calculé sur l’ensemble des
            articles analysés après déduplication.
        </div>

    </section>


    <!-- ================= SELECTED ARTICLES ================= -->

    <section class="articles">

        {articles_html}

    </section>


    <!-- ================= AUDIT TABLE ================= -->

    <section class="audit">

        <h2>
            Tableau d’analyse
        </h2>

        <p class="audit-description">
            Tous les articles analysés, classés par score
            décroissant. Les articles filtrés restent visibles
            afin de permettre un contrôle du classement.
        </p>

        <div class="table-wrapper">

            <table>

                <thead>

                    <tr>
                        <th>Article</th>
                        <th>Source</th>
                        <th>Date</th>
                        <th>Score</th>
                        <th>Niveau</th>
                        <th>Statut</th>
                    </tr>

                </thead>

                <tbody>

                    {audit_table}

                </tbody>

            </table>

        </div>

    </section>


    <footer>
        Scanner automatique — Asie centrale.
        Classification basée sur les droits humains,
        la politique intérieure et les événements
        géopolitiques majeurs.
    </footer>

</main>

</body>
</html>
"""


# ============================================================
# MAIN
# ============================================================

def main():
    print(
        "[INFO] Starting Asia Central News Scanner"
    )

    scan_result = scan_news()

    page = create_web_page(
        scan_result
    )

    with open(
        "index.html",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(page)

    print(
        "[INFO] index.html generated"
    )

    print(
        "[INFO] Scan completed successfully"
    )


if __name__ == "__main__":
    main()
