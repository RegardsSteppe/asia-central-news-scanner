import re
import html
import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
import feedparser
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

REQUEST_TIMEOUT = 20

MAX_FEED_ENTRIES = 40
MAX_HTML_ARTICLES = 30
ARTICLE_PAGE_FETCH_LIMIT = 20

# Nombre d'articles affichés sur GitHub Pages
ARTICLES_TO_DISPLAY = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AsiaCentralNewsScanner/3.0; "
        "+https://github.com/RegardsSteppe/asia-central-news-scanner)"
    )
}


# ============================================================
# SOURCES
# ============================================================

SOURCES = [
    {
        "name": "Eurasianet",
        "url": "https://eurasianet.org/",
        "rss": [
            "https://eurasianet.org/main-rss-feed",
        ],
    },
    {
        "name": "Cabar.asia",
        "url": "https://cabar.asia/",
        "rss": [
            "https://cabar.asia/ru/feed",
            "https://cabar.asia/feed",
        ],
    },
    {
        "name": "Azernews",
        "url": "https://www.azernews.az/",
        "rss": [],
    },
    {
        "name": "Radio Free Europe / Radio Liberty",
        "url": "https://www.rferl.org/",
        "rss": [],
        "rss_directory": "https://www.rferl.org/rssfeeds",
    },
]


# ============================================================
# CENTRAL ASIA — LARGE VOCABULARY
# ============================================================

# Noms des pays en anglais
COUNTRY_TERMS_EN = {
    "Kazakhstan": [
        "kazakhstan",
        "kazakh",
        "kazakhstani",
        "kazakhstan's",
    ],
    "Kyrgyzstan": [
        "kyrgyzstan",
        "kyrgyz",
        "kyrgyzstan's",
        "kirghizstan",
        "kirghiz",
    ],
    "Tajikistan": [
        "tajikistan",
        "tajik",
        "tajikistan's",
    ],
    "Turkmenistan": [
        "turkmenistan",
        "turkmen",
        "turkmenistan's",
    ],
    "Uzbekistan": [
        "uzbekistan",
        "uzbek",
        "uzbekistan's",
    ],
}

# Noms en russe
COUNTRY_TERMS_RU = {
    "Kazakhstan": [
        "казахстан",
        "казахстанский",
        "казах",
        "казахский",
    ],
    "Kyrgyzstan": [
        "кыргызстан",
        "киргизстан",
        "кыргызский",
        "киргизский",
        "кыргыз",
        "киргиз",
    ],
    "Tajikistan": [
        "таджикистан",
        "таджикский",
        "таджик",
    ],
    "Turkmenistan": [
        "туркменистан",
        "туркменский",
        "туркмен",
    ],
    "Uzbekistan": [
        "узбекистан",
        "узбекский",
        "узбек",
    ],
}

# Expressions régionales
REGIONAL_TERMS = [
    # English
    "central asia",
    "central asian",
    "central asian states",
    "central asian countries",
    "central asian region",
    "post-soviet central asia",
    "former soviet central asia",

    # Russian
    "центральная азия",
    "центральноазиатский",
    "центральноазиатские",
    "страны центральной азии",
    "государства центральной азии",
    "региона центральной азии",
]


# Pays / acteurs proches qui peuvent être très importants pour
# l'actualité d'Asie centrale.
REGIONAL_ACTORS = [
    # Russie
    "russia",
    "russian",
    "russia's",
    "moscow",
    "kremlin",
    "putin",
    "россия",
    "российский",
    "российская",
    "российские",
    "москва",
    "кремль",
    "путин",

    # Chine
    "china",
    "chinese",
    "beijing",
    "xi jinping",
    "китай",
    "китайский",
    "пекин",
    "си цзиньпин",

    # Afghanistan
    "afghanistan",
    "afghan",
    "афганистан",
    "афганский",

    # Iran
    "iran",
    "iranian",
    "tehran",
    "иран",
    "иранский",
    "тегеран",

    # Caucasus / corridors
    "azerbaijan",
    "azerbaijani",
    "armenia",
    "georgia",
    "азербайджан",
    "азербайджанский",
    "армения",
    "армянский",
    "грузия",
    "грузинский",

    # Turkey
    "turkey",
    "turkish",
    "ankara",
    "турция",
    "турецкий",
    "анкара",

    # EU / US — important for regional geopolitics
    "european union",
    "eu",
    "united states",
    "washington",
    "евросоюз",
    "европейский союз",
    "сша",
    "вашингтон",
]


