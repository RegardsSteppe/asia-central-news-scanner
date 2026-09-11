from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import feedparser
from bs4 import BeautifulSoup

from http_utils import fetch_url
from text_utils import (
    clean_text,
    clean_title,
    normalize_url,
    parse_date,
)


# ============================================================
# CONFIGURATION DES CONSTANTES
# ============================================================

CACHE_TTL = 3600  # Cache timeout en secondes (1 heure)
REQUEST_TIMEOUT = 30  # Timeout pour les requêtes en secondes
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# Google News ajoute systématiquement " - <nom du site>" à la fin de
# chaque titre dans ses flux RSS (ex. "Foo Sentenced - Human Rights
# Watch") : coupé uniquement pour les flux news.google.com, jamais en
# général, pour ne pas tronquer un vrai titre qui se terminerait
# légitimement par un tiret.
_GOOGLE_NEWS_TITLE_SUFFIX_RE = re.compile(r"\s+-\s+[^-]{2,60}$")


def _strip_google_news_suffix(title: str) -> str:
    return _GOOGLE_NEWS_TITLE_SUFFIX_RE.sub("", title).strip()


def parse_rss(
    content: str,
    source: dict[str, Any],
    feed_url: str = "",
) -> list[dict[str, Any]]:
    feed = feedparser.parse(content or "")

    is_google_news = "news.google.com" in feed_url

    articles: list[dict[str, Any]] = []

    for entry in getattr(feed, "entries", None) or []:
        try:
            title = clean_title(entry.get("title", ""))
            summary = clean_text(
                entry.get("summary")
                or entry.get("description")
                or ""
            )

            link = entry.get("link", "")
        except AttributeError:
            # Entrée mal formée (ne se comporte pas comme un dict) :
            # on l'ignore sans faire échouer tout le flux.
            continue

        if not title or not link:
            continue

        if is_google_news:
            title = _strip_google_news_suffix(title)
            if not title:
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
    seen_urls: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = urljoin(base_url, link.get("href", ""))
        title = clean_title(link.get_text(" ", strip=True))

        if not title or not href:
            continue

        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"}:
            continue

        if not looks_like_article_link(href, title):
            continue

        normalized = normalize_url(href)
        if normalized in seen_urls:
            continue
        seen_urls.add(normalized)

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


# ---------------------------------------------------------------------------
# FILTRAGE DES LIENS D'ARTICLES
# ---------------------------------------------------------------------------

# Segments d'URL clairement non-liés à un article (navigation, utilitaires...).
_NON_ARTICLE_PATH_PATTERNS = (
    "/tag/",
    "/tags/",
    "/category/",
    "/categories/",
    "/author/",
    "/authors/",
    "/page/",
    "/pages/",
    "/search",
    "/feed",
    "/rss",
    "/privacy",
    "/contact",
    "/about",
    "/terms",
    "/login",
    "/signup",
    "/register",
    "/subscribe",
    "/newsletter",
    "/advertise",
    "/careers",
    "/sitemap",
    "/archive",
    "/archives",
    "/wp-admin",
    "/wp-login",
    "/cart",
    "/account",
    # Pages de profil/bio (auteurs, chercheurs, staff) : fréquentes sur
    # les sites de think tanks, elles passaient le filtre générique
    # (titre = juste un nom propre, 2 segments de chemin) faute d'être
    # explicitement exclues — ex. hudson.org/experts/<nom>,
    # fpri.org/contributor/<nom>, eurasianet.org/people/<nom>.
    "/experts/",
    "/expert/",
    "/people/",
    "/person/",
    "/staff/",
    "/team/",
    "/scholars/",
    "/scholar/",
    "/fellows/",
    "/fellow/",
    "/contributors/",
    "/contributor/",
    "/profile/",
    "/profiles/",
    "/bio/",
    "/bios/",
    # Pages thématiques/outils génériques (pas un article précis) : le
    # filtre générique (titre suffisant + 2 segments de chemin) les
    # laissait passer, ex. Amnesty amnesty.org/en/what-we-do/
    # armed-conflict/, CPJ cpj.org/data/missing, RSF rsf.org/fr/
    # pays-<pays> (page listant tous les articles sur un pays,
    # pas un article) ou rsf.org/fr/classement (l'outil de
    # classement, pas une actualité).
    "/what-we-do/",
    "/human-rights-education",
    "/issue/",
    "/issues/",
    "/topic/",
    "/topics/",
    "/petition/",
    "/petitions/",
    "/pays-",
    "/classement",
    "/barometre",
    "/data/",
)

