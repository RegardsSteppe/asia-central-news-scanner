from __future__ import annotations

import time
from typing import Any

import requests


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
        raise RuntimeError(
            f"HTTP error: {exc}"
        ) from exc
