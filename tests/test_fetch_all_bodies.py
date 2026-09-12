import csv
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch_all_bodies import (
    _fetch_one,
    _is_google_news_url,
    fetch_all_bodies,
    load_previous_results,
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
    requêtes en parallèle).

    Un premier correctif (sémaphore partagé par le même pool que le
    reste du corpus) a été essayé puis abandonné le 2026-09-12 : un
    tiers du corpus (2220/6725, vérifié) est du Google News, donc les
    threads du pool principal bloqués sur semaphore.acquire()
    finissaient par affamer le reste — un deuxième run a terminé PLUS
    LENTEMENT que le premier (débit passant de ~39/min à ~5.6/min de
    façon monotone). Google News est maintenant un ThreadPoolExecutor
    séparé et dédié : ses requêtes ne consomment jamais un slot du pool
    principal.
    """

    @patch("fetch_all_bodies.extract_body")
    @patch("fetch_all_bodies.time.sleep")
    def test_non_google_news_url_does_not_sleep(self, mock_sleep, mock_extract):
        mock_extract.return_value = ("Body.", None)

        row = dict(SAMPLE_ROW, url="https://example.com/article")
        _fetch_one(row, google_news_delay=5.0)

        mock_sleep.assert_not_called()

    @patch("fetch_all_bodies.extract_body")
    @patch("fetch_all_bodies.time.sleep")
    def test_google_news_url_sleeps_after_fetch(self, mock_sleep, mock_extract):
        mock_extract.return_value = ("Body.", None)

        row = dict(
            SAMPLE_ROW, url="https://news.google.com/rss/articles/abc?oc=5"
        )
        _fetch_one(row, google_news_delay=2.5)

        mock_sleep.assert_called_once_with(2.5)

    @patch("fetch_all_bodies.extract_body")
    @patch("fetch_all_bodies.time.sleep")
    def test_sleep_still_happens_when_extract_body_raises(
        self, mock_sleep, mock_extract
    ):
        mock_extract.side_effect = ConnectionError("boom")

        row = dict(
            SAMPLE_ROW, url="https://news.google.com/rss/articles/abc?oc=5"
        )
        _fetch_one(row, google_news_delay=0.1)

        mock_sleep.assert_called_once_with(0.1)

    @patch("fetch_all_bodies.extract_body")
    def test_concurrency_is_actually_capped_for_google_news(self, mock_extract):
        # Pas juste un appel de mock : vérifie que le nombre RÉEL
        # d'appels news.google.com simultanés ne dépasse jamais
        # google_news_concurrency, avec un vrai ThreadPoolExecutor.
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
    def test_non_google_news_urls_are_not_throttled(self, mock_extract):
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

    @patch("fetch_all_bodies.extract_body")
    def test_google_news_backlog_never_starves_the_main_pool(self, mock_extract):
        # Le bug corrigé le 2026-09-12 : avec un sémaphore partagé dans
        # le même pool, un grand nombre d'URLs Google News en tête de
        # liste bloquait tous les threads du pool principal, empêchant
        # les articles non-Google-News (pourtant rapides) d'avancer.
        # Avec des pools séparés, extract_body() doit être appelé pour
        # les URLs non-Google-News presque immédiatement, sans attendre
        # que le backlog Google News (lent) libère des threads.
        started = time.perf_counter()
        other_call_times: list[float] = []
        lock = threading.Lock()

        def fake_extract(url, expected_title=""):
            if "news.google.com" in url:
                time.sleep(1.0)
            else:
                with lock:
                    other_call_times.append(time.perf_counter() - started)
            return "Body.", None

        mock_extract.side_effect = fake_extract

        google_rows = [
            dict(SAMPLE_ROW, url=f"https://news.google.com/rss/articles/{i}")
            for i in range(20)
        ]
        other_rows = [
            dict(SAMPLE_ROW, url=f"https://example.com/{i}") for i in range(5)
        ]

        results = fetch_all_bodies(
            other_rows + google_rows,
            workers=5,
            google_news_concurrency=2,
            google_news_delay=0.0,
        )

        self.assertEqual(len(results), 25)
        by_url = {r["url"]: r for r in results}
        for row in other_rows:
            self.assertEqual(by_url[row["url"]]["body"], "Body.")
        # Les 5 articles non-Google-News doivent tous démarrer quasi
        # instantanément (pas après avoir attendu des slots du pool
        # Google News, occupé pendant ~10s par son backlog de 20 URLs
        # x 1s / 2 threads).
        self.assertEqual(len(other_call_times), 5)
        self.assertLess(max(other_call_times), 1.0)


class LoadPreviousResultsTests(unittest.TestCase):
    def test_missing_file_returns_empty_dict(self):
        self.assertEqual(load_previous_results("/no/such/file.json"), {})

    def test_invalid_json_returns_empty_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "broken.json")
            Path(path).write_text("not json", encoding="utf-8")

            self.assertEqual(load_previous_results(path), {})

    def test_only_keeps_successful_articles(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "previous.json")
            data = {
                "articles": [
                    {"url": "https://example.com/ok", "body": "Full text."},
                    {
                        "url": "https://example.com/failed",
                        "body": "",
                        "fetch_error": "boom",
                    },
                    {
                        "url": "https://example.com/empty-body",
                        "body": "",
                    },
                    {"url": "", "body": "Full text."},  # pas de clé exploitable
                ],
            }
            Path(path).write_text(json.dumps(data), encoding="utf-8")

            done = load_previous_results(path)

        self.assertEqual(list(done.keys()), ["https://example.com/ok"])


class ResumeAndCheckpointTests(unittest.TestCase):
    """
    Décidé le 2026-09-12 : sur ~6800 articles, un run peut prendre
    plusieurs heures et être tué par le timeout du job GitHub Actions
    avant de finir — 4 runs consécutifs ont perdu 100% de leur
    progression faute d'avoir jamais rien écrit sur disque avant la
    toute fin. fetch_all_bodies() checkpointe désormais sur disque en
    cours de route, et --resume-from permet de repartir d'un run
    précédent (complet ou partiel) sans re-télécharger ce qui a déjà
    réussi.
    """

    @patch("fetch_all_bodies.extract_body")
    def test_checkpoint_file_reflects_already_done_plus_new_results(
        self, mock_extract
    ):
        mock_extract.return_value = ("Fresh body.", None)

        with tempfile.TemporaryDirectory() as tmp:
            checkpoint_path = str(Path(tmp) / "out.json")

            already_done = [
                dict(SAMPLE_ROW, url="https://example.com/already", body="Old body.")
            ]
            new_rows = [dict(SAMPLE_ROW, url="https://example.com/new")]

            fetch_all_bodies(
                new_rows,
                workers=1,
                checkpoint_path=checkpoint_path,
                already_done=already_done,
            )

            with open(checkpoint_path, encoding="utf-8") as handle:
                data = json.load(handle)

        by_url = {a["url"]: a for a in data["articles"]}
        self.assertEqual(by_url["https://example.com/already"]["body"], "Old body.")
        self.assertEqual(by_url["https://example.com/new"]["body"], "Fresh body.")

    @patch("fetch_all_bodies.extract_body")
    def test_checkpoint_is_written_mid_run_not_just_at_the_end(self, mock_extract):
        mock_extract.return_value = ("Body.", None)

        with tempfile.TemporaryDirectory() as tmp:
            checkpoint_path = str(Path(tmp) / "out.json")
            seen_partial_counts: list[int] = []

            original_replace = os.replace

            def spy_replace(src, dst):
                with open(src, encoding="utf-8") as handle:
                    data = json.load(handle)
                seen_partial_counts.append(len(data["articles"]))
                original_replace(src, dst)

            rows = [
                dict(SAMPLE_ROW, url=f"https://example.com/{i}") for i in range(150)
            ]

            with patch("fetch_all_bodies.os.replace", side_effect=spy_replace):
                fetch_all_bodies(rows, workers=4, checkpoint_path=checkpoint_path)

        # Un checkpoint intermédiaire (à 100) ET un final (à 150) :
        # jamais un seul et unique écrit tout à la fin.
        self.assertIn(100, seen_partial_counts)
        self.assertIn(150, seen_partial_counts)

    @patch("fetch_all_bodies.extract_body")
    def test_main_resume_from_skips_previously_successful_articles(
        self, mock_extract
    ):
        mock_extract.return_value = ("Fresh body.", None)

        with tempfile.TemporaryDirectory() as tmp:
            input_path = str(Path(tmp) / "articles.csv")
            output_path = str(Path(tmp) / "out.json")
            previous_path = str(Path(tmp) / "previous.json")

            write_csv(
                input_path,
                [
                    dict(SAMPLE_ROW, url="https://example.com/already-ok"),
                    dict(SAMPLE_ROW, url="https://example.com/previously-failed"),
                    dict(SAMPLE_ROW, url="https://example.com/never-tried"),
                ],
            )
            Path(previous_path).write_text(
                json.dumps(
                    {
                        "articles": [
                            {
                                "url": "https://example.com/already-ok",
                                "body": "Old successful body.",
                            },
                            {
                                "url": "https://example.com/previously-failed",
                                "body": "",
                                "fetch_error": "boom",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            main(
                [
                    "--input", input_path,
                    "--output", output_path,
                    "--workers", "2",
                    "--resume-from", previous_path,
                ]
            )

            with open(output_path, encoding="utf-8") as handle:
                data = json.load(handle)

        fetched_urls = {call.args[0] for call in mock_extract.call_args_list}
        self.assertNotIn("https://example.com/already-ok", fetched_urls)
        self.assertIn("https://example.com/previously-failed", fetched_urls)
        self.assertIn("https://example.com/never-tried", fetched_urls)

        by_url = {a["url"]: a for a in data["articles"]}
        self.assertEqual(len(by_url), 3)
        self.assertEqual(
            by_url["https://example.com/already-ok"]["body"], "Old successful body."
        )
        self.assertEqual(
            by_url["https://example.com/previously-failed"]["body"], "Fresh body."
        )
        self.assertEqual(
            by_url["https://example.com/never-tried"]["body"], "Fresh body."
        )

    @patch("fetch_all_bodies.extract_body")
    def test_main_without_resume_from_is_unaffected(self, mock_extract):
        mock_extract.return_value = ("Body.", None)

        with tempfile.TemporaryDirectory() as tmp:
            input_path = str(Path(tmp) / "articles.csv")
            output_path = str(Path(tmp) / "out.json")
            write_csv(input_path, [dict(SAMPLE_ROW)])

            main(["--input", input_path, "--output", output_path, "--workers", "1"])

            with open(output_path, encoding="utf-8") as handle:
                data = json.load(handle)

        self.assertEqual(len(data["articles"]), 1)
        self.assertEqual(data["articles"][0]["body"], "Body.")


if __name__ == "__main__":
    unittest.main()
