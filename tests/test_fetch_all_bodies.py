import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch_all_bodies import fetch_all_bodies, load_rows, main


def write_csv(path, rows):
    fieldnames = ["title", "summary", "url", "source", "score", "level"]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


SAMPLE_ROW = {
    "title": "Kazakhstan Jails Activist for Ten Years",
    "summary": "A court sentenced an activist to ten years in prison.",
    "url": "https://example.com/article",
    "source": "Human Rights Watch",
    "score": "92",
    "level": "A",
}


class LoadRowsTests(unittest.TestCase):
    def test_loads_all_rows_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "articles.csv")
            write_csv(path, [SAMPLE_ROW, dict(SAMPLE_ROW, title="Second")])

            rows = load_rows(path)

        self.assertEqual(len(rows), 2)

    def test_limit_truncates_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "articles.csv")
            write_csv(
                path, [dict(SAMPLE_ROW, title=f"Article {i}") for i in range(5)]
            )

            rows = load_rows(path, limit=2)

        self.assertEqual(len(rows), 2)


class FetchAllBodiesTests(unittest.TestCase):
    @patch("fetch_all_bodies.extract_body")
    def test_attaches_body_on_success(self, mock_extract):
        mock_extract.return_value = ("Full article text.", None)

        results = fetch_all_bodies([dict(SAMPLE_ROW)], workers=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["body"], "Full article text.")
        self.assertNotIn("fetch_error", results[0])

    @patch("fetch_all_bodies.extract_body")
    def test_attaches_language_from_source_name(self, mock_extract):
        mock_extract.return_value = ("Full article text.", None)

        with patch(
            "fetch_all_bodies.SOURCE_LANGUAGE",
            {"Human Rights Watch": "en"},
        ):
            results = fetch_all_bodies([dict(SAMPLE_ROW)], workers=1)

        self.assertEqual(results[0]["language"], "en")

    @patch("fetch_all_bodies.extract_body")
    def test_one_failure_does_not_stop_the_batch(self, mock_extract):
        def side_effect(url, expected_title=""):
            if "fail" in url:
                raise ConnectionError("boom")
            return ("Body text.", None)

        mock_extract.side_effect = side_effect

        rows = [
            dict(SAMPLE_ROW, url="https://example.com/ok"),
            dict(SAMPLE_ROW, url="https://example.com/fail"),
        ]

        results = fetch_all_bodies(rows, workers=2)

        by_url = {r["url"]: r for r in results}
        self.assertEqual(by_url["https://example.com/ok"]["body"], "Body text.")
        self.assertNotIn("fetch_error", by_url["https://example.com/ok"])
        self.assertIn("fetch_error", by_url["https://example.com/fail"])
        self.assertIn("boom", by_url["https://example.com/fail"]["fetch_error"])

    @patch("fetch_all_bodies.extract_body")
    def test_empty_body_is_flagged_as_error(self, mock_extract):
        # extract_body() renvoie "" volontairement quand la page reçue
        # ne correspond pas au titre attendu (redirection douce).
        mock_extract.return_value = ("", None)

        results = fetch_all_bodies([dict(SAMPLE_ROW)], workers=1)

        self.assertEqual(results[0]["body"], "")
        self.assertIn("fetch_error", results[0])

    def test_missing_url_returns_error_without_calling_extract_body(self):
        with patch("fetch_all_bodies.extract_body") as mock_extract:
            results = fetch_all_bodies(
                [dict(SAMPLE_ROW, url="")], workers=1
            )

            mock_extract.assert_not_called()

        self.assertIn("fetch_error", results[0])


class MainIntegrationTests(unittest.TestCase):
    @patch("fetch_all_bodies.extract_body")
    def test_writes_expected_json_shape(self, mock_extract):
        mock_extract.return_value = ("Full article text.", None)

        with tempfile.TemporaryDirectory() as tmp:
            input_path = str(Path(tmp) / "articles.csv")
            output_path = str(Path(tmp) / "out.json")

            write_csv(input_path, [dict(SAMPLE_ROW), dict(SAMPLE_ROW, url="https://example.com/2")])

            main(["--input", input_path, "--output", output_path, "--workers", "2"])

            with open(output_path, encoding="utf-8") as handle:
                data = json.load(handle)

        self.assertIn("articles", data)
        self.assertEqual(len(data["articles"]), 2)
        self.assertEqual(data["articles"][0]["body"], "Full article text.")

    @patch("fetch_all_bodies.extract_body")
    def test_limit_flag_restricts_processed_rows(self, mock_extract):
        mock_extract.return_value = ("Body.", None)

        with tempfile.TemporaryDirectory() as tmp:
            input_path = str(Path(tmp) / "articles.csv")
            output_path = str(Path(tmp) / "out.json")

            write_csv(
                input_path,
                [dict(SAMPLE_ROW, url=f"https://example.com/{i}") for i in range(10)],
            )

            main(["--input", input_path, "--output", output_path, "--limit", "3"])

            with open(output_path, encoding="utf-8") as handle:
                data = json.load(handle)

        self.assertEqual(len(data["articles"]), 3)


if __name__ == "__main__":
    unittest.main()
