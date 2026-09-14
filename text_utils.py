from __future__ import annotations

import html
import re
import unicodedata
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse

from boilerplate import BOILERPLATE_PAR_SOURCE


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


# Bloc « articles recommandés » à délimiteurs explicites. Al Jazeera
# aplatit ses listes en texte : "Recommended Stories list of 3 items
# list 1 of 3 <titre> ... end of list". Les bornes étant nettes, on
# retire exactement la portion concernée où qu'elle se trouve.
_BLOC_RECOMMANDE = re.compile(
    r"Recommended Stories\s+list of \d+ items?.*?end of list",
    re.IGNORECASE | re.DOTALL,
)

# Marqueurs de pied de page qui introduisent des titres d'AUTRES
# articles. Contrairement au bloc ci-dessus ils n'ont pas de fin
# explicite, donc on ne peut que tronquer — et tronquer n'est sûr que
# si le marqueur est déjà en fin de texte (voir _SEUIL_QUEUE).
_MARQUEURS_QUEUE = re.compile(
    r"(?:Читайте также"
    r"|Related (?:Stories|Articles|Coverage|News)"
    r"|Most (?:Read|Popular)"
    r"|You may also like"
    r"|Follow us on)",
    re.IGNORECASE,
)

# Un marqueur situé dans les derniers 20 % du texte est un pied de
# page ; plus haut, c'est un renvoi inséré au fil de l'article et le
# vrai contenu continue après lui. La distinction n'est pas
# cosmétique : sur Novastan, « Lire aussi sur Novastan : ... » apparaît
# au tiers de l'article, avec 4 000 à 6 000 caractères de corps réel
# derrière — tronquer là détruirait l'article. Ces renvois en ligne
# sont donc laissés en place, faute de borne de fin fiable.
_SEUIL_QUEUE = 0.80


def strip_related_blocks(text: Any) -> str:
    """
    Retire du corps d'un article les blocs qui citent D'AUTRES
    articles.

    Repéré le 2026-09-14 par le harnais de caractérisation :
    « Turkmenistan leader's son wins presidential election » montait de
    E à C parce que son corps contenait "Recommended Stories ...
    Turkmenistan's dissidents fear crackdown in Turkish exile ...",
    c'est-à-dire le titre d'un autre article. Le scoring lisait un
    ancrage répressif qui n'appartenait pas à l'article scoré. Sur
    9 235 articles archivés, environ un millier de corps portent un
    bloc de ce genre.

    La fonction est idempotente : la repasser sur un texte déjà
    nettoyé ne change rien, ce qui permet de l'appliquer aussi bien à
    l'extraction qu'en rattrapage sur l'archive existante.
    """
    if not text:
        return ""

    text = str(text)

    text = _BLOC_RECOMMANDE.sub(" ", text)

    marqueur = _MARQUEURS_QUEUE.search(text)
    if marqueur and marqueur.start() >= _SEUIL_QUEUE * len(text):
        text = text[: marqueur.start()]

    return re.sub(r"\s+", " ", text).strip()


def strip_boilerplate(text: Any, source: Any = "") -> str:
    """
    Retire le pied de page que `source` recopie sous tous ses articles.

    Complément de strip_related_blocks(), qui travaille par marqueur
    ("Читайте также", "Recommended Stories"). Un marqueur par site ne
    passe pas à l'échelle : Asia-Plus termine par un fil "Recent News"
    sans aucun marqueur, 24.kg par un bloc "Popular". La table de
    boilerplate.py, elle, est dérivée mécaniquement du corpus — un
    texte identique d'un article à l'autre d'une même source ne peut
    pas être le contenu de cet article-là.

    Voir tools/detecter_boilerplate.py pour la façon dont la table est
    produite et pour les deux garde-fous qui l'empêchent de confondre
    un pied de page avec un article republié.

    Idempotente, comme strip_related_blocks() : le rattrapage sur
    l'archive existante en dépend.
    """
    if not text:
        return ""

    text = str(text)
    suffixe = BOILERPLATE_PAR_SOURCE.get(str(source or ""))

    if suffixe and text.endswith(suffixe):
        text = text[: -len(suffixe)]

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

# Paramètres de tracking/partage qui ne distinguent pas deux articles
# différents mais font que la même page apparaît comme une URL "unique"
# à chaque fois (et donc échappe à la déduplication).
_TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "utm_referrer",
    "fbclid",
    "gclid",
    "yclid",
    "mc_cid",
    "mc_eid",
    "_hsenc",
    "_hsmi",
    "igshid",
    "ref",
    "ref_src",
    "spref",
}


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

    if parsed.query:
        kept_params = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.lower() not in _TRACKING_QUERY_PARAMS
        ]
        parsed = parsed._replace(query=urlencode(kept_params))

    return parsed.geturl().strip()


# ============================================================
# ÂGE D'UN ARTICLE
# ============================================================

def article_age_days(date: Any, now: datetime | None = None) -> float | None:
    """
    Âge d'un article en jours (float), ou None si la date est absente ou
    inexploitable.

    Une date sans fuseau est supposée UTC plutôt que de faire échouer la
    soustraction : les dates viennent de flux RSS et de pages HTML
    hétérogènes, dont beaucoup omettent le fuseau.

    Vivait en trois exemplaires (html_template.article_age_days,
    synthesis._article_age_days, et l'import de categorisation.py qui
    faisait dépendre la couche de description de la couche de
    présentation) ; consolidé ici le 2026-09-13.
    """
    if not isinstance(date, datetime):
        return None

    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    reference = now or datetime.now(timezone.utc)

    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)

    return (reference - date).total_seconds() / 86400
