import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from news_scanner import (
    build_csv_rows,
    canonical_article_key,
    collect_articles,
    deduplicate,
    load_seen_keys,
)


class CanonicalArticleKeyTests(unittest.TestCase):
    def test_uses_url_when_present(self):
        article = {"url": "https://Example.com/News/1/", "title": "Title"}
        self.assertEqual(canonical_article_key(article), "example.com/news/1")

    def test_falls_back_to_title_when_no_url(self):
        article = {"url": "", "title": "Some Title! With Punctuation."}
        self.assertEqual(
            canonical_article_key(article), "some title with punctuation"
        )

    def test_empty_article_returns_empty_key(self):
        self.assertEqual(canonical_article_key({}), "")


class DeduplicateTests(unittest.TestCase):
    def test_removes_duplicate_urls(self):
        articles = [
            {"url": "https://example.com/news/1", "title": "A"},
            {"url": "https://example.com/news/1", "title": "A duplicate"},
            {"url": "https://example.com/news/2", "title": "B"},
        ]
        result = deduplicate(articles)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "A")

    def test_skips_articles_without_key(self):
        articles = [{"url": "", "title": ""}]
        self.assertEqual(deduplicate(articles), [])

    def test_empty_list(self):
        self.assertEqual(deduplicate([]), [])


class CsvExportTests(unittest.TestCase):
    def test_rows_include_article_data_scores_and_keywords(self):
        rows = build_csv_rows(
            [
                {
                    "date": None,
                    "source": "Example",
                    "title": "A title",
                    "url": "https://example.com/article",
                    "summary": "Summary",
                    "score": 82,
                    "level": "A",
                    "priority": "high",
                    "relevant": True,
                    "theme": "Rights",
                    "reasons": ["human rights"],
                    "signals": {
                        "human_rights": ["freedom"],
                        "repression": ["arrested", "freedom"],
                        "geography_score": 12,
                    },
                }
            ]
        )

        self.assertEqual(rows[0]["title"], "A title")
        self.assertEqual(rows[0]["score"], 82)
        self.assertEqual(rows[0]["keywords"], "freedom; arrested")
        self.assertEqual(rows[0]["geography_score"], 12)


class MemorySeenKeysTests(unittest.TestCase):
    def test_load_seen_keys_filters_invalid_entries(self):
        memory = {"seen_article_keys": ["a", "", None, 42, "b"]}
        self.assertEqual(load_seen_keys(memory), {"a", "b"})


class CollectArticlesTests(unittest.TestCase):
    @patch("news_scanner.diagnose_source_content")
    @patch("news_scanner.parse_rss")
    @patch("news_scanner.fetch_url")
    def test_skips_previously_seen_keys_early(
        self,
        mock_fetch,
        mock_parse,
        mock_diag,
    ):
        with patch(
            "news_scanner.SOURCES",
            new=[
                {"name": "S1", "url": "https://example.com/rss", "type": "rss"},
            ],
        ):
            mock_fetch.return_value = "<rss></rss>"
            mock_parse.return_value = [
                {"url": "https://example.com/keep", "title": "Keep"},
                {"url": "https://example.com/old", "title": "Old"},
            ]

            articles, ok, total, skipped = collect_articles(
                seen_keys={"example.com/old"}
            )

        self.assertEqual(ok, 1)
        self.assertEqual(total, 1)
        self.assertEqual(skipped, 1)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["url"], "https://example.com/keep")


if __name__ == "__main__":
    unittest.main()