# ============================================================
# TOPICS
# ============================================================

# Droits humains / dissidence
HUMAN_RIGHTS_TERMS = [
    # English
    "human rights",
    "human rights abuses",
    "rights violations",
    "rights violation",
    "civil rights",
    "freedom of speech",
    "freedom of expression",
    "freedom of press",
    "press freedom",
    "free speech",
    "political prisoner",
    "political prisoners",
    "dissident",
    "dissidents",
    "political opposition",
    "opposition activist",
    "opposition leader",
    "political activist",
    "activist",
    "activists",
    "rights activist",
    "human rights activist",
    "journalist detained",
    "journalist arrested",
    "journalist imprisoned",
    "independent journalist",
    "independent media",
    "independent outlet",
    "censorship",
    "torture",
    "arbitrary detention",
    "political repression",
    "political persecution",
    "persecution",
    "crackdown",
    "protest crackdown",
    "mass arrests",
    "forced disappearance",
    "disappeared",
    "kidnapped",

    # Russian
    "права человека",
    "нарушение прав человека",
    "нарушения прав человека",
    "правозащитник",
    "правозащитники",
    "правозащитный",
    "диссидент",
    "диссиденты",
    "оппозиционер",
    "оппозиционеры",
    "оппозиция",
    "политическая оппозиция",
    "политический активист",
    "политические активисты",
    "активист",
    "активисты",
    "правозащитник",
    "журналист",
    "журналисты",
    "независимый журналист",
    "независимые СМИ",
    "независимые медиа",
    "свобода слова",
    "свобода прессы",
    "свобода выражения",
    "цензура",
    "репрессии",
    "политические репрессии",
    "политическое преследование",
    "преследование",
    "политзаключенный",
    "политзаключённый",
    "политзаключенные",
    "политзаключённые",
    "политический заключенный",
    "политический заключённый",
    "произвольное задержание",
    "произвольно задержан",
    "произвольно задержали",
    "задержан",
    "задержана",
    "задержали",
    "арестован",
    "арестована",
    "арестовали",
    "приговорен",
    "приговорена",
    "осужден",
    "осуждён",
    "осуждена",
    "пытки",
    "пытка",
    "исчезновение",
    "похищен",
    "похищена",
    "похищение",
    "протест",
    "протесты",
    "митинг",
]


# Politique / sécurité / géopolitique
POLITICAL_TERMS = [
    # English
    "president",
    "presidential",
    "government",
    "parliament",
    "politics",
    "political",
    "election",
    "elections",
    "opposition",
    "constitution",
    "minister",
    "prime minister",
    "foreign policy",
    "diplomatic",
    "diplomacy",
    "security",
    "border",
    "border security",
    "military",
    "army",
    "sanctions",
    "treaty",
    "summit",
    "regional summit",
    "state visit",
    "strategic partnership",

    # Russian
    "президент",
    "президентский",
    "правительство",
    "парламент",
    "политика",
    "политический",
    "выборы",
    "оппозиция",
    "конституция",
    "министр",
    "премьер-министр",
    "внешняя политика",
    "дипломатия",
    "дипломатический",
    "безопасность",
    "граница",
    "пограничный",
    "военный",
    "армия",
    "санкции",
    "договор",
    "саммит",
    "встреча лидеров",
    "стратегическое партнерство",
    "стратегическое партнёрство",
]


# Actualité régionale importante
REGIONAL_EVENT_TERMS = [
    # SCO
    "shanghai cooperation organization",
    "shanghai cooperation organisation",
    "sco summit",
    "sco",
    "шанхайская организация сотрудничества",
    "шос",

    # Relations régionales
    "central asian summit",
    "central asia summit",
    "central asian leaders",
    "central asian presidents",
    "central asian cooperation",
    "central asian integration",
    "regional cooperation",
    "regional integration",
    "regional security",

    "саммит центральной азии",
    "саммит стран центральной азии",
    "лидеры центральной азии",
    "президенты центральной азии",
    "сотрудничество в центральной азии",
    "интеграция центральной азии",
    "региональное сотрудничество",
    "региональная безопасность",

    # Transport / geopolitics
    "middle corridor",
    "trans-caspian",
    "trans-caspian corridor",
    "transport corridor",
    "trade corridor",
    "rail corridor",
    "pipeline",
    "gas pipeline",
    "energy security",
    "water security",

    "средний коридор",
    "транскаспийский коридор",
    "транспортный коридор",
    "торговый коридор",
    "железнодорожный коридор",
    "газопровод",
    "энергетическая безопасность",
    "водная безопасность",
]