# Segments d'URL qui indiquent plutôt une page d'article.
_ARTICLE_PATH_PATTERNS = (
    "/news/",
    "/article/",
    "/articles/",
    "/stories/",
    "/story/",
    "/posts/",
    "/post/",
    "/opinion/",
    "/blog/",
)

# Textes de lien trop génériques pour être considérés comme un titre d'article.
_GENERIC_LINK_TEXTS = {
    "read more",
    "lire la suite",
    "next",
    "next page",
    "previous",
    "previous page",
    "home",
    "accueil",
    "back",
    "more",
    "learn more",
    "click here",
    "here",
    "login",
    "log in",
    "sign up",
    "signup",
    "register",
    "subscribe",
    "contact",
    "contact us",
    "about",
    "about us",
    "privacy",
    "privacy policy",
    "terms",
    "terms of service",
    "search",
    "menu",
    "share",
    "tweet",
    "facebook",
    "twitter",
    "print",
    "comments",
    "continue reading",
    "...",
    "»",
    "«",
    ">>",
    "<<",
}

# Motif d'une date dans le chemin d'URL, ex. /2024/03/15/ ou /2024-03-15/
_DATE_PATH_RE = re.compile(r"/(19|20)\d{2}[/-](0?[1-9]|1[0-2])[/-]")

# Longueur minimale d'un titre de lien pour être considéré comme un article.
_MIN_TITLE_LENGTH = 8
_MIN_TITLE_WORDS = 2


