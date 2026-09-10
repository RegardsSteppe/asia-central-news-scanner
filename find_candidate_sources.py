"""
Outil ponctuel de découverte de sources — PAS branché sur le scan
quotidien (news-scanner.yml). Idée : les meilleurs articles (niveau A)
citent souvent, dans leur corps, l'ONG, l'organisme ou le rapport qui a
motivé l'article. En listant les domaines externes vers lesquels ces
articles pointent et qui ne sont pas déjà dans sources.py, on obtient
des pistes concrètes de nouvelles sources plutôt que de deviner.

Usage (nécessite un accès réseau sortant, donc à lancer via le workflow
find-sources.yml plutôt qu'en local sur un environnement restreint) :

    python find_candidate_sources.py --csv articles.csv --levels A
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from http_utils import fetch_url
from sources import SOURCES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
REQUEST_TIMEOUT = 30
CACHE_TTL = 3600

# Domaines de navigation/réseaux sociaux/pub/analytics — jamais des
# sources d'actualité, on les écarte pour ne pas polluer le résultat.
# Liste enrichie après un premier run réel (voir commit history) :
# telegram.me/wa.me/vk.*/ok.ru/bsky.app/dzen.ru/yandex.* et les
# widgets de dons/cookies passaient au travers de la première version.
_EXCLUDED_DOMAIN_SUFFIXES = (
    "facebook.com", "fb.com", "twitter.com", "x.com", "instagram.com",
    "youtube.com", "youtu.be", "linkedin.com", "whatsapp.com", "wa.me",
    "t.me", "telegram.org", "telegram.me", "pinterest.com", "reddit.com",
    "tiktok.com", "threads.net", "threads.com", "bsky.app",
    "vk.com", "vk.ru", "ok.ru", "dzen.ru", "yandex.ru", "yandex.com",
    "ya.ru", "google.com", "google.co", "apple.com", "play.google.com",
    "wikipedia.org", "wikimedia.org", "wikidata.org",
    "doubleclick.net", "googletagmanager.com", "google-analytics.com",
    "googlesyndication.com", "amazon-adsystem.com", "adnxs.com",
    "taboola.com", "outbrain.com", "criteo.com", "cloudflareinsights.com",
    "hotjar.com", "sentry.io", "disqus.com", "addtoany.com",
    "mailchimp.com", "typepad.com", "cookiedatabase.org", "donorbox.org",
    "paypal.com", "akamaized.net",
    # Sites-sœurs de RFE/RL, sous d'autres noms de domaine (mêmes
    # articles reliés en interne, pas des sources tierces) — voir
    # RFE/RL dans sources.py.
    "currenttime.tv", "radiomarsho.com", "azatliq.org", "azattyqasia.org",
)


def domain_of(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def _registrable_label(domain: str) -> str:
    """Second-to-last label, e.g. "aljazeera" for "training.aljazeera.net"."""
    parts = domain.split(".")
    return parts[-2] if len(parts) >= 2 else domain


def is_excluded(domain: str) -> bool:
    return any(
        domain == suffix or domain.endswith("." + suffix)
        for suffix in _EXCLUDED_DOMAIN_SUFFIXES
    )


def is_same_organization(domain: str, own_domain: str) -> bool:
    """
    Catches an outlet's own network under a different domain name (e.g.
    an article on aljazeera.com linking to careers.aljazeera.net, or
    about.rferl.org from an article on rferl.org) — same registrable
    label, different subdomain or TLD. Not a citation to a third party.
    """
    return _registrable_label(domain) == _registrable_label(own_domain)


def known_domains() -> set[str]:
    """Domaines déjà couverts par une entrée de sources.py."""
    domains: set[str] = set()

    for source in SOURCES:
        for url in (
            [source.get("url", "")]
            + source.get("feeds", [])
            + source.get("fallbacks", [])
        ):
            if url:
                domains.add(domain_of(url))

    return domains


def extract_outbound_domains(html: str, own_domain: str) -> set[str]:
    """External, non-boilerplate domains linked from an article page."""
    soup = BeautifulSoup(html, "html.parser")
    domains: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if not href.startswith("http"):
            continue

        domain = domain_of(href)
        if not domain or is_excluded(domain):
            continue
        if is_same_organization(domain, own_domain):
            continue

        domains.add(domain)

    return domains


def find_candidates(
    rows: list[dict],
    known: set[str],
) -> tuple[dict[str, int], dict[str, tuple[str, str]]]:
    counts: dict[str, int] = defaultdict(int)
    examples: dict[str, tuple[str, str]] = {}

    for row in rows:
        url = row.get("url")
        if not url:
            continue

        own_domain = domain_of(url)

        try:
            html = fetch_url(url, HEADERS, REQUEST_TIMEOUT, CACHE_TTL)
        except Exception as exc:  # noqa: BLE001 - outil diagnostic, on continue
            print(f"  [erreur] {url}: {exc}")
            continue

        for domain in extract_outbound_domains(html, own_domain):
            if domain in known:
                continue

            counts[domain] += 1
            examples.setdefault(domain, (row.get("title", ""), url))

    return counts, examples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default="articles.csv")
    parser.add_argument(
        "--levels",
        default="A",
        help="Niveaux à analyser, séparés par des virgules (ex: A ou A,B)",
    )
    args = parser.parse_args()

    levels = {level.strip() for level in args.levels.split(",") if level.strip()}

    with open(args.csv, encoding="utf-8") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row.get("level") in levels
        ]

    print(f"Analyse de {len(rows)} article(s) de niveau {args.levels}...\n")

    known = known_domains()
    counts, examples = find_candidates(rows, known)

    if not counts:
        print("Aucun domaine externe candidat trouvé.")
        return

    print(f"{'Domaine':40s} {'citations':>10s}  Exemple")
    print("-" * 100)

    for domain, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        title, url = examples[domain]
        print(f"{domain:40s} {count:10d}  {title[:60]!r} ({url})")


if __name__ == "__main__":
    main()
