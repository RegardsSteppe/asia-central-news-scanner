from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Nombre de tentatives (dont la première) pour les erreurs réseau
# transitoires (timeout, connexion, 5xx).
MAX_ATTEMPTS = 3

# Délai de base (secondes) pour le backoff exponentiel entre tentatives.
RETRY_BACKOFF_BASE = 1.0

# Codes HTTP considérés comme transitoires et donc "retryables".
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


# ============================================================
# CACHE
# ============================================================

_MEMORY_CACHE: dict[str, tuple[float, Any]] = {}


def cache_get(
    key: str,
    cache_ttl: int,
) -> Any | None:
    item = _MEMORY_CACHE.get(key)

    if not item:
        return None

    timestamp, value = item

    if time.time() - timestamp > cache_ttl:
        _MEMORY_CACHE.pop(key, None)
        return None

    return value


def cache_set(
    key: str,
    value: Any,
) -> None:
    _MEMORY_CACHE[key] = (time.time(), value)


# ============================================================
# HTTP
# ============================================================

def _is_retryable_error(exc: requests.exceptions.RequestException) -> bool:
    """
    Détermine si une exception réseau mérite une nouvelle tentative :
    timeouts, erreurs de connexion, et statuts HTTP transitoires (429/5xx).
    Les erreurs SSL et les statuts 4xx (hors 429) ne sont pas retryables.
    """

    if isinstance(
        exc,
        (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ),
    ):
        return True

    response = getattr(exc, "response", None)

    if response is not None and response.status_code in _RETRYABLE_STATUS_CODES:
        return True

    return False


def fetch_url(
    url: str,
    headers: dict[str, str],
    request_timeout: int,
    cache_ttl: int,
    force_refresh: bool = False,
) -> str:

    if not force_refresh:
        cached = cache_get(
            url,
            cache_ttl,
        )

        if cached is not None:
            return cached

    last_exc: requests.exceptions.RequestException | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=request_timeout,
                allow_redirects=True,
            )

            response.raise_for_status()

            # requests détecte généralement correctement l'encodage.
            # On utilise apparent_encoding uniquement si nécessaire.
            if (
                not response.encoding
                or response.encoding.lower() == "iso-8859-1"
            ):
                apparent = getattr(
                    response,
                    "apparent_encoding",
                    None,
                )

                if apparent:
                    response.encoding = apparent

            content = response.text

            cache_set(
                url,
                content,
            )

            return content

        except requests.exceptions.SSLError as exc:
            raise RuntimeError(
                f"SSL/TLS error: {exc}"
            ) from exc

        except requests.exceptions.RequestException as exc:
            last_exc = exc

            if attempt < MAX_ATTEMPTS and _is_retryable_error(exc):
                delay = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))

                logger.warning(
                    "fetch_url retry %s/%s for %s after %s: %s",
                    attempt,
                    MAX_ATTEMPTS,
                    url,
                    type(exc).__name__,
                    exc,
                )

                time.sleep(delay)
                continue

            raise RuntimeError(
                f"HTTP error: {exc}"
            ) from exc

    # Ne devrait jamais être atteint, mais garde le typage strict.
    raise RuntimeError(
        f"HTTP error: {last_exc}"
    )
