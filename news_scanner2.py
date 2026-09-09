from __future__ import annotations

import csv
import re
from pathlib import Path

from html_template import create_web_page
from sources2 import SOURCES, STATIC_ARTICLES
from scoring2 import classify_article
from text_utils import article_date_timestamp, clean_title


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "index2.html"
CSV_OUTPUT_FILE = BASE_DIR / "articles2.csv"
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "beyond",
    "why",
    "most",
    "world",
    "takes",
    "take",
    "asia",
    "central",
    "hudson",
    "institute",
}


def load_articles() -> list[dict[str, object]]:
    return [dict(article) for article in STATIC_ARTICLES]


def build_title_vocabulary(articles: list[dict[str, object]]) -> list[dict[str, object]]:
    counts: dict[str, int] = {}

    for article in articles:
        title = clean_title(article.get("title", "")).lower()
        for word in re.findall(r"[^\W\d_][\w'-]{2,}", title, flags=re.UNICODE):
            word = word.strip("-'")
            if not word or word in STOPWORDS:
                continue
            counts[word] = counts.get(word, 0) + 1

    vocabulary = [{"word": word, "count": count} for word, count in counts.items()]
    vocabulary.sort(key=lambda item: (-item["count"], item["word"]))
    return vocabulary[:100]


def build_stats(
    articles: list[dict[str, object]],
    sources_successful: int,
    sources_total: int,
) -> dict[str, object]:
    scores = [float(article.get("score", 0) or 0) for article in articles]
    levels = {"A": 0, "B": 0, "C": 0, "D": 0}
    retained = 0

    for article in articles:
        level = str(article.get("level", "D"))
        if level in levels:
            levels[level] += 1
        if article.get("relevant"):
            retained += 1

    average = sum(scores) / len(scores) if scores else 0
    relevance_rate = (retained / len(articles) * 100) if articles else 0

    return {
        "analyzed": len(articles),
        "retained": retained,
        "avg_score": round(average, 1),
        "level_a": levels["A"],
        "level_b": levels["B"],
        "level_c": levels["C"],
        "level_d": levels["D"],
        "sources_successful": sources_successful,
        "sources_total": sources_total,
        "relevance_rate": round(relevance_rate, 1),
    }


def build_audit(articles: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "score": article.get("score", 0),
            "level": article.get("level", "D"),
            "relevant": article.get("relevant", False),
            "theme": article.get("theme", ""),
            "url": article.get("url", ""),
            "date": article.get("date"),
        }
        for article in articles
    ]


def build_csv_rows(articles: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for article in articles:
        date = article.get("date")
        signals = article.get("signals")
        if not isinstance(signals, dict):
            signals = {}

        rows.append(
            {
                "date": date.isoformat() if hasattr(date, "isoformat") else date or "",
                "source": article.get("source", ""),
                "source_label": article.get("source_label", ""),
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "summary": article.get("summary", ""),
                "score": article.get("score", 0),
                "level": article.get("level", "D"),
                "priority": article.get("priority", ""),
                "relevant": article.get("relevant", False),
                "theme": article.get("theme", ""),
                "reasons": "; ".join(article.get("reasons") or []),
                "geography_score": signals.get("geography_score", 0),
                "target_score": signals.get("target_score", 0),
                "repression_score": signals.get("repression_score", 0),
                "rights_score": signals.get("rights_score", 0),
                "journalism_score": signals.get("journalism_score", 0),
                "geopolitical_score": signals.get("geopolitical_score", 0),
                "freshness_score": signals.get("freshness_score", 0),
            }
        )

    return rows


def export_csv(articles: list[dict[str, object]]) -> None:
    rows = build_csv_rows(articles)
    fieldnames = [
        "date",
        "source",
        "source_label",
        "title",
        "url",
        "summary",
        "score",
        "level",
        "priority",
        "relevant",
        "theme",
        "reasons",
        "geography_score",
        "target_score",
        "repression_score",
        "rights_score",
        "journalism_score",
        "geopolitical_score",
        "freshness_score",
    ]

    with CSV_OUTPUT_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV | {CSV_OUTPUT_FILE.name} créé | {len(rows)} articles")


def main() -> None:
    articles = load_articles()

    for article in articles:
        classify_article(article)

    articles.sort(
        key=lambda article: (
            bool(article.get("relevant")),
            article.get("score", 0),
            article_date_timestamp(article),
        ),
        reverse=True,
    )

    vocabulary = build_title_vocabulary(articles)
    stats = build_stats(
        articles,
        sources_successful=len(SOURCES),
        sources_total=len(SOURCES),
    )
    audit = build_audit(articles)
    export_csv(articles)

    html_output = create_web_page(
        articles=articles,
        audit=audit,
        stats=stats,
        title_words=vocabulary,
    )
    OUTPUT_FILE.write_text(html_output, encoding="utf-8")
    print(f"HTML | {OUTPUT_FILE.name} créé | {len(articles)} articles")


if __name__ == "__main__":
    main()
