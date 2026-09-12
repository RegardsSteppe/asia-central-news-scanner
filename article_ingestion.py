from __future__ import annotations

import json
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

            # La <description> Google News n'est jamais un vrai résumé :
            # c'est juste le titre ré-empaqueté en lien HTML suivi du
            # nom de la source ('<a href="...">Titre</a> <font ...>
            # Source</font>'), affiché tel quel sur le site sans rien
            # apporter. Le vrai résumé, s'il existe, viendra de
            # l'enrichissement (corps de l'article).
            summary = ""

        # Repéré en audit réel le 2026-09-11 : le flux Google News
        # (site:hrw.org...) indexe aussi de vieilles pages de
        # navigation du site ("Table of Contents Europe & Central
        # Asia", "Countries") au même titre que les vrais articles.
        # looks_like_article_link() n'était jamais appliqué aux
        # entrées RSS (seulement au scraping HTML) : le titre seul
        # ("Countries" — 1 mot) suffit à les rejeter. Pour Google
        # News uniquement le titre compte : son URL de redirection
        # opaque (news.google.com/rss/articles/<hash>) contient
        # littéralement "/rss", ce que looks_like_article_link()
        # rejetterait toujours à tort si on lui passait cette URL. Le
        # suffixe Google News doit être retiré AVANT ce test, sinon
        # "Countries - Human Rights Watch" (5 mots) masquerait que le
        # vrai titre "Countries" (1 mot) devrait être rejeté.
        if is_google_news:
            if not _title_passes_generic_filter(title):
                continue
        elif not looks_like_article_link(link, title):
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
    # Repéré en audit réel le 2026-09-11 : encore le même filtre par
    # défaut (titre suffisant + 2 segments) qui laissait passer des
    # pages-outils, ex. amnesty.org/en/get-involved/take-action/
    # (page de campagne générique, pas un article précis) ou les
    # microsites OHCHR Special Procedures — spcommreports.ohchr.org/
    # Tmsearch/... (moteur de recherche) et spinternet.ohchr.org/
    # _Layouts/.../ViewAllCountryMandates.aspx (page ASP.NET/
    # SharePoint de navigation, pas un article).
    "/get-involved/",
    "/tmsearch/",
    "_layouts/",
    # Repéré en audit réel le 2026-09-11 (niveau C) : pages de listing/
    # agrégation, pas un article précis — uhrp.org/news_cat/uhrp-in-
    # the-news/ (archive de catégorie WordPress) et hronikatm.com/
    # other-media/iz-drugih-smi/ ("depuis d'autres médias", une
    # rubrique de republication, pas un contenu original).
    "/news_cat/",
    "/other-media/",
    # "/sports/" : contenu hors-sujet plutôt que "pas un article" à
    # proprement parler, mais Al Jazeera par pays agrège tout le site
    # (sport, culture, économie...) — un résultat de tennis atteignait
    # le niveau C via un simple homonyme ("court" de tennis matchant
    # le vocabulaire judiciaire). Exclu à la source plutôt que de
    # complexifier le scoring pour un cas hors périmètre du projet.
    "/sports/",
    # uscirf.gov/news-room/uscirf-spotlight : page d'émission
    # (liste tous les épisodes du podcast), pas un épisode précis.
    "/uscirf-spotlight",
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
    # Repéré en audit réel le 2026-09-11 (indexé par Google News
    # depuis d'anciennes pages hrw.org) : sommaire/index générique,
    # pas un article.
    "table of contents",
    "table of contents europe & central asia",
    "countries",
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


def _title_passes_generic_filter(title: str) -> bool:
    """
    Vérifications sur le seul titre (longueur, nombre de mots,
    libellés génériques) — réutilisées pour les entrées RSS Google
    News, dont l'URL est un lien de redirection opaque
    (news.google.com/rss/articles/<hash>) sur lequel les vérifications
    de chemin de looks_like_article_link() n'ont aucun sens (il
    contient toujours littéralement "/rss", ce qui les rejetterait
    toutes à tort).
    """
    if not title:
        return False

    normalized_title = title.strip().lower()

    if len(normalized_title) < _MIN_TITLE_LENGTH:
        return False

    if len(normalized_title.split()) < _MIN_TITLE_WORDS:
        return False

    if normalized_title in _GENERIC_LINK_TEXTS:
        return False

    return True


def looks_like_article_link(url: str, title: str) -> bool:
    """
    Heuristique conservatrice pour ne garder que les liens
    ressemblant à de vrais articles.

    Rejette les liens de navigation/catégories/tags/pages
    utilitaires ainsi que les libellés de lien trop génériques.
    """
    if not url or not title:
        return False

    if not _title_passes_generic_filter(title):
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