# Economie pertinente lorsqu'elle concerne la région.
ECONOMIC_TERMS = [
    "trade",
    "investment",
    "economy",
    "economic",
    "energy",
    "oil",
    "gas",
    "uranium",
    "mining",
    "sanctions",
    "exports",
    "imports",
    "tariffs",
    "infrastructure",
    "railway",
    "rail",
    "pipeline",
    "water",

    "торговля",
    "инвестиции",
    "экономика",
    "экономический",
    "энергетика",
    "нефть",
    "газ",
    "уран",
    "добыча",
    "экспорт",
    "импорт",
    "тарифы",
    "инфраструктура",
    "железная дорога",
    "трубопровод",
    "вода",
]


# ============================================================
# NEGATIVE SIGNALS
# ============================================================

# Ces termes ne rendent PAS un article pertinent.
# Ils permettent surtout d'éliminer les faux positifs.
GENERIC_BUSINESS_TERMS = [
    # English
    "restaurant",
    "restaurants",
    "food",
    "dining",
    "corporate dining",
    "menu",
    "meal",
    "meals",
    "catering",
    "cafe",
    "coffee",
    "hotel",
    "hospitality",
    "lifestyle",
    "shopping",
    "fashion",
    "beauty",
    "entertainment",
    "advertising",
    "marketing",
    "startup",
    "product launch",
    "brand",
    "consumer",
    "customer experience",

    # Russian
    "ресторан",
    "рестораны",
    "еда",
    "питание",
    "корпоративное питание",
    "меню",
    "кафе",
    "отель",
    "гостиница",
    "развлечения",
    "реклама",
    "маркетинг",
    "стартап",
    "бренд",
    "потребитель",
]


SPORTS_TERMS = [
    "football",
    "soccer",
    "basketball",
    "boxing",
    "wrestling",
    "tennis",
    "athletics",
    "championship",
    "tournament",
    "match",
    "freestyle wrestling",
    "олимпиада",
    "футбол",
    "баскетбол",
    "бокс",
    "борьба",
    "теннис",
    "чемпионат",
    "турнир",
    "матч",
]


GENERIC_TECH_TERMS = [
    "ai training",
    "artificial intelligence training",
    "software update",
    "app launch",
    "mobile app",
    "tech startup",
]


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("asia-central-news-scanner")


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
    except requests.RequestException as exc:
        logger.warning("Impossible de récupérer %s : %s", url, exc)
        return None


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    if not text:
        return ""

    text = html.unescape(str(text))
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def phrase_present(text, phrase):
    """
    Recherche robuste :
    - les phrases multi-mots sont cherchées directement
    - les mots seuls utilisent des limites pour éviter
      des faux positifs du type "arrest" dans un autre mot.
    """
    text = normalize_text(text)
    phrase = normalize_text(phrase)

    if not text or not phrase:
        return False

    if " " in phrase or "-" in phrase:
        return phrase in text

    pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def find_terms(text, terms):
    found = []

    for term in terms:
        if phrase_present(text, term):
            found.append(term)

    return found


def contains_any(text, terms):
    return bool(find_terms(text, terms))


# ============================================================
# GEOGRAPHY
# ============================================================

def detect_central_asia(text):
    """
    Retourne les pays d'Asie centrale détectés.
    Les variantes anglaises et russes sont prises en compte.
    """
    found = []

    for country, terms in COUNTRY_TERMS_EN.items():
        if contains_any(text, terms):
            found.append(country)
            continue

    for country, terms in COUNTRY_TERMS_RU.items():
        if country not in found and contains_any(text, terms):
            found.append(country)

    if contains_any(text, REGIONAL_TERMS):
        found.append("Central Asia")

    return sorted(set(found))


def detect_regional_actor(text):
    return find_terms(text, REGIONAL_ACTORS)


# ============================================================
# ARTICLE EXTRACTION
# ============================================================

def clean_html_fragment(fragment):
    if not fragment:
        return ""

    soup = BeautifulSoup(fragment, "html.parser")

    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "form",
        "nav",
        "header",
        "footer",
        "aside",
    ]):
        tag.decompose()

    return soup.get_text(" ", strip=True)


