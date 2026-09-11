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

        self.assertTrue(
            any("Caucase" in reason for reason in article["reasons"])
        )


class PresentTenseHeadlineVerbTests(unittest.TestCase):
    """
    Régression réelle (audit du 2026-09-11) : un article HRW
    correctement récupéré ("Kazakhstan Jails Activists for Peaceful
    Xinjiang Protest") restait noté 30/BRUIT car "jails" (présent
    journalistique) n'était dans aucune liste de termes de
    répression — seule la forme passée "jailed" y figurait. Les
    titres de presse utilisent très souvent le présent d'action
    ("X Jails/Sentences/Detains Y").
    """

    def test_present_tense_jails_reaches_level_a(self):
        article = {
            "title": "Kazakhstan Jails Activists for Peaceful Xinjiang Protest",
            "summary": "",
            "body": "",
            "source": "Human Rights Watch",
        }

        classify_article(article)

        self.assertEqual(article["level"], "A")

    def test_present_tense_sentences_reaches_level_b_or_above(self):
        article = {
            "title": "Uzbekistan Court Sentences Independent Journalist to 12 Years",
            "summary": "",
            "body": "",
            "source": "Human Rights Watch",
        }

        classify_article(article)

        self.assertIn(article["level"], ("A", "B"))


class RegionalEqualityTests(unittest.TestCase):
    """
    Le Caucase est une région ciblée à part entière, au même titre
    que l'Asie centrale (pas un sujet secondaire plafonné) — et les
    Ouïghours/Xinjiang sont traités de la même façon.
    """

    def test_caucasus_only_article_can_reach_level_a(self):
        # Régression réelle : un article de niveau critique
        # (répression confirmée + cible identifiée) sur l'Azerbaïdjan
        # (Caucase, aucune mention d'Asie centrale) restait plafonné
        # au niveau D quel que soit son score, à cause d'un plafond
        # "Caucase uniquement" désormais supprimé.
        article = {
            "title": "Azerbaijan",
            "summary": "",
            "body": (
                "Azerbaijan activist and journalist Anar Mammadli was "
                "arrested and sentenced to prison after a politically "
                "motivated trial, human rights defenders say, as "
                "authorities in Baku persecuted independent media in a "
                "crackdown on dissent."
            ),
            "source": "Amnesty International",
            "url": "https://example.com/azerbaijan",
        }

        classify_article(article)

        self.assertNotEqual(article["level"], "D")
        self.assertNotEqual(article["level"], "E")

    def test_caucasus_geography_score_matches_central_asia(self):
        caucasus_article = {
            "title": "Georgia",
            "summary": "",
            "body": "",
            "source": "Test Source",
            "url": "https://example.com/georgia",
        }
        central_asia_article = {
            "title": "Kazakhstan",
            "summary": "",
            "body": "",
            "source": "Test Source",
            "url": "https://example.com/kazakhstan",
        }

        classify_article(caucasus_article)
        classify_article(central_asia_article)

        self.assertEqual(
            caucasus_article["signals"]["geography_score"],
            central_asia_article["signals"]["geography_score"],
        )

    def test_recognizes_uyghur_xinjiang_as_regional_context(self):
        article = {
            "title": "China detains Uyghur activists in Xinjiang crackdown",
            "summary": "",
            "body": "",
            "source": "Test Source",
            "url": "https://example.com/xinjiang",
        }

        classify_article(article)

        self.assertTrue(
            any("Ouïghours" in reason for reason in article["reasons"])
        )
        self.assertTrue(article["signals"]["uyghur"])


class NonRegionalActivistLevelTests(unittest.TestCase):
    """
    Niveau D (nouveau) : un article hors région (ni Asie centrale, ni
    Caucase, ni Ouïghours/Xinjiang) mais avec un vrai signal
    droits humains/activiste, à distinguer du niveau E (bruit pur).
    """

    def test_non_regional_activist_story_reaches_level_d(self):
        article = {
            "title": "Iran",
            "summary": "",
            "body": (
                "An Iranian human rights defender was arrested and "
                "imprisoned after being detained by authorities, "
                "rights groups say, in an ongoing political crackdown "
                "on activists and journalists."
            ),
            "source": "Human Rights Watch",
            "url": "https://example.com/iran",
        }

        classify_article(article)

        self.assertEqual(article["level"], "D")

    def test_pure_noise_stays_level_e(self):
        article = {
            "title": "Ronaldo scores in record World Cup match",
            "summary": "",
            "body": "",
            "source": "Al Jazeera — Uzbekistan",
            "url": "https://example.com/football",
        }

        classify_article(article)

        self.assertEqual(article["level"], "E")


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


