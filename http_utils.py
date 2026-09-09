from __future__ import annotations

import logging
import json
import os
import time
import threading
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Nombre de tentatives (dont la première) pour les erreurs réseau
# transitoires (timeout, connexion, 5xx).
MAX_ATTEMPTS = max(
    1,
    int(os.getenv("SCANNER_HTTP_MAX_ATTEMPTS", "3")),
)

# Délai de base (secondes) pour le backoff exponentiel entre tentatives.
RETRY_BACKOFF_BASE = max(
    0.0,
    float(os.getenv("SCANNER_HTTP_RETRY_BACKOFF_BASE", "1.0")),
)

# Codes HTTP considérés comme transitoires et donc "retryables".
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


# ============================================================
# CACHE
# ============================================================

_MEMORY_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_META: dict[str, dict[str, Any]] | None = None
_CACHE_LOCK = threading.Lock()
_CACHE_FILE = Path(
    os.getenv(
        "SCANNER_HTTP_CACHE_FILE",
        str(Path(__file__).resolve().parent / "http_cache.json"),
    )
)


def _load_cache_meta() -> dict[str, dict[str, Any]]:
    global _CACHE_META

    if _CACHE_META is not None:
        return _CACHE_META

    if not _CACHE_FILE.exists():
        _CACHE_META = {}
        return _CACHE_META

    try:
        with _CACHE_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, dict):
                _CACHE_META = data
                return _CACHE_META
    except Exception:
        pass

    _CACHE_META = {}
    return _CACHE_META


def _save_cache_meta() -> None:
    if _CACHE_META is None:
        return

    try:
        with _CACHE_FILE.open("w", encoding="utf-8") as handle:
            json.dump(_CACHE_META, handle, ensure_ascii=False)
    except Exception:
        logger.debug("Unable to save HTTP cache metadata", exc_info=True)


def _get_cache_meta_item(url: str) -> dict[str, Any] | None:
    with _CACHE_LOCK:
        data = _load_cache_meta().get(url)
        if isinstance(data, dict):
            return data
    return None


def _resolve_timeout(request_timeout: int) -> tuple[float, float]:
    read_timeout = max(
        1.0,
        float(os.getenv("SCANNER_HTTP_READ_TIMEOUT", str(request_timeout))),
    )
    connect_default = min(read_timeout, 5.0)
    connect_timeout = max(
        1.0,
        float(os.getenv("SCANNER_HTTP_CONNECT_TIMEOUT", str(connect_default))),
    )
    return (connect_timeout, read_timeout)


def cache_get(
    key: str,
    cache_ttl: int,
    allow_stale: bool = False,
) -> Any | None:
    with _CACHE_LOCK:
        item = _MEMORY_CACHE.get(key)

        if item:
            timestamp, value = item
            if allow_stale or time.time() - timestamp <= cache_ttl:
                return value
            _MEMORY_CACHE.pop(key, None)

        cache_item = _load_cache_meta().get(key)
        if not isinstance(cache_item, dict):
            return None

        fetched_at = cache_item.get("fetched_at")
        content = cache_item.get("content")
        if not isinstance(fetched_at, (int, float)) or not isinstance(content, str):
            return None

        if not allow_stale and time.time() - fetched_at > cache_ttl:
            return None

        _MEMORY_CACHE[key] = (fetched_at, content)
        return content

def cache_set(
    key: str,
    value: Any,
    etag: str = "",
    last_modified: str = "",
) -> None:
    now = time.time()
    with _CACHE_LOCK:
        _MEMORY_CACHE[key] = (now, value)
        _load_cache_meta()[key] = {
            "fetched_at": now,
            "content": value,
            "etag": etag,
            "last_modified": last_modified,
        }
        _save_cache_meta()


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
    timeout = _resolve_timeout(request_timeout)
    conditional_headers = dict(headers)
    meta = _get_cache_meta_item(url)
    if meta:
        etag = meta.get("etag")
        last_modified = meta.get("last_modified")
        if isinstance(etag, str) and etag:
            conditional_headers["If-None-Match"] = etag
        if isinstance(last_modified, str) and last_modified:
            conditional_headers["If-Modified-Since"] = last_modified

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
                headers=conditional_headers if not force_refresh else headers,
                timeout=timeout,
                allow_redirects=True,
            )

            if response.status_code == 304:
                cached = cache_get(url, cache_ttl, allow_stale=True)
                if cached is not None:
                    return cached

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=timeout,
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
                etag=response.headers.get("ETag", ""),
                last_modified=response.headers.get("Last-Modified", ""),
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