def extract_article_body(url):
    """
    Extrait uniquement le contenu éditorial probable.

    IMPORTANT :
    on ne fait plus soup.get_text() sur toute la page.
    Cela évite que le menu, les articles recommandés ou
    le footer déclenchent des mots comme "arrest", "activist", etc.
    """
    content = fetch_url(url)

    if not content:
        return ""

    soup = BeautifulSoup(content, "html.parser")

    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "form",
        "nav",
        "header",
        "footer",
        "aside",
    ]):
        tag.decompose()

    # Supprimer les blocs typiquement non éditoriaux.
    for element in soup.find_all(
        attrs={
            "class": re.compile(
                r"(nav|menu|footer|sidebar|related|recommend|"
                r"newsletter|social|share|advert|promo)",
                re.I,
            )
        }
    ):
        element.decompose()

    for element in soup.find_all(
        attrs={
            "id": re.compile(
                r"(nav|menu|footer|sidebar|related|recommend|"
                r"newsletter|social|share|advert|promo)",
                re.I,
            )
        }
    ):
        element.decompose()

    article = soup.find("article")

    if article:
        text = article.get_text(" ", strip=True)
    else:
        main = soup.find("main")

        if main:
            text = main.get_text(" ", strip=True)
        else:
            # Fallback limité : paragraphes uniquement.
            paragraphs = soup.find_all("p")
            text = " ".join(
                p.get_text(" ", strip=True)
                for p in paragraphs
            )

    text = re.sub(r"\s+", " ", text)

    return text[:30000]


# ============================================================
# RSS DISCOVERY
# ============================================================

def discover_rss_links(page_url):
    content = fetch_url(page_url)

    if not content:
        return []

    soup = BeautifulSoup(content, "html.parser")

    links = []

    # <link rel="alternate" type="application/rss+xml">
    for link in soup.find_all("link"):
        rel = link.get("rel", [])
        href = link.get("href")

        rel_text = " ".join(rel).lower() if isinstance(rel, list) else str(rel).lower()

        if href and (
            "rss" in rel_text
            or "atom" in rel_text
            or "application/rss+xml" in str(link.get("type", "")).lower()
            or "application/atom+xml" in str(link.get("type", "")).lower()
        ):
            links.append(urljoin(page_url, href))

    # Liens visibles contenant RSS / Atom.
    for a in soup.find_all("a", href=True):
        href = a["href"]
        label = a.get_text(" ", strip=True)

        combined = f"{label} {href}".lower()

        if any(word in combined for word in [
            "rss",
            "atom",
            "feed",
            "watchdog",
        ]):
            links.append(urljoin(page_url, href))

    # Déduplication.
    result = []
    seen = set()

    for link in links:
        if link not in seen:
            seen.add(link)
            result.append(link)

    return result


def discover_rferl_specialized_feeds():
    """
    RFE/RL possède plusieurs flux : Watchdog, pays, régions, etc.

    On découvre les liens depuis leur page RSS au lieu de dépendre
    d'URLs codées en dur susceptibles de changer.
    """
    page = "https://www.rferl.org/rssfeeds"

    content = fetch_url(page)

    if not content:
        logger.warning("RFE/RL : impossible d'ouvrir la page RSS.")
        return []

    soup = BeautifulSoup(content, "html.parser")

    wanted = [
        "watchdog",
        "kazakhstan",
        "kyrgyzstan",
        "tajikistan",
        "turkmenistan",
        "uzbekistan",
        "central asia",
        "azerbaijan",
    ]

    feeds = []

    for a in soup.find_all("a", href=True):
        href = urljoin(page, a["href"])
        label = a.get_text(" ", strip=True)

        combined = normalize_text(f"{label} {href}")

        if any(term in combined for term in wanted):
            feeds.append((label, href))

    # Déduplication
    result = []
    seen = set()

    for label, href in feeds:
        if href not in seen:
            seen.add(href)
            result.append((label, href))

    logger.info(
        "RFE/RL : %d flux spécialisés découverts.",
        len(result),
    )

    for label, href in result:
        logger.info("  RFE/RL feed : %s -> %s", label, href)

    return result


# ============================================================
# RSS PARSING
# ============================================================