def _dates_from_json_ld(soup: BeautifulSoup):
    """
    Certains sites (Al Jazeera, HRF...) n'exposent leur date de
    publication que dans un bloc JSON-LD schema.org
    (<script type="application/ld+json">datePublished...), sans
    aucune des balises meta/time classiques. On y cherche
    "datePublished" (à défaut "dateCreated"), y compris dans un
    @graph imbriqué.
    """
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.get_text() or "")
        except (ValueError, TypeError):
            continue

        candidates = data if isinstance(data, list) else [data]

        expanded = []
        for item in candidates:
            if isinstance(item, dict) and isinstance(item.get("@graph"), list):
                expanded.extend(item["@graph"])
            else:
                expanded.append(item)

        for item in expanded:
            if not isinstance(item, dict):
                continue

            for key in ("datePublished", "dateCreated"):
                parsed = parse_date(item.get(key))
                if parsed:
                    return parsed

    return None


def extract_published_date(soup: BeautifulSoup):
    """
    Cherche la date de publication d'une page d'article dans les
    métadonnées standard (Open Graph, schema.org, etc.), une balise
    <time>, puis en dernier recours un bloc JSON-LD. Retourne un
    datetime (via parse_date) ou None.
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

    return _dates_from_json_ld(soup)


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


def _distinctive_words(text: str, top_n: int = 2) -> set[str]:
    # Les `top_n` mots significatifs les plus longs d'un texte, plutôt
    # qu'un simple seuil de longueur : un mot long mais générique
    # ("Armenia", "corruption"...) revient dans de nombreux articles
    # différents d'une même source et ne suffit pas à distinguer LEUR
    # sujet réel — repéré le 2026-09-12 sur occrp.org, où deux articles
    # sans rapport partagent souvent "Armenia"/"probe". Le terme
    # vraiment spécifique à un article (un nom propre, un terme rare)
    # est presque toujours parmi les plus longs du titre.
    words = sorted(_significant_words(text), key=lambda w: (-len(w), w))
    return set(words[:top_n])


def _body_matches_expected_title(expected_title: str, body_text: str) -> bool:
    """
    Filet de sécurité complémentaire à _page_matches_expected_title() :
    repéré le 2026-09-12 sur occrp.org (le <title>/<h1> de la page est
    correct, mais le conteneur choisi comme corps de l'article est en
    fait une vignette "derniers articles" sans rapport avec l'article
    demandé) et hrf.org (le corps extrait n'est que "Human Rights
    Foundation", un fragment de boilerplate). Exige qu'au moins un
    terme distinctif du titre attendu apparaisse dans le texte
    réellement extrait — pas une fraction de recouvrement globale
    comme pour le titre de page, car un corps d'article reformule
    souvent son titre plutôt que de le répéter mot pour mot.
    """
    expected_distinctive = _distinctive_words(expected_title)

    if not expected_distinctive:
        return True

    # Cherche les mots distinctifs du TITRE n'importe où dans le
    # vocabulaire du corps entier — pas seulement parmi les mots les
    # plus longs DU CORPS. Un vrai article de plusieurs centaines de
    # mots contient presque toujours des mots plus longs que les
    # termes-clé du titre (noms propres, mots composés, artefacts de
    # mise en forme...) sans rapport avec eux ; restreindre aux mots
    # les plus longs du corps rejetterait alors la quasi-totalité des
    # articles légitimes.
    return bool(expected_distinctive & _significant_words(body_text))


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

    # Repéré le 2026-09-12 sur turkmen.news : le thème WordPress marque
    # chaque commentaire avec la balise sémantique <article> (pratique
    # courante), et soup.find("article") ci-dessous récupérait alors le
    # fil de commentaires au lieu du corps réel. On retire toute
    # section dont la classe/l'id évoque des commentaires avant de
    # chercher le conteneur principal.
    for tag in soup.find_all(
        lambda t: (
            (t.get("class") and any("comment" in c.lower() for c in t.get("class", [])))
            or (t.get("id") and "comment" in t.get("id", "").lower())
        )
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

    text = clean_text(text)

    if expected_title and not _body_matches_expected_title(expected_title, text):
        # Le <title>/<h1> de la page correspondait bien (sinon on
        # serait déjà sorti plus haut), mais le conteneur choisi comme
        # corps de l'article n'a aucun terme distinctif en commun avec
        # le titre attendu — probablement un widget/une vignette sans
        # rapport plutôt que le vrai contenu (voir occrp.org, hrf.org).
        return "", None

    return text, published_date


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
        # Langue déclarée de la source (voir sources.py) : point de
        # départ pour scoper en scoring les vérifications regex
        # coûteuses spécifiques à une langue (morphologie russe, motifs
        # farsi...) sur les articles concernés plutôt que sur tout le
        # corpus. Pour les quelques sources qui ne déclarent aucune
        # langue unique (absente, ou "multi"), classify_article()
        # détecte la langue réelle de chaque article et réécrit ce
        # champ en conséquence — donc ce n'est qu'une valeur initiale,
        # pas la langue finale garantie de l'article.
        "language": source.get("language", ""),
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
