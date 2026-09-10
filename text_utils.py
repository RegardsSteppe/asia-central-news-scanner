from __future__ import annotations

import html
import re
import unicodedata
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse


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