def parse_feed(feed_url, source_name):
    logger.info("Lecture RSS : %s", feed_url)

    try:
        response = requests.get(
            feed_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        parsed = feedparser.parse(response.content)

    except requests.RequestException as exc:
        logger.warning(
            "%s : erreur RSS %s : %s",
            source_name,
            feed_url,
            exc,
        )
        return []

    if not parsed.entries:
        logger.warning(
            "%s : RSS trouvé mais aucun article.",
            source_name,
        )
        return []

    articles = []

    for entry in parsed.entries[:MAX_FEED_ENTRIES]:

        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()

        summary = (
            entry.get("summary")
            or entry.get("description")
            or ""
        )

        summary = clean_html_fragment(summary)

        published = (
            entry.get("published")
            or entry.get("updated")
            or ""
        )

        published_parsed = (
            entry.get("published_parsed")
            or entry.get("updated_parsed")
        )

        timestamp = None

        if published_parsed:
            try:
                timestamp = datetime(
                    *published_parsed[:6],
                    tzinfo=timezone.utc,
                )
            except Exception:
                timestamp = None

        if not title or not link:
            continue

        articles.append({
            "source": source_name,
            "title": title,
            "summary": summary,
            "url": link,
            "published": published,
            "timestamp": timestamp,
            "body": "",
        })

    logger.info(
        "%s : %d articles RSS récupérés.",
        source_name,
        len(articles),
    )

    return articles


# ============================================================
# HTML FALLBACK
# ============================================================

def extract_html_articles(source):
    url = source["url"]

    content = fetch_url(url)

    if not content:
        return []

    soup = BeautifulSoup(content, "html.parser")

    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "form",
    ]):
        tag.decompose()

    articles = []
    seen_urls = set()

    # Priorité aux balises article.
    candidates = soup.find_all("article")

    if not candidates:
        candidates = soup.find_all(
            ["h1", "h2", "h3"]
        )

    for candidate in candidates[:MAX_HTML_ARTICLES]:

        if candidate.name in ["h1", "h2", "h3"]:
            heading = candidate
        else:
            heading = candidate.find(
                ["h1", "h2", "h3"]
            )

        if not heading:
            continue

        title = heading.get_text(" ", strip=True)

        if not title or len(title) < 10:
            continue

        link = heading.find_parent("a", href=True)

        if link:
            href = link["href"]
        else:
            link = candidate.find("a", href=True)
            href = link["href"] if link else None

        if not href:
            continue

        full_url = urljoin(url, href)

        if full_url in seen_urls:
            continue

        seen_urls.add(full_url)

        summary = ""

        if candidate.name == "article":
            summary = candidate.get_text(
                " ",
                strip=True,
            )

        articles.append({
            "source": source["name"],
            "title": title,
            "summary": summary[:5000],
            "url": full_url,
            "published": "",
            "timestamp": None,
            "body": "",
        })

    logger.info(
        "%s : %d articles HTML récupérés.",
        source["name"],
        len(articles),
    )

    return articles


# ============================================================
# SCORING
# ============================================================

