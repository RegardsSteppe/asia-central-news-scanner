import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scoring import classify_article


class CityGeographyTests(unittest.TestCase):
    """
    Régression : la géographie n'était détectée que via des noms de
    pays, jamais des villes — un titre ne citant qu'une ville
    (ex. "Samarkand") tombait à 0/100 faute de tout ancrage régional.
    """

    def test_recognizes_major_central_asian_cities(self):
        article = {
            "title": "Mr. Trump, Take the Golden Road to Samarkand",
            "summary": "",
            "body": "",
            "source": "Hudson Institute",
            "url": "https://www.hudson.org/example",
        }

        classify_article(article)

        self.assertGreater(article["score"], 0)
        self.assertTrue(
            any("Asie centrale" in reason for reason in article["reasons"])
        )

    def test_recognizes_major_caucasus_cities(self):
        article = {
            "title": "Protests continue in Tbilisi over new legislation",
            "summary": "",
            "body": "",
            "source": "Test Source",
            "url": "https://example.com/tbilisi-protests",
        }

        classify_article(article)

        # Caucase-only reste pénalisé par ailleurs (comportement
        # pré-existant, hors sujet ici) : on vérifie seulement que la
        # ville est bien reconnue comme un signal géographique.
        self.assertTrue(
            any("Caucase" in reason for reason in article["reasons"])
        )


class SecurityIsolationTests(unittest.TestCase):
    """
    Garde-fou pour l'ajout de sources sécurité (Hudson Institute et
    consorts) : le nouveau vocabulaire sécurité (MAJOR_GEOPOLITICAL_TERMS)
    ne doit jamais, à lui seul, produire un article de niveau A — ce
    niveau reste réservé aux signaux droits humains/répression forts.
    """

    def test_pure_security_article_never_reaches_level_a(self):
        article = {
            "title": (
                "Border security cooperation deepens as Uzbekistan and "
                "Tajikistan tackle militant insurgency threat"
            ),
            "summary": (
                "Officials cited concerns over cross-border attacks, "
                "extremism and instability linked to Afghanistan, and "
                "announced new security cooperation agreements under "
                "CSTO coordination."
            ),
            "body": "",
            "source": "Hudson Institute",
            "url": "https://www.hudson.org/security/example",
        }

        classify_article(article)

        self.assertNotEqual(article["level"], "A")
        self.assertFalse(article["relevant"] and article["level"] == "A")

    def test_security_terms_do_not_block_genuine_activist_case(self):
        article = {
            "title": "Kazakh activist detained and tortured after protest",
            "summary": (
                "Human rights defenders say the activist was arbitrarily "
                "detained and tortured following his arrest in Kazakhstan."
            ),
            "body": "",
            "source": "Turkmen.News",
            "url": "https://turkmen.news/example",
        }

        classify_article(article)

        self.assertEqual(article["level"], "A")
        self.assertTrue(article["relevant"])


if __name__ == "__main__":
    unittest.main()
