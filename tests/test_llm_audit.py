import csv
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm_audit import (
    AuditArticle,
    build_batches,
    build_user_prompt,
    load_articles,
    parse_flagged,
    run_audit,
)


def write_csv(path, rows):
    fieldnames = ["title", "summary", "url", "source", "score", "level"]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class LoadArticlesTests(unittest.TestCase):
    def test_filters_to_requested_levels(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "articles.csv")
            write_csv(path, [
                {"title": "A", "summary": "", "url": "u1", "source": "s", "score": 90, "level": "A"},
                {"title": "B", "summary": "", "url": "u2", "source": "s", "score": 10, "level": "E"},
                {"title": "C", "summary": "", "url": "u3", "source": "s", "score": 20, "level": "D"},
            ])

            articles = load_articles(path, levels={"D", "E"})

        self.assertEqual({a.title for a in articles}, {"B", "C"})

    def test_all_levels_when_none_passed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "articles.csv")
            write_csv(path, [
                {"title": "A", "summary": "", "url": "u1", "source": "s", "score": 90, "level": "A"},
                {"title": "B", "summary": "", "url": "u2", "source": "s", "score": 10, "level": "E"},
            ])

            articles = load_articles(path, levels=None)

        self.assertEqual(len(articles), 2)

    def test_missing_level_defaults_to_e(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "articles.csv")
            write_csv(path, [
                {"title": "A", "summary": "", "url": "u1", "source": "s", "score": ""},
            ])

            articles = load_articles(path, levels={"E"})

        self.assertEqual(len(articles), 1)


class BuildBatchesTests(unittest.TestCase):
    def test_splits_into_expected_batch_sizes(self):
        articles = [
            AuditArticle(i, f"title {i}", "", "url", "src", 0, "E")
            for i in range(7)
        ]

        batches = build_batches(articles, batch_size=3)

        self.assertEqual([len(b) for b in batches], [3, 3, 1])

    def test_empty_articles_returns_no_batches(self):
        self.assertEqual(build_batches([], batch_size=25), [])


class BuildUserPromptTests(unittest.TestCase):
    def test_numbers_articles_and_truncates_summary(self):
        articles = [
            AuditArticle(0, "First title", "a" * 500, "url", "src", 0, "E"),
            AuditArticle(1, "Second title", "", "url", "src", 0, "E"),
        ]

        prompt = build_user_prompt(articles, max_summary_chars=10)

        self.assertIn("1. First title — " + "a" * 10, prompt)
        self.assertIn("2. Second title", prompt)
        self.assertNotIn("a" * 11, prompt)


class ParseFlaggedTests(unittest.TestCase):
    def setUp(self):
        self.batch = [
            AuditArticle(0, "Title one", "", "url1", "src", 0, "E"),
            AuditArticle(1, "Title two", "", "url2", "src", 0, "E"),
        ]

    def test_parses_valid_json(self):
        raw = '{"flagged": [{"n": 2, "reason": "activist detained"}]}'

        result = parse_flagged(raw, self.batch)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0].title, "Title two")
        self.assertEqual(result[0][1], "activist detained")

    def test_parses_json_wrapped_in_markdown_fence(self):
        raw = (
            "Voici le résultat :\n```json\n"
            '{"flagged": [{"n": 1, "reason": "journalist case"}]}'
            "\n```"
        )

        result = parse_flagged(raw, self.batch)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0].title, "Title one")

    def test_empty_flagged_list_returns_nothing(self):
        raw = '{"flagged": []}'

        self.assertEqual(parse_flagged(raw, self.batch), [])

    def test_malformed_json_returns_nothing_without_raising(self):
        raw = "I cannot help with that."

        self.assertEqual(parse_flagged(raw, self.batch), [])

    def test_out_of_range_index_is_ignored(self):
        raw = '{"flagged": [{"n": 99, "reason": "x"}]}'

        self.assertEqual(parse_flagged(raw, self.batch), [])

    def test_non_integer_index_is_ignored(self):
        raw = '{"flagged": [{"n": "two", "reason": "x"}]}'

        self.assertEqual(parse_flagged(raw, self.batch), [])


class RunAuditTests(unittest.TestCase):
    def test_writes_report_with_flagged_articles_only(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            input_path = str(Path(tmp) / "articles.csv")
            output_path = str(Path(tmp) / "report.csv")

            write_csv(input_path, [
                {"title": "Missed activist case", "summary": "", "url": "u1", "source": "Src", "score": 12, "level": "E"},
                {"title": "Routine economic news", "summary": "", "url": "u2", "source": "Src", "score": 5, "level": "E"},
            ])

            with patch("llm_audit.call_llm") as mock_call:
                mock_call.return_value = (
                    '{"flagged": [{"n": 1, "reason": "activist detained"}]}'
                )

                run_audit(
                    input_path=input_path,
                    output_path=output_path,
                    levels={"E"},
                    batch_size=25,
                    base_url="http://localhost:8000/v1",
                    api_key="",
                    model="test-model",
                    max_summary_chars=300,
                    temperature=0.1,
                    timeout=10,
                )

            with open(output_path, encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Missed activist case")
        self.assertEqual(rows[0]["llm_reason"], "activist detained")

    def test_continues_after_a_failed_batch(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            input_path = str(Path(tmp) / "articles.csv")
            output_path = str(Path(tmp) / "report.csv")

            write_csv(input_path, [
                {"title": f"Article {i}", "summary": "", "url": f"u{i}", "source": "Src", "score": 5, "level": "E"}
                for i in range(3)
            ])

            with patch("llm_audit.call_llm") as mock_call:
                mock_call.side_effect = ConnectionError("unreachable")

                run_audit(
                    input_path=input_path,
                    output_path=output_path,
                    levels={"E"},
                    batch_size=1,
                    base_url="http://localhost:8000/v1",
                    api_key="",
                    model="test-model",
                    max_summary_chars=300,
                    temperature=0.1,
                    timeout=10,
                )

            with open(output_path, encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        # Aucun lot n'a réussi, mais ça ne doit jamais lever d'exception :
        # le rapport (vide) doit tout de même être écrit.
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