def classify_article(article):
    """
    V3 :
    
    1. Le titre + résumé sont la source principale.
    2. Le corps sert uniquement de confirmation.
    3. Les mots de navigation ne peuvent plus créer un signal.
    4. Les événements géopolitiques majeurs comme le SCO
       peuvent être pertinents même sans être "droits humains".
    """

    title = normalize_text(article["title"])
    summary = normalize_text(article.get("summary", ""))

    headline_text = f"{title} {summary}".strip()

    # Corps uniquement pour confirmation.
    body = normalize_text(article.get("body", ""))

    score = 0
    reasons = []

    # --------------------------------------------------------
    # GÉOGRAPHIE
    # --------------------------------------------------------

    geography = detect_central_asia(headline_text)

    # Si le titre/résumé ne suffit pas, on regarde le corps.
    if not geography and body:
        geography = detect_central_asia(body)

    if geography:
        score += 5
        reasons.append(
            "géographie: " + ", ".join(geography)
        )

    regional_actors = detect_regional_actor(headline_text)

    if regional_actors:
        score += 2
        reasons.append(
            "acteur régional: " + ", ".join(regional_actors[:5])
        )

    # --------------------------------------------------------
    # DROITS HUMAINS / DISSIDENCE
    # --------------------------------------------------------

    hr_terms = find_terms(
        headline_text,
        HUMAN_RIGHTS_TERMS,
    )

    if hr_terms:
        # Plusieurs signaux valent davantage.
        if len(hr_terms) >= 2:
            score += 8
        else:
            score += 5

        reasons.append(
            "droits humains/dissidence: "
            + ", ".join(hr_terms[:6])
        )

    # --------------------------------------------------------
    # POLITIQUE
    # --------------------------------------------------------

    political_terms = find_terms(
        headline_text,
        POLITICAL_TERMS,
    )

    if political_terms:
        score += 2
        reasons.append(
            "politique: "
            + ", ".join(political_terms[:5])
        )

    # --------------------------------------------------------
    # ÉVÉNEMENT RÉGIONAL IMPORTANT
    # --------------------------------------------------------

    event_terms = find_terms(
        headline_text,
        REGIONAL_EVENT_TERMS,
    )

    if event_terms:
        score += 6
        reasons.append(
            "événement régional: "
            + ", ".join(event_terms[:5])
        )

    # --------------------------------------------------------
    # ÉCONOMIE / ÉNERGIE
    # --------------------------------------------------------

    economic_terms = find_terms(
        headline_text,
        ECONOMIC_TERMS,
    )

    if economic_terms and geography:
        score += 2
        reasons.append(
            "économie/énergie: "
            + ", ".join(economic_terms[:5])
        )

    # --------------------------------------------------------
    # SIGNALS DE RÉPRESSION
    # --------------------------------------------------------

    repression_terms = [
        "arrested",
        "arrest",
        "detained",
        "detention",
        "imprisoned",
        "jail",
        "sentenced",
        "convicted",
        "banned",
        "raided",
        "crackdown",
        "repression",
        "torture",
        "задержан",
        "задержана",
        "задержали",
        "арестован",
        "арестована",
        "арестовали",
        "осужден",
        "осуждён",
        "осуждена",
        "приговорен",
        "приговорена",
        "репрессии",
        "пытки",
    ]

    repression_found = find_terms(
        headline_text,
        repression_terms,
    )

    if repression_found and geography:
        score += 5
        reasons.append(
            "action répressive: "
            + ", ".join(repression_found[:5])
        )

    # --------------------------------------------------------
    # CORPS DE L'ARTICLE = CONFIRMATION UNIQUEMENT
    # --------------------------------------------------------

    if body:
        body_hr = find_terms(
            body,
            HUMAN_RIGHTS_TERMS,
        )

        body_geo = detect_central_asia(body)

        # Le corps peut renforcer un article déjà pertinent.
        if body_hr and geography:
            score += min(3, len(body_hr))
            reasons.append(
                "confirmation article: droits humains"
            )

        if body_geo and not geography:
            score += 2
            reasons.append(
                "confirmation article: géographie"
            )

    # --------------------------------------------------------
    # EXCLUSIONS BUSINESS / CORPORATE
    # --------------------------------------------------------

    business_found = find_terms(
        headline_text,
        GENERIC_BUSINESS_TERMS,
    )

    if business_found:
        score -= 10
        reasons.append(
            "hors sujet business: "
            + ", ".join(business_found[:5])
        )

    # --------------------------------------------------------
    # EXCLUSIONS SPORTS
    # --------------------------------------------------------

    sports_found = find_terms(
        headline_text,
        SPORTS_TERMS,
    )

    if sports_found:
        score -= 12
        reasons.append(
            "hors sujet sport: "
            + ", ".join(sports_found[:5])
        )

    # --------------------------------------------------------
    # EXCLUSIONS TECH GÉNÉRIQUE
    # --------------------------------------------------------

    tech_found = find_terms(
        headline_text,
        GENERIC_TECH_TERMS,
    )

    if tech_found and not geography:
        score -= 8
        reasons.append(
            "hors sujet tech"
        )

    # --------------------------------------------------------
    # RÈGLE DE PERTINENCE
    # --------------------------------------------------------

    # Un événement régional important passe même sans HR.
    is_major_regional_event = bool(event_terms and geography)

    # Droits humains + géographie = très bon candidat.
    is_human_rights = bool(hr_terms and geography)

    # Politique seule ne suffit pas.
    is_political = bool(political_terms and geography)

    # Économie seule ne suffit pas.
    is_economic = bool(economic_terms and geography)

    # Deux signaux régionaux peuvent suffire.
    has_regional_context = bool(
        geography
        and (
            political_terms
            or economic_terms
            or regional_actors
        )
    )

    relevant = (
        is_human_rights
        or is_major_regional_event
        or (
            score >= 7
            and has_regional_context
        )
        or (
            score >= 8
            and is_political
        )
        or (
            score >= 8
            and is_economic
            and regional_actors
        )
    )

    # Un article business fortement identifié ne passe pas.
    if business_found:
        relevant = False

    # Un article sportif ne passe jamais.
    if sports_found:
        relevant = False

    # --------------------------------------------------------
    # CAS SPÉCIAL : SCO
    # --------------------------------------------------------

    # Le SCO est explicitement considéré comme intéressant
    # pour le scanner régional.
    if (
        geography
        and (
            "sco" in event_terms
            or "shanghai cooperation organization" in event_terms
            or "shanghai cooperation organisation" in event_terms
            or "шанхайская организация сотрудничества" in event_terms
        )
        and not sports_found
        and not business_found
    ):
        relevant = True

        if "événement régional majeur: SCO" not in reasons:
            reasons.append("événement régional majeur: SCO")

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    logger.info(
        "%s | score=%d | relevant=%s | %s",
        article["title"],
        score,
        relevant,
        "; ".join(reasons) if reasons else "aucun signal",
    )

    article["score"] = score
    article["relevant"] = relevant
    article["reasons"] = reasons

    return article


