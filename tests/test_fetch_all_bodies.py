import csv
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch_all_bodies import (
    _fetch_one,
    _is_google_news_url,
    fetch_all_bodies,
    load_rows,
    main,
)


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


class IsGoogleNewsUrlTests(unittest.TestCase):
    def test_recognizes_google_news_host(self):
        self.assertTrue(
            _is_google_news_url("https://news.google.com/rss/articles/abc?oc=5")
        )

    def test_rejects_other_hosts(self):
        self.assertFalse(_is_google_news_url("https://example.com/article"))
        self.assertFalse(_is_google_news_url("https://www.hrw.org/news/x"))

    def test_handles_malformed_url_without_raising(self):
        self.assertFalse(_is_google_news_url("not a url"))
        self.assertFalse(_is_google_news_url(""))


class GoogleNewsThrottleTests(unittest.TestCase):
    """
    Décidé avec l'utilisateur le 2026-09-11 : un run réel sur les ~6800
    articles a été tué par son timeout après seulement 38% (2600/6725)
    — 180/180 avertissements du log pointaient vers des 503 sur
    news.google.com (rate-limiting de Google face au volume de
    requêtes en parallèle). Ce throttle limite juste news.google.com,
    le reste du corpus garde sa pleine concurrence.
    """

    @patch("fetch_all_bodies.extract_body")
    @patch("fetch_all_bodies.time.sleep")
    def test_non_google_news_url_does_not_touch_semaphore_or_sleep(
        self, mock_sleep, mock_extract
    ):
        mock_extract.return_value = ("Body.", None)
        fake_semaphore = MagicMock()

        row = dict(SAMPLE_ROW, url="https://example.com/article")
        _fetch_one(row, fake_semaphore, google_news_delay=5.0)

        fake_semaphore.acquire.assert_not_called()
        fake_semaphore.release.assert_not_called()
        mock_sleep.assert_not_called()

    @patch("fetch_all_bodies.extract_body")
    @patch("fetch_all_bodies.time.sleep")
    def test_google_news_url_acquires_semaphore_and_sleeps(
        self, mock_sleep, mock_extract
    ):
        mock_extract.return_value = ("Body.", None)
        fake_semaphore = MagicMock()

        row = dict(
            SAMPLE_ROW, url="https://news.google.com/rss/articles/abc?oc=5"
        )
        _fetch_one(row, fake_semaphore, google_news_delay=2.5)

        fake_semaphore.acquire.assert_called_once()
        fake_semaphore.release.assert_called_once()
        mock_sleep.assert_called_once_with(2.5)

    @patch("fetch_all_bodies.extract_body")
    @patch("fetch_all_bodies.time.sleep")
    def test_semaphore_is_released_even_when_extract_body_raises(
        self, mock_sleep, mock_extract
    ):
        mock_extract.side_effect = ConnectionError("boom")
        fake_semaphore = MagicMock()

        row = dict(
            SAMPLE_ROW, url="https://news.google.com/rss/articles/abc?oc=5"
        )
        _fetch_one(row, fake_semaphore, google_news_delay=0.1)

        fake_semaphore.acquire.assert_called_once()
        fake_semaphore.release.assert_called_once()

    @patch("fetch_all_bodies.extract_body")
    def test_concurrency_is_actually_capped_for_google_news(self, mock_extract):
        # Pas juste que le sémaphore est appelé : vérifie que le
        # nombre RÉEL d'appels news.google.com simultanés ne dépasse
        # jamais google_news_concurrency, avec un vrai ThreadPoolExecutor.
        lock = threading.Lock()
        state = {"current": 0, "max_seen": 0}

        def fake_extract(url, expected_title=""):
            with lock:
                state["current"] += 1
                state["max_seen"] = max(state["max_seen"], state["current"])
            time.sleep(0.05)
            with lock:
                state["current"] -= 1
            return "Body.", None

        mock_extract.side_effect = fake_extract

        rows = [
            dict(SAMPLE_ROW, url=f"https://news.google.com/rss/articles/{i}")
            for i in range(6)
        ]

        fetch_all_bodies(
            rows, workers=6, google_news_concurrency=2, google_news_delay=0.0
        )

        self.assertLessEqual(state["max_seen"], 2)

    @patch("fetch_all_bodies.extract_body")
    def test_non_google_news_urls_are_not_throttled_by_the_semaphore(
        self, mock_extract
    ):
        mock_extract.return_value = ("Body.", None)

        rows = [
            dict(SAMPLE_ROW, url=f"https://example.com/{i}") for i in range(5)
        ]

        results = fetch_all_bodies(
            rows, workers=5, google_news_concurrency=1, google_news_delay=10.0
        )

        # Si le throttle s'appliquait par erreur au reste du corpus,
        # ce test dépasserait largement toute limite de temps
        # raisonnable (5 x 10s en série) — il termine en pratique quasi
        # instantanément.
        self.assertEqual(len(results), 5)


if __name__ == "__main__":
    unittest.main()
