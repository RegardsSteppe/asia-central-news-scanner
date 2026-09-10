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

        prompt = mock_model.create_chat_completion.call_args.kwargs[
            "messages"
        ][0]["content"]
        self.assertIn("Article 0", prompt)
        self.assertIn("Article 2", prompt)
        self.assertNotIn("Article 3", prompt)


if __name__ == "__main__":
    unittest.main()