# ============================================================
# ARTICLE ENRICHMENT
# ============================================================

def enrich_articles(articles):
    """
    On ne télécharge pas toutes les pages.
    Seulement les meilleurs candidats initiaux.
    """

    # Priorité :
    # - articles sans date en dernier
    # - puis les plus récents
    candidates = sorted(
        articles,
        key=lambda x: (
            x.get("timestamp") or datetime.min.replace(
                tzinfo=timezone.utc
            )
        ),
        reverse=True,
    )

    candidates = candidates[:ARTICLE_PAGE_FETCH_LIMIT]

    for article in candidates:
        try:
            article["body"] = extract_article_body(
                article["url"]
            )
        except Exception as exc:
            logger.warning(
                "Erreur enrichissement %s : %s",
                article["url"],
                exc,
            )

    return articles


# ============================================================
# DÉDUPLICATION
# ============================================================

def deduplicate_articles(articles):
    seen = set()
    result = []

    for article in articles:
        title_key = normalize_text(
            article["title"]
        )

        # Normalisation légère des titres.
        title_key = re.sub(
            r"[^\w\s]",
            "",
            title_key,
        )

        if not title_key:
            continue

        if title_key in seen:
            continue

        seen.add(title_key)
        result.append(article)

    return result


# ============================================================
# TRI
# ============================================================

def article_sort_key(article):
    timestamp = article.get("timestamp")

    if timestamp:
        return timestamp

    return datetime.min.replace(
        tzinfo=timezone.utc
    )


# ============================================================
# FETCH ALL NEWS
# ============================================================

def fetch_all_news():
    all_articles = []

    for source in SOURCES:

        source_articles = []

        # ----------------------------------------------------
        # RSS connus
        # ----------------------------------------------------

        for rss_url in source.get("rss", []):
            parsed = parse_feed(
                rss_url,
                source["name"],
            )

            source_articles.extend(parsed)

        # ----------------------------------------------------
        # RFE/RL : flux spécialisés
        # ----------------------------------------------------

        if source["name"] == "Radio Free Europe / Radio Liberty":

            specialized = (
                discover_rferl_specialized_feeds()
            )

            for label, feed_url in specialized:
                parsed = parse_feed(
                    feed_url,
                    source["name"],
                )

                source_articles.extend(parsed)

        # ----------------------------------------------------
        # Si aucun RSS : découverte RSS
        # ----------------------------------------------------

        if not source_articles:
            discovered = discover_rss_links(
                source["url"]
            )

            for rss_url in discovered[:10]:
                parsed = parse_feed(
                    rss_url,
                    source["name"],
                )

                source_articles.extend(parsed)

        # ----------------------------------------------------
        # Fallback HTML
        # ----------------------------------------------------

        if not source_articles:
            source_articles = extract_html_articles(
                source
            )

        all_articles.extend(
            source_articles
        )

    logger.info(
        "TOTAL avant déduplication : %d articles.",
        len(all_articles),
    )

    all_articles = deduplicate_articles(
        all_articles
    )

    logger.info(
        "TOTAL après déduplication : %d articles.",
        len(all_articles),
    )

    # --------------------------------------------------------
    # Première classification sur titre + résumé.
    # --------------------------------------------------------

    classified = []

    for article in all_articles:
        classify_article(article)
        classified.append(article)

    # --------------------------------------------------------
    # Enrichissement seulement des candidats prometteurs.
    # --------------------------------------------------------

    promising = [
        article
        for article in classified
        if article["relevant"]
        or article["score"] >= 4
    ]

    logger.info(
        "Articles prometteurs à enrichir : %d",
        len(promising),
    )

    enrich_articles(promising)

    # --------------------------------------------------------
    # Reclassification après enrichissement.
    # --------------------------------------------------------

    final_articles = []

    for article in classified:
        if article in promising:
            classify_article(article)

        if article["relevant"]:
            final_articles.append(article)

    # --------------------------------------------------------
    # Tri par date
    # --------------------------------------------------------

    final_articles.sort(
        key=article_sort_key,
        reverse=True,
    )

    logger.info(
        "Articles pertinents finaux : %d",
        len(final_articles),
    )

    return final_articles


