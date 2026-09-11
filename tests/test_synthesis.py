import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from synthesis import generate_synthesis


class GenerateSynthesisTests(unittest.TestCase):
    def test_empty_articles_returns_empty_string_without_loading_model(self):
        with patch("synthesis._load_model") as mock_load:
            result = generate_synthesis([])

        self.assertEqual(result, "")
        mock_load.assert_not_called()

    @patch("synthesis._load_model")
    def test_returns_generated_text_on_success(self, mock_load):
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = {
            "choices": [
                {"message": {"content": "  Synthèse générée.  "}}
            ]
        }
        mock_load.return_value = mock_model

        articles = [
            {"title": "Activist detained", "summary": "Details here."},
        ]

        result = generate_synthesis(articles)

        self.assertEqual(result, "Synthèse générée.")
        mock_model.create_chat_completion.assert_called_once()

    @patch("synthesis._load_model")
    def test_model_failure_returns_empty_string(self, mock_load):
        # La génération de la synthèse ne doit jamais faire échouer le
        # scan complet : toute erreur (modèle indisponible, échec de
        # téléchargement...) doit être absorbée.
        mock_load.side_effect = RuntimeError("model download failed")

        articles = [{"title": "Activist detained", "summary": "Details."}]

        result = generate_synthesis(articles)

        self.assertEqual(result, "")

    @patch("synthesis._load_model")
    def test_caps_number_of_articles_sent_to_model(self, mock_load):
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_load.return_value = mock_model

        articles = [
            {"title": f"Article {i}", "summary": "x"} for i in range(50)
        ]

        generate_synthesis(articles, max_articles=3)

        messages = mock_model.create_chat_completion.call_args.kwargs[
            "messages"
        ]
        # Le dernier message "user" porte la vraie liste d'articles
        # (les précédents sont le system prompt + l'exemple few-shot).
        articles_prompt = messages[-1]["content"]
        self.assertIn("Article 0", articles_prompt)
        self.assertIn("Article 2", articles_prompt)
        self.assertNotIn("Article 3", articles_prompt)

    @patch("synthesis._load_model")
    def test_prioritizes_highest_scored_articles_when_over_limit(
        self, mock_load
    ):
        # Le briefing doit couvrir en priorité les cas les plus
        # graves : si plus de max_articles niveau A dans la journée,
        # on garde les mieux notés, pas les premiers dans l'ordre de
        # collecte.
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_load.return_value = mock_model

        articles = [
            {"title": "Low score case", "summary": "x", "score": 10},
            {"title": "High score case", "summary": "x", "score": 95},
            {"title": "Mid score case", "summary": "x", "score": 50},
        ]

        generate_synthesis(articles, max_articles=2)

        messages = mock_model.create_chat_completion.call_args.kwargs[
            "messages"
        ]
        articles_prompt = messages[-1]["content"]
        self.assertIn("High score case", articles_prompt)
        self.assertIn("Mid score case", articles_prompt)
        self.assertNotIn("Low score case", articles_prompt)

    @patch("synthesis._load_model")
    def test_falls_back_to_titles_only_when_no_summary_or_body(
        self, mock_load
    ):
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_load.return_value = mock_model

        articles = [{"title": "Bare title, no summary", "summary": ""}]

        generate_synthesis(articles)

        messages = mock_model.create_chat_completion.call_args.kwargs[
            "messages"
        ]
        articles_prompt = messages[-1]["content"]
        self.assertIn("Bare title, no summary", articles_prompt)

    @patch("synthesis._load_model")
    def test_refusal_like_response_is_treated_as_empty(self, mock_load):
        # Filet de sécurité : si le modèle répond par un
        # méta-commentaire/refus au lieu d'une synthèse, on ne publie
        # pas ce texte sur le site.
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            "Je suis désolé, mais je ne peux pas rédiger "
                            "une synthèse factuelle basée sur ces articles."
                        )
                    }
                }
            ]
        }
        mock_load.return_value = mock_model

        articles = [{"title": "Some article", "summary": ""}]

        result = generate_synthesis(articles)

        self.assertEqual(result, "")

    @patch("synthesis._load_model")
    def test_excludes_articles_older_than_max_age_days(self, mock_load):
        # Décidé avec l'utilisateur le 2026-09-11 : la synthèse
        # quotidienne ne doit couvrir que l'actualité récente, pas un
        # vieux rapport pertinent qui refait surface (score/niveau
        # restent volontairement indifférents à l'âge — voir
        # scoring.py — donc ce filtre est bien nécessaire ici).
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_load.return_value = mock_model

        now = datetime.now(timezone.utc)
        articles = [
            {
                "title": "Recent case",
                "summary": "x",
                "date": now - timedelta(days=2),
            },
            {
                "title": "Old republished report",
                "summary": "x",
                "date": now - timedelta(days=90),
            },
        ]

        generate_synthesis(articles, max_age_days=14)

        messages = mock_model.create_chat_completion.call_args.kwargs[
            "messages"
        ]
        articles_prompt = messages[-1]["content"]
        self.assertIn("Recent case", articles_prompt)
        self.assertNotIn("Old republished report", articles_prompt)

    @patch("synthesis._load_model")
    def test_keeps_articles_with_unknown_date(self, mock_load):
        # Un article sans date exploitable ne doit pas être écarté :
        # mieux vaut le couvrir que d'exclure à tort un cas peut-être
        # récent.
        mock_model = MagicMock()
        mock_model.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_load.return_value = mock_model

        articles = [
            {"title": "No date case", "summary": "x", "date": None},
        ]

        result = generate_synthesis(articles)

        self.assertNotEqual(result, "")
        mock_model.create_chat_completion.assert_called_once()

    @patch("synthesis._load_model")
    def test_returns_empty_string_when_all_articles_are_too_old(
        self, mock_load
    ):
        now = datetime.now(timezone.utc)
        articles = [
            {
                "title": "Old case",
                "summary": "x",
                "date": now - timedelta(days=60),
            },
        ]

        result = generate_synthesis(articles, max_age_days=14)

        self.assertEqual(result, "")
        mock_load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