class FarsiVocabularyTests(unittest.TestCase):
    """
    Après l'ajout de sources iraniennes (IRNA, Fararu) : sans
    vocabulaire persan, un article en farsi ne pouvait jamais franchir
    la porte géographique ni atteindre le niveau A, quel que soit son
    contenu.
    """

    def test_recognizes_tajikistan_in_farsi(self):
        article = {
            "title": "تاجیکستان می‌کوشد یک منتقد را از ترکیه بازگرداند",
            "summary": "",
            "body": "",
            "source": "Fararu",
            "url": "https://www.fararu.com/example",
        }

        classify_article(article)

        self.assertGreater(article["score"], 0)
        self.assertTrue(
            any("Asie centrale" in reason for reason in article["reasons"])
        )

    def test_farsi_activist_detained_reaches_level_a(self):
        article = {
            "title": "فعال حقوق بشر تاجیک بازداشت و شکنجه شد",
            "summary": (
                "فعال مدنی پس از اعتراض در تاجیکستان به‌طور خودسرانه "
                "بازداشت و شکنجه شد."
            ),
            "body": "",
            "source": "Fararu",
            "url": "https://www.fararu.com/example-2",
        }

        classify_article(article)

        self.assertEqual(article["level"], "A")
        self.assertTrue(article["relevant"])

    def test_ambiguous_dushanbe_word_does_not_grant_geography(self):
        # "دوشنبه" veut aussi dire "lundi" en persan : volontairement
        # absent de CENTRAL_ASIA_TERMS pour éviter qu'un simple jour
        # de la semaine ne fasse passer la porte géographique.
        article = {
            "title": "قیمت طلا روز دوشنبه اعلام شد",
            "summary": "",
            "body": "",
            "source": "Fararu",
            "url": "https://www.fararu.com/example-3",
        }

        classify_article(article)

        self.assertFalse(
            any("Asie centrale" in reason for reason in article["reasons"])
        )


class FrenchVocabularyTests(unittest.TestCase):
    """
    Régression réelle (audit du 2026-09-11) : un article HRW en
    français sur Anar Mammadli (Azerbaïdjan) ne franchissait ni la
    porte géographique ("Azerbaïdjan" absent de CAUCASUS_TERMS) ni
    l'ancrage HR principal (aucun vocabulaire français dans
    TARGET_TERMS_V9/EXPLICIT_HR_ACTION_TERMS_V9/REPRESSION_TERMS_V9),
    alors que l'équivalent anglais/russe passait sans problème. Plusieurs
    sources (HRW FR, Amnesty FR, RSF, Novastan FR) publient en français.
    """

    def test_recognizes_azerbaijan_in_french(self):
        article = {
            "title": "Azerbaïdjan : un défenseur des droits humains condamné",
            "summary": "",
            "body": "",
            "source": "Human Rights Watch — français",
            "url": "https://example.com/fr-1",
        }

        classify_article(article)

        self.assertTrue(
            any("Caucase" in reason for reason in article["reasons"])
        )

    def test_french_activist_detained_reaches_level_a(self):
        article = {
            "title": "Un défenseur des droits humains tadjik arrêté et torturé",
            "summary": (
                "Un militant a été arbitrairement détenu et torturé après "
                "une manifestation au Tadjikistan, selon des défenseurs "
                "des droits humains."
            ),
            "body": "",
            "source": "Human Rights Watch — français",
            "url": "https://example.com/fr-2",
        }

        classify_article(article)

        self.assertEqual(article["level"], "A")
        self.assertTrue(article["relevant"])


if __name__ == "__main__":
    unittest.main()