# ============================================================
# HTML
# ============================================================

def format_date(article):
    timestamp = article.get("timestamp")

    if timestamp:
        try:
            return timestamp.strftime(
                "%Y-%m-%d %H:%M UTC"
            )
        except Exception:
            pass

    published = article.get("published", "")

    return published or "Date inconnue"


def escape_html(text):
    return (
        html.escape(str(text))
        if text is not None
        else ""
    )


def create_web_page(articles):
    selected = articles[:ARTICLES_TO_DISPLAY]

    generated_at = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d %H:%M UTC")

    cards = []

    for article in selected:

        reasons = article.get(
            "reasons",
            [],
        )

        reasons_html = ""

        if reasons:
            reasons_html = (
                "<div class='reasons'>"
                + escape_html(
                    " • ".join(reasons[:4])
                )
                + "</div>"
            )

        card = f"""
        <article class="card">
            <div class="source">
                {escape_html(article["source"])}
            </div>

            <h2>
                <a href="{escape_html(article["url"])}"
                   target="_blank"
                   rel="noopener noreferrer">
                    {escape_html(article["title"])}
                </a>
            </h2>

            <div class="date">
                {escape_html(format_date(article))}
            </div>

            <p>
                {escape_html(article.get("summary", ""))[:700]}
            </p>

            {reasons_html}
        </article>
        """

        cards.append(card)

    if not cards:
        cards_html = """
        <div class="empty">
            Aucun article pertinent trouvé lors du dernier scan.
        </div>
        """
    else:
        cards_html = "\n".join(cards)

    page = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Central Asia News Scanner</title>

    <style>
        body {{
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;

            max-width: 1000px;
            margin: 0 auto;
            padding: 30px 20px;

            background: #f5f5f5;
            color: #222;
        }}

        h1 {{
            margin-bottom: 5px;
        }}

        .subtitle {{
            color: #666;
            margin-bottom: 30px;
        }}

        .updated {{
            font-size: 13px;
            color: #888;
            margin-bottom: 25px;
        }}

        .card {{
            background: white;
            border-radius: 10px;
            padding: 22px;
            margin-bottom: 18px;
            box-shadow:
                0 2px 8px rgba(0,0,0,0.07);
        }}

        .source {{
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            color: #666;
            margin-bottom: 8px;
        }}

        h2 {{
            margin: 0 0 8px 0;
            font-size: 22px;
            line-height: 1.3;
        }}

        h2 a {{
            color: #111;
            text-decoration: none;
        }}

        h2 a:hover {{
            text-decoration: underline;
        }}

        .date {{
            font-size: 12px;
            color: #888;
            margin-bottom: 14px;
        }}

        p {{
            line-height: 1.6;
            color: #444;
        }}

        .reasons {{
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px solid #eee;
            font-size: 11px;
            color: #888;
        }}

        .empty {{
            background: white;
            padding: 25px;
            border-radius: 10px;
        }}
    </style>
</head>

<body>

    <h1>Central Asia News Scanner</h1>

    <div class="subtitle">
        Actualités récentes d'Asie centrale —
        politique, droits humains, dissidence,
        sécurité, géopolitique et événements régionaux.
    </div>

    <div class="updated">
        Dernier scan : {escape_html(generated_at)}
    </div>

    {cards_html}

</body>
</html>
"""

    with open(
        "index.html",
        "w",
        encoding="utf-8",
    ) as file:
        file.write(page)

    logger.info(
        "index.html généré avec %d articles.",
        len(selected),
    )


# ============================================================
# MAIN
# ============================================================

def main():
    logger.info(
        "=========================================="
    )
    logger.info(
        "Central Asia News Scanner V3"
    )
    logger.info(
        "=========================================="
    )

    articles = fetch_all_news()

    create_web_page(
        articles
    )

    logger.info(
        "Scan terminé."
    )


if __name__ == "__main__":
    main()
