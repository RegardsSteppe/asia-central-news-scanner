from __future__ import annotations

from pathlib import Path

from html_template import create_web_page
from news_scanner import build_audit, build_stats, build_title_vocabulary
from sources2 import SOURCES, STATIC_ARTICLES
from scoring2 import classify_article
from text_utils import article_date_timestamp


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "index2.html"


def load_articles() -> list[dict[str, object]]:
    return [dict(article) for article in STATIC_ARTICLES]


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
