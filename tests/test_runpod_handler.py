import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scoring import classify_article
from runpod_handler import (
    batch_score_articles,
    handler,
    score_articles,
    score_one_article,
)


ACTIVIST_ARTICLE = {
    "title": "Kazakhstan Jails Activist for Ten Years Over Peaceful Protest",
    "summary": (
        "A court sentenced a human rights activist to ten years in "
        "prison after a peaceful protest against government corruption."
    ),
    "source": "Test Source",
    "url": "https://example.com/activist",
}

NOISE_ARTICLE = {
    "title": "Routine economic news about GDP growth",
    "summary": "",
    "source": "Test Source",
    "url": "https://example.com/noise",
}


class ScoreOneArticleTests(unittest.TestCase):
    def test_scores_a_valid_article(self):
        result = score_one_article(dict(ACTIVIST_ARTICLE), index=0)

        self.assertNotIn("error", result)
        self.assertEqual(result["level"], "A")
        self.assertGreater(result["score"], 0)
        self.assertIn("keywords", result)
        self.assertIn("sub_scores", result)

    def test_missing_title_returns_error_not_exception(self):
        result = score_one_article({"summary": "no title here"}, index=5)

        self.assertEqual(result["index"], 5)
        self.assertIn("error", result)
        self.assertIn("title", result["error"])

    def test_non_dict_article_returns_error_not_exception(self):
        result = score_one_article("not a dict", index=2)

        self.assertEqual(result["index"], 2)
        self.assertIn("error", result)

    def test_missing_optional_fields_do_not_crash(self):
        result = score_one_article({"title": "Bare title only"}, index=0)

        self.assertNotIn("error", result)
        self.assertEqual(result["source"], "")
        self.assertEqual(result["url"], "")

    def test_result_matches_direct_classify_article_call(self):
        # Le handler ne doit jamais diverger du scoring existant : même
        # entrée, même score/niveau qu'un appel direct à
        # classify_article().
        direct = dict(ACTIVIST_ARTICLE)
        classify_article(direct)

        wrapped = score_one_article(dict(ACTIVIST_ARTICLE), index=0)

        self.assertEqual(wrapped["score"], direct["score"])
        self.assertEqual(wrapped["level"], direct["level"])
        self.assertEqual(wrapped["theme"], direct["theme"])


class ScoreArticlesTests(unittest.TestCase):
    def test_scores_a_batch_of_articles(self):
        result = score_articles(
            {"articles": [dict(ACTIVIST_ARTICLE), dict(NOISE_ARTICLE)]}
        )

        self.assertEqual(result["mode"], "score")
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["scored"], 2)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["results"][0]["level"], "A")
        self.assertEqual(result["results"][1]["level"], "E")

    def test_one_bad_article_does_not_stop_the_batch(self):
        result = score_articles(
            {
                "articles": [
                    dict(ACTIVIST_ARTICLE),
                    {"summary": "missing title"},
                    dict(NOISE_ARTICLE),
                ]
            }
        )

        self.assertEqual(result["count"], 3)
        self.assertEqual(result["scored"], 2)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["errors"][0]["index"], 1)
        # Les deux articles valides autour du mauvais sont bien notés.
        scored_indexes = {r["index"] for r in result["results"]}
        self.assertEqual(scored_indexes, {0, 2})

    def test_missing_articles_field_raises_value_error(self):
        with self.assertRaises(ValueError):
            score_articles({})

    def test_articles_not_a_list_raises_value_error(self):
        with self.assertRaises(ValueError):
            score_articles({"articles": "not a list"})

    def test_empty_articles_list_returns_empty_results(self):
        result = score_articles({"articles": []})

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["results"], [])
        self.assertEqual(result["errors"], [])


class BatchScoreArticlesTests(unittest.TestCase):
    def test_matches_score_mode_output_across_multiple_chunks(self):
        articles = [dict(ACTIVIST_ARTICLE) for _ in range(5)]

        batch_result = batch_score_articles(
            {"articles": articles, "batch_size": 2}
        )
        score_result = score_articles({"articles": articles})

        self.assertEqual(batch_result["scored"], score_result["scored"])
        self.assertEqual(
            [r["score"] for r in batch_result["results"]],
            [r["score"] for r in score_result["results"]],
        )
        # Les index restent globaux malgré le découpage en lots.
        self.assertEqual(
            [r["index"] for r in batch_result["results"]], [0, 1, 2, 3, 4]
        )

    def test_errors_keep_correct_global_index_across_chunks(self):
        articles = [
            dict(ACTIVIST_ARTICLE),
            {"summary": "no title"},
            dict(NOISE_ARTICLE),
            {"summary": "also no title"},
        ]

        result = batch_score_articles(
            {"articles": articles, "batch_size": 2}
        )

        error_indexes = sorted(e["index"] for e in result["errors"])
        self.assertEqual(error_indexes, [1, 3])

    def test_invalid_batch_size_raises_value_error(self):
        with self.assertRaises(ValueError):
            batch_score_articles(
                {"articles": [dict(ACTIVIST_ARTICLE)], "batch_size": 0}
            )

    def test_default_batch_size_used_when_not_provided(self):
        result = batch_score_articles({"articles": [dict(ACTIVIST_ARTICLE)]})

        self.assertEqual(result["scored"], 1)


class HandlerTests(unittest.TestCase):
    def test_accepts_runpod_style_event_with_input_wrapper(self):
        event = {
            "id": "job-123",
            "input": {"mode": "score", "articles": [dict(ACTIVIST_ARTICLE)]},
        }

        result = handler(event)

        self.assertEqual(result["mode"], "score")
        self.assertEqual(result["scored"], 1)

    def test_accepts_bare_payload_without_input_wrapper(self):
        result = handler({"mode": "score", "articles": [dict(ACTIVIST_ARTICLE)]})

        self.assertEqual(result["scored"], 1)

    def test_defaults_to_score_mode_when_mode_omitted(self):
        result = handler({"articles": [dict(ACTIVIST_ARTICLE)]})

        self.assertEqual(result["mode"], "score")

    def test_batch_mode_is_dispatched_correctly(self):
        result = handler(
            {"mode": "batch", "articles": [dict(ACTIVIST_ARTICLE)], "batch_size": 1}
        )

        self.assertEqual(result["mode"], "batch")
        self.assertEqual(result["scored"], 1)

    def test_unknown_mode_returns_error_without_raising(self):
        result = handler({"mode": "translate", "articles": []})

        self.assertIn("error", result)
        self.assertIn("translate", result["error"])

    def test_missing_articles_returns_error_without_raising(self):
        result = handler({"mode": "score"})

        self.assertIn("error", result)

    def test_non_dict_event_returns_error_without_raising(self):
        result = handler(["not", "a", "dict"])

        self.assertIn("error", result)

    def test_non_dict_input_returns_error_without_raising(self):
        result = handler({"input": "not a dict"})

        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
