# memory.py

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


MEMORY_FILE = Path("data/articles_memory.json")

CACHE_DURATION_MINUTES = 60


def now_utc():
    return datetime.now(timezone.utc)


def iso_now():
    return now_utc().isoformat()


def parse_datetime(value):
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed

    except Exception:
        return None


def ensure_memory_directory():
    MEMORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


def load_memory():
    ensure_memory_directory()

    if not MEMORY_FILE.exists():
        return {
            "articles": {},
            "sources": {},
        }

    try:
        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except Exception:
        return {
            "articles": {},
            "sources": {},
        }

    data.setdefault(
        "articles",
        {}
    )

    data.setdefault(
        "sources",
        {}
    )

    return data


def save_memory(memory):
    ensure_memory_directory()

    temporary_file = MEMORY_FILE.with_suffix(
        ".tmp"
    )

    with open(
        temporary_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            memory,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary_file.replace(
        MEMORY_FILE
    )


def article_key(article):
    """
    L'URL est l'identifiant principal.
    """

    url = article.get(
        "url",
        "",
    ).strip().lower()

    if url:
        return url

    title = article.get(
        "title",
        "",
    ).strip().lower()

    return title


def source_key(source):
    return source.get(
        "name",
        ""
    ).strip().lower()


def is_source_cached(
    memory,
    source,
):
    """
    Retourne True si cette source a été
    parcourue il y a moins d'une heure.
    """

    key = source_key(
        source
    )

    if not key:
        return False

    source_memory = memory[
        "sources"
    ].get(
        key
    )

    if not source_memory:
        return False

    last_scan = parse_datetime(
        source_memory.get(
            "last_scan"
        )
    )

    if not last_scan:
        return False

    expiration = (
        last_scan
        + timedelta(
            minutes=CACHE_DURATION_MINUTES
        )
    )

    return now_utc() < expiration


def source_last_scan(
    memory,
    source,
):
    key = source_key(
        source
    )

    source_memory = memory[
        "sources"
    ].get(
        key,
        {}
    )

    return source_memory.get(
        "last_scan"
    )


def mark_source_scanned(
    memory,
    source,
    article_count=0,
):
    key = source_key(
        source
    )

    memory[
        "sources"
    ][key] = {
        "name": source.get(
            "name",
            "",
        ),
        "last_scan": iso_now(),
        "article_count": article_count,
    }


def get_article(
    memory,
    article,
):
    key = article_key(
        article
    )

    if not key:
        return None

    return memory[
        "articles"
    ].get(
        key
    )


def is_article_known(
    memory,
    article,
):
    return (
        get_article(
            memory,
            article,
        )
        is not None
    )


def save_article(
    memory,
    article,
):
    key = article_key(
        article
    )

    if not key:
        return

    existing = memory[
        "articles"
    ].get(
        key,
        {}
    )

    if "first_seen" not in existing:
        existing["first_seen"] = iso_now()

    existing.update({
        "url": article.get(
            "url",
            "",
        ),

        "title": article.get(
            "title",
            "",
        ),

        "summary": article.get(
            "summary",
            "",
        ),

        "source": article.get(
            "source",
            "",
        ),

        "source_short": article.get(
            "source_short",
            "",
        ),

        "date": (
            article["date"].isoformat()
            if isinstance(
                article.get("date"),
                datetime,
            )
            else article.get(
                "date"
            )
        ),

        "score": article.get(
            "score",
            0,
        ),

        "level": article.get(
            "level",
            "D",
        ),

        "theme": article.get(
            "theme",
            "",
        ),

        "relevant": article.get(
            "relevant",
            False,
        ),

        "reasons": article.get(
            "reasons",
            [],
        ),

        "last_seen": iso_now(),
    })

    memory[
        "articles"
    ][key] = existing


def save_articles(
    memory,
    articles,
):
    for article in articles:
        save_article(
            memory,
            article,
        )


def get_all_articles(
    memory
):
    return list(
        memory[
            "articles"
        ].values()
    )


def get_memory_stats(
    memory
):
    articles = memory[
        "articles"
    ]

    levels = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    }

    for article in articles.values():

        level = article.get(
            "level",
            "D",
        )

        if level in levels:
            levels[level] += 1

    return {
        "articles": len(
            articles
        ),

        "sources": len(
            memory[
                "sources"
            ]
        ),

        "levels": levels,
    }