def _has_repeated_path_prefix(path: str) -> bool:
    """
    Détecte un chemin qui répète son propre préfixe à l'identique
    (ex. /en/region/x/en/region/x/y) — trouvé en réel sur FIDH : leur
    page cible sert des liens relatifs sans "/" initial, qui se
    combinent avec une URL source déjà profonde pour produire une URL
    cassée. Toujours un bug de construction d'URL, jamais un article
    légitime.
    """
    segments = [segment for segment in path.split("/") if segment]
    n = len(segments)

    for prefix_len in range(2, n // 2 + 1):
        if segments[:prefix_len] == segments[prefix_len:2 * prefix_len]:
            return True

    return False


def looks_like_article_link(url: str, title: str) -> bool:
    """
    Heuristique conservatrice pour ne garder que les liens
    ressemblant à de vrais articles.

    Rejette les liens de navigation/catégories/tags/pages
    utilitaires ainsi que les libellés de lien trop génériques.
    """
    if not url or not title:
        return False

    normalized_title = title.strip().lower()

    if len(normalized_title) < _MIN_TITLE_LENGTH:
        return False

    if len(normalized_title.split()) < _MIN_TITLE_WORDS:
        return False

    if normalized_title in _GENERIC_LINK_TEXTS:
        return False

    parsed = urlparse(url)
    path = parsed.path.lower()

    if not path or path == "/":
        return False

    if any(pattern in path for pattern in _NON_ARTICLE_PATH_PATTERNS):
        return False

    if _has_repeated_path_prefix(path):
        return False

    if any(pattern in path for pattern in _ARTICLE_PATH_PATTERNS):
        return True

    if _DATE_PATH_RE.search(path):
        # Une simple archive mensuelle/journalière (ex. "/2024/03/") n'a
        # pas de segment supplémentaire pour l'article lui-même : ce n'est
        # pas un article mais une page de liste, on la rejette.
        segments = [segment for segment in path.split("/") if segment]
        return len(segments) >= 3

    # Par défaut, accepter les chemins suffisamment spécifiques
    # (au moins deux segments non vides) pour rester conservateur
    # sans être trop restrictif sur les sites qui ne suivent pas
    # les motifs ci-dessus.
    segments = [segment for segment in path.split("/") if segment]
    if len(segments) < 2:
        return False

    return True


# Emplacements usuels de la date de publication dans le <head> d'une
# page d'article : (nom de balise, attributs à matcher, attribut à lire).
_DATE_META_LOCATIONS = (
    ("meta", {"property": "article:published_time"}, "content"),
    ("meta", {"property": "og:article:published_time"}, "content"),
    ("meta", {"name": "publish-date"}, "content"),
    ("meta", {"name": "publish_date"}, "content"),
    ("meta", {"name": "publication_date"}, "content"),
    ("meta", {"name": "date"}, "content"),
    ("meta", {"name": "sailthru.date"}, "content"),
    ("meta", {"itemprop": "datePublished"}, "content"),
    ("meta", {"name": "parsely-pub-date"}, "content"),
)


def extract_published_date(soup: BeautifulSoup):
    """
    Cherche la date de publication d'une page d'article dans les
    métadonnées standard (Open Graph, schema.org, etc.) puis dans une
    balise <time>. Retourne un datetime (via parse_date) ou None.
    """
    for tag_name, attrs, source_attr in _DATE_META_LOCATIONS:
        tag = soup.find(tag_name, attrs=attrs)
        if not tag:
            continue

        value = tag.get(source_attr)
        parsed = parse_date(value)

        if parsed:
            return parsed

    time_tag = soup.find("time")

    if time_tag:
        value = time_tag.get("datetime") or time_tag.get_text(strip=True)
        parsed = parse_date(value)

        if parsed:
            return parsed

    return None


def _significant_words(text: str) -> set[str]:
    return set(re.findall(r"[^\W\d_]{4,}", (text or "").lower(), flags=re.UNICODE))


def _page_matches_expected_title(
    expected_title: str,
    soup: BeautifulSoup,
) -> bool:
    """
    Certains sites répondent 200 OK mais redirigent silencieusement
    une URL d'article invalide/supprimée vers leur page d'accueil (ou
    une autre page générique) — un code HTTP normal ne peut pas
    détecter ça. On compare le titre attendu (déjà connu depuis le
    flux/la page de liste) aux titres réellement présents sur la page
    récupérée ; en cas de recouvrement trop faible, on considère qu'on
    n'a pas la bonne page.
    """
    expected_words = _significant_words(expected_title)

    if len(expected_words) < 2:
        return True

    candidates = []

    title_tag = soup.find("title")
    if title_tag:
        candidates.append(title_tag.get_text())

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title:
        candidates.append(og_title.get("content", ""))

    h1 = soup.find("h1")
    if h1:
        candidates.append(h1.get_text())

    page_words: set[str] = set()
    for candidate in candidates:
        page_words |= _significant_words(candidate)

    if not page_words:
        return True

    overlap = expected_words & page_words
    return len(overlap) / len(expected_words) >= 0.3


def extract_body(
    url: str,
    source: dict[str, Any] | None = None,
    force_refresh: bool = False,
    expected_title: str = "",
) -> tuple[str, Any]:
    content = fetch_url(
        url,
        headers=HEADERS,
        request_timeout=REQUEST_TIMEOUT,
        cache_ttl=CACHE_TTL,
        force_refresh=force_refresh,
    )

    soup = BeautifulSoup(content, "html.parser")

    if expected_title and not _page_matches_expected_title(expected_title, soup):
        # On n'a probablement pas atterri sur l'article (redirection
        # douce, page supprimée...) : mieux vaut ne rien renvoyer que
        # de scorer/afficher le contenu d'une page sans rapport.
        return "", None

    published_date = extract_published_date(soup)

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

    return clean_text(text), published_date


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
