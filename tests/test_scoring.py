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


class FalsePositiveCoherenceTests(unittest.TestCase):
    """
    Audit de cohérence réel (2026-09-11, revue systématique de tous
    les articles de niveau A) : deux articles sans aucun rapport avec
    l'Asie centrale/le Caucase/les Ouïghours atteignaient le niveau A
    par deux mécanismes différents.
    """

    def test_rfe_rl_article_about_iran_is_not_auto_regional(self):
        # RFE/RL couvre l'Iran (service Radio Farda), la Russie,
        # l'Ukraine... "radio free europe" ne doit plus, à lui seul,
        # rendre un article régional : la géographie doit être jugée
        # sur le contenu, comme pour toute autre source.
        article = {
            "title": (
                "Iranian Twin Sisters Reportedly Tortured Over January "
                "Protests; One Sentenced To Death, Other Gets 25 Years"
            ),
            "summary": (
                "Iranian twin sisters turned 20 behind bars this year, "
                "awaiting the outcome of a case that has drawn scrutiny "
                "over allegations of torture and severe mistreatment."
            ),
            "body": "",
            "source": "Radio Free Europe / Radio Liberty",
        }

        classify_article(article)

        self.assertNotEqual(article["level"], "A")

    def test_single_incidental_body_mention_does_not_grant_regional_context(self):
        # Une mention isolée d'un pays cible, perdue dans un article
        # sur un sujet totalement différent (ici la Syrie), ne doit
        # pas suffire à faire passer la porte régionale.
        article = {
            "title": (
                "German journalist recounts 5-month detention in Syria, "
                "urges colleague's release"
            ),
            "summary": "",
            "body": (
                "The journalist was held in Syria. Press freedom issues "
                "have also been documented in Uzbekistan and elsewhere, "
                "CPJ said."
            ),
            "source": "Committee to Protect Journalists",
        }

        classify_article(article)

        self.assertNotEqual(article["level"], "A")

    def test_two_distinct_body_mentions_still_grant_regional_context(self):
        # À l'inverse, deux mentions distinctes dans le corps restent
        # un signal suffisant quand le titre lui-même n'en porte aucun
        # (comportement existant, à ne pas casser).
        article = {
            "title": "Rights group publishes annual report",
            "summary": "",
            "body": (
                "The report documents an activist arrested in Tashkent "
                "and another detained in Bishkek, both held without "
                "trial for months."
            ),
            "source": "Test Source",
        }

        classify_article(article)

        self.assertTrue(article["signals"]["regional_context"])


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

    def test_routine_crime_or_war_reporting_is_not_promoted_to_level_d(self):
        # Régression réelle (audit du 2026-09-11) : de la pure
        # actualité criminelle/militaire russe (un agent détenu, un
        # suspect arrêté) déclenchait "primary_repression" tout seul
        # (mots "détenu"/"arrêté" sans aucune cible activiste/
        # journaliste identifiée) et atterrissait dans le niveau D
        # au lieu du bruit pur — un détenu de droit commun n'est pas
        # un cas droits humains.
        article = {
            "title": "Задержанный молдаванин рассказал о задании Киева убить генерала",
            "summary": "",
            "body": "",
            "source": "TASS — russe",
            "url": "https://example.com/tass-1",
        }

        classify_article(article)

        self.assertEqual(article["level"], "E")

    def test_severe_repression_without_named_target_still_reaches_level_d(self):
        # Le remplacement de "primary_repression" par "severe_detected"
        # ne doit pas perdre les cas graves (torture, condamnation à
        # mort...) qui ne nomment pas explicitement un "activiste"/
        # "journaliste" — seuls les mots-clés d'une répression
        # ordinaire (arrêté/détenu tout seul) doivent être exclus.
        article = {
            "title": "Twin sisters tortured over protests, one sentenced to death",
            "summary": (
                "The sisters were tortured in custody and one was "
                "sentenced to death, human rights groups say."
            ),
            "body": "",
            "source": "Radio Free Europe / Radio Liberty",
            "url": "https://example.com/rfe-1",
        }

        classify_article(article)

        self.assertEqual(article["level"], "D")


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


class RussianMorphologyGapTests(unittest.TestCase):
    """
    Audit réel du 2026-09-11 (échantillon niveau D) : le russe est
    une langue à déclinaisons/genre — la correspondance de phrase
    exacte utilisée pour la géographie et les rôles (activiste,
    journaliste...) ne reconnaissait qu'une forme nominative/masculine
    unique, ratant les tournures les plus courantes d'une dépêche.
    """

    def test_recognizes_declined_country_name_in_russian(self):
        # "Узбекистана" est le génitif de "Узбекистан" — la forme la
        # plus courante dans une phrase ("sur les champs de coton
        # D'Ouzbékistan"), jamais la forme nominative isolée.
        article = {
            "title": (
                "На хлопковых полях Узбекистана задержана "
                "корреспондент «Штерн»"
            ),
            "summary": "",
            "body": "",
            "source": "Centre1",
        }

        classify_article(article)

        self.assertTrue(
            any("Asie centrale" in reason for reason in article["reasons"])
        )
        self.assertEqual(article["level"], "B")

    def test_recognizes_adjectival_city_name_in_russian(self):
        # "Наманганская" (adjectif dérivé de la ville de Namangan) ne
        # correspond pas à "наманган" en recherche de phrase exacte.
        article = {
            "title": (
                "Наманганская правозащитница приговорена к "
                "исправительным работам"
            ),
            "summary": "",
            "body": "",
            "source": "Centre1",
        }

        classify_article(article)

        self.assertEqual(article["level"], "A")

    def test_recognizes_feminine_human_rights_defender(self):
        # "правозащитницА" (féminin) change la fin du radical par
        # rapport à "правозащитниК" (masculin) — pas une simple
        # forme déclinée, un vrai gap de vocabulaire avant ce fix.
        article = {
            "title": "Правозащитница осуждена за пост в соцсетях",
            "summary": "",
            "body": "",
            "source": "Kazakhstan",
        }

        result = classify_article(article)

        self.assertTrue(result["signals"]["has_activist"])


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
