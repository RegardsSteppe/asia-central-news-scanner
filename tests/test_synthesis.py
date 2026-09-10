import sys
import unittest
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


if __name__ == "__main__":
    unittest.main()
