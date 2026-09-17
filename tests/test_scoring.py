import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scoring import (
    classify_article,
    decide_level,
    decide_priority,
    decide_relevance,
    decide_theme,
)
from matching import detect_language


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
        # Titre et URL réalistes : la version d'origine ("Iran" sous
        # /iran) avait exactement la forme d'une page pays et ressort
        # désormais en F. Un vrai article porte un titre-phrase et un
        # slug qui n'est pas son titre entier.
        article = {
            "title": "Iranian Rights Defender Jailed After Months In Detention",
            "summary": "",
            "body": (
                "An Iranian human rights defender was arrested and "
                "imprisoned after being detained by authorities, "
                "rights groups say, in an ongoing political crackdown "
                "on activists and journalists."
            ),
            "source": "Human Rights Watch",
            "url": "https://example.com/news/iranian-rights-defender-jailed",
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

    def test_stem_matching_runs_via_detected_language_when_source_declares_none(self):
        # Suggestion de l'utilisateur le 2026-09-11 (les vérifications
        # regex russes ralentissaient le scan sur tout le corpus, y
        # compris les articles non-russes) : la source connaît
        # généralement sa langue (sources.py), donc build_article() la
        # propage sur chaque article et classify_article() ne lance ces
        # vérifications coûteuses que sur les articles concernés — un
        # gain de vitesse, pas de justesse. Mais le 2026-09-11
        # (deuxième demande) : quand la source ne déclare aucune
        # langue unique (absente, ou "multi" — ex: RFE/RL qui mélange
        # plusieurs services linguistiques), classify_article() doit
        # quand même détecter la langue réelle du texte (script
        # cyrillique/persan/latin) plutôt que de sauter silencieusement
        # les vérifications russes sur du contenu qui EST en russe.
        article = {
            "title": (
                "На хлопковых полях Узбекистана задержана "
                "корреспондент «Штерн»"
            ),
            "summary": "",
            "body": "",
            "source": "Centre1",
            # Pas de "language" ici : simule une source dont la langue
            # n'a pas été propagée (ou "multi") — doit être détectée.
        }

        classify_article(article)

        self.assertTrue(
            any("Asie centrale" in reason for reason in article["reasons"])
        )
        self.assertEqual(article["language"], "ru")

    def test_stem_matching_skipped_for_explicitly_declared_non_russian_source(self):
        # À l'inverse : quand la source déclare explicitement une
        # langue non-russe, on fait confiance à cette déclaration et on
        # saute les vérifications russes (coûteuses) sans lancer de
        # détection par script.
        article = {
            "title": (
                "На хлопковых полях Узбекистана задержана "
                "корреспондент «Штерн»"
            ),
            "summary": "",
            "body": "",
            "source": "Centre1",
            "language": "en",
        }

        classify_article(article)

        self.assertFalse(
            any("Asie centrale" in reason for reason in article["reasons"])
        )
        self.assertEqual(article["language"], "en")

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
            "language": "ru",
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
            "language": "ru",
        }

        classify_article(article)

        self.assertEqual(article["level"], "A")

    def test_recognizes_modern_kyrgyz_adjective_form(self):
        # "кыргызские" (adjectif russe moderne, orthographe post-1991)
        # ne partage pas le radical de "кыргызстан" (qui ne couvre que
        # "кыргызстана", "кыргызстане"...) — seule la forme "киргиз"
        # (orthographe soviétique) était couverte avant ce fix. Repéré
        # en audit réel le 2026-09-12 sur un article Kloop resté à
        # 0/E faute de reconnaître "кыргызские власти".
        article = {
            "title": (
                "Кыргызские власти пытались арестовать активиста "
                "за рубежом"
            ),
            "summary": "",
            "body": "",
            "source": "Centre1",
            "language": "ru",
        }

        classify_article(article)

        self.assertTrue(
            any("Asie centrale" in reason for reason in article["reasons"])
        )

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


class LanguageTaggingTests(unittest.TestCase):
    """
    Suite à la demande de l'utilisateur le 2026-09-11 : le premier
    passage de scope-par-langue ne couvrait que les vérifications
    russes (radicaux + morphologie), en laissant tourner
    inconditionnellement ACTIVIST_REPRESSION_RU_PATTERNS/FA_PATTERNS et
    JOURNALIST_REPRESSION_RU_PATTERNS/FA_PATTERNS sur tous les
    articles quelle que soit leur langue. Chaque article doit ressortir
    de classify_article() tagué avec sa langue effective (détectée par
    script quand la source ne déclare rien d'unique), et ce tag doit
    être utilisé pour scoper *toutes* les vérifications regex
    langue-spécifiques, pas seulement le russe.
    """

    def test_detect_language_recognizes_cyrillic_script(self):
        self.assertEqual(
            detect_language("Активист задержан в Узбекистане после протеста"),
            "ru",
        )

    def test_detect_language_recognizes_persian_script(self):
        self.assertEqual(
            detect_language("فعال حقوق بشر تاجیک بازداشت و شکنجه شد"),
            "fa",
        )

    def test_detect_language_defaults_to_en_for_latin_script(self):
        self.assertEqual(
            detect_language("Kazakhstan jails activist over peaceful protest"),
            "en",
        )

    def test_detect_language_returns_empty_for_too_little_text(self):
        self.assertEqual(detect_language("ok"), "")
        self.assertEqual(detect_language(""), "")

    def test_farsi_repression_pattern_gated_to_detected_farsi_language(self):
        # Même texte/motif que FarsiVocabularyTests.
        # test_farsi_activist_detained_reaches_level_a, sans "language"
        # déclaré : doit toujours atteindre le niveau A grâce à la
        # détection par script (fa), pas malgré elle.
        article = {
            "title": "فعال حقوق بشر تاجیک بازداشت و شکنجه شد",
            "summary": (
                "فعال مدنی پس از اعتراض در تاجیکستان به‌طور خودسرانه "
                "بازداشت و شکنجه شد."
            ),
            "body": "",
            "source": "Fararu",
            "url": "https://www.fararu.com/example-lang-tag",
        }

        classify_article(article)

        self.assertEqual(article["language"], "fa")
        self.assertEqual(article["level"], "A")

    def test_farsi_repression_pattern_skipped_for_declared_russian_source(self):
        # Motif farsi présent dans le texte (citation, translittération...)
        # mais la source déclare explicitement "ru" : le motif FA ne
        # doit pas être testé, on fait confiance à la déclaration.
        article = {
            "title": "فعال حقوق بشر تاجیک بازداشت و شکنجه شد",
            "summary": "",
            "body": "",
            "source": "Test Source",
            "language": "ru",
        }

        classify_article(article)

        self.assertEqual(article["language"], "ru")

    def test_multi_language_source_resolves_via_detection(self):
        # Sources déclarées "multi" (ex: RFE/RL) mélangent plusieurs
        # services linguistiques dans un seul flux : classify_article()
        # doit détecter la langue réelle de chaque article plutôt que
        # de rester bloqué sur "multi" (ce qui aurait pour effet de ne
        # jamais lancer les vérifications russes/farsi sur ces sources).
        article = {
            "title": (
                "На хлопковых полях Узбекистана задержана "
                "корреспондент «Штерн»"
            ),
            "summary": "",
            "body": "",
            "source": "Radio Free Europe / Radio Liberty",
            "language": "multi",
        }

        classify_article(article)

        self.assertEqual(article["language"], "ru")
        self.assertTrue(
            any("Asie centrale" in reason for reason in article["reasons"])
        )


class ScoreIsAgeIndependentTests(unittest.TestCase):
    """
    Décidé avec l'utilisateur le 2026-09-11 : le score et le niveau
    mesurent la pertinence sémantique d'un article, jamais son âge —
    un vieux rapport pertinent (ex. republié via le contournement
    Google News sur un site bloqué) doit obtenir exactement le même
    score/niveau qu'un article frais équivalent. La fraîcheur ne joue
    que sur l'affichage (tri, badge — voir html_template.py) et sur la
    sélection des articles couverts par la synthèse quotidienne (voir
    synthesis.py), jamais sur le score lui-même.
    """

    def _base_article(self):
        return {
            "title": "Kazakhstan Jails Activist for Ten Years Over Protest",
            "summary": (
                "A court in Kazakhstan sentenced a human rights activist "
                "to ten years in prison after a peaceful protest."
            ),
            "body": "",
            "source": "Test Source",
            "url": "https://example.com/example",
        }

    def test_identical_score_regardless_of_declared_age(self):
        fresh = self._base_article()
        fresh["age_days"] = 0

        old = self._base_article()
        old["age_days"] = 900

        no_age_info = self._base_article()

        classify_article(fresh)
        classify_article(old)
        classify_article(no_age_info)

        self.assertEqual(fresh["score"], old["score"])
        self.assertEqual(fresh["score"], no_age_info["score"])
        self.assertEqual(fresh["level"], old["level"])
        self.assertEqual(fresh["level"], no_age_info["level"])

    def test_freshness_score_no_longer_in_signals(self):
        article = self._base_article()

        classify_article(article)

        self.assertNotIn("freshness_score", article["signals"])


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


class RussianRepressionMorphologyTests(unittest.TestCase):
    """
    Régression du 2026-09-13 : la liste de morphologie répressive
    existait en double (keywords.py et une copie plus courte dans
    scoring.py qui la masquait). En les unifiant, la racine large
    "\\bпыт\\w*\\b" est apparue — elle couvre "пытка" (torture) mais
    aussi "пытаться" (essayer), deux mots sans rapport.
    """

    def _has_morphology(self, text):
        from matching import has_russian_repression_morphology

        return has_russian_repression_morphology(text)

    def test_detects_torture_noun_including_genitive_plural(self):
        # "пыток" (génitif pluriel) intercale un о : la racine "пытк"
        # ne le couvre pas, d'où un motif dédié.
        self.assertTrue(self._has_morphology("пытки в тюрьме"))
        self.assertTrue(self._has_morphology("применение пыток"))

    def test_detects_torture_verb_past_tense(self):
        self.assertTrue(self._has_morphology("его пытали в сизо"))

    def test_does_not_confuse_torture_with_trying(self):
        # Cas réels du corpus publié du 2026-09-13.
        self.assertFalse(
            self._has_morphology("запад пытается вернуть былое лидерство")
        )
        self.assertFalse(
            self._has_morphology("мужчина пытался затащить ребенка в автомобиль")
        )

    def test_detects_charges_stem_missing_from_the_old_scoring_copy(self):
        # "обвинения" : présent seulement dans la liste de keywords.py,
        # qui n'était jamais utilisée. Un article HRW russe sur un
        # activiste turkmène visé par de "nouvelles accusations
        # douteuses" était plafonné faute de ce motif.
        self.assertTrue(self._has_morphology("предъявлены новые обвинения"))

    def test_detects_both_spellings_of_sentenced(self):
        # Le russe écrit indifféremment е ou ё.
        self.assertTrue(self._has_morphology("осужденный активист"))
        self.assertTrue(self._has_morphology("осуждённый активист"))


class DerivedDecisionTests(unittest.TestCase):
    """
    Niveau, priorité, thème et pertinence étaient quatre cascades de
    `if` noyées au milieu des 116 variables locales de
    classify_article(), donc impossibles à tester isolément — alors que
    ce sont les règles qui bougent le plus souvent. Extraites en
    fonctions pures de (score, signals) le 2026-09-13.
    """

    def test_level_falls_back_to_d_for_non_regional_human_rights_story(self):
        # Un article HRW sur un défenseur des droits hors région n'est
        # pas du bruit : D le distingue du sport et de l'économie.
        self.assertEqual(
            decide_level(80, {"regional_context": False, "global_hr_signal": True}),
            "D",
        )
        self.assertEqual(
            decide_level(80, {"regional_context": False, "global_hr_signal": False}),
            "E",
        )

    def test_level_a_requires_a_confirmed_signal_not_just_a_high_score(self):
        base = {"regional_context": True}
        self.assertEqual(decide_level(95, base), "B")
        self.assertEqual(
            decide_level(95, {**base, "confirmed_activist_pressure": True}), "A"
        )

    def test_non_news_and_noise_always_fall_to_e(self):
        for flag in ("non_news", "noise"):
            self.assertEqual(
                decide_level(
                    99,
                    {
                        "regional_context": True,
                        "confirmed_repression": True,
                        flag: True,
                    },
                ),
                "E",
            )

    def test_level_thresholds(self):
        base = {"regional_context": True}
        self.assertEqual(decide_level(55, base), "B")
        self.assertEqual(decide_level(54, base), "C")
        self.assertEqual(decide_level(35, base), "C")
        self.assertEqual(decide_level(34, base), "E")

    def test_priority_thresholds(self):
        for score, expected in (
            (100, "ABSOLUE"), (90, "ABSOLUE"), (89, "TRÈS HAUTE"),
            (60, "HAUTE"), (40, "MOYENNE"), (20, "FAIBLE"), (19, "BRUIT"),
            (0, "BRUIT"),
        ):
            self.assertEqual(decide_priority(score), expected, f"score={score}")

    def test_theme_follows_declared_priority_order(self):
        # Les deux signaux présents : le plus prioritaire gagne.
        self.assertEqual(
            decide_theme(
                {"confirmed_activist_pressure": True, "domestic": True}
            ),
            "Activistes / dissidents sous pression",
        )

    def test_theme_defaults_when_nothing_matches(self):
        self.assertEqual(decide_theme({}), "Faible priorité")

    def test_confirmed_pressure_overrides_the_score_threshold(self):
        # Cœur éditorial du scanner : jamais écarté pour quelques points.
        self.assertTrue(
            decide_relevance(0, {"confirmed_journalist_pressure": True})
        )

    def test_relevance_requires_regional_context_and_a_signal(self):
        self.assertFalse(
            decide_relevance(90, {"regional_context": False, "has_activist": True})
        )
        self.assertFalse(decide_relevance(90, {"regional_context": True}))
        self.assertTrue(
            decide_relevance(90, {"regional_context": True, "has_activist": True})
        )

    def test_relevance_rejects_noise_even_when_scored(self):
        self.assertFalse(
            decide_relevance(
                90,
                {"regional_context": True, "has_activist": True, "noise": True},
            )
        )


class NiveauFPagesDeRubriqueTests(unittest.TestCase):
    """
    F : pages de rubrique (pays, région, thème) et mobilier de site.

    Les mettre en E revenait à dire "article sans intérêt" d'une page
    qui n'est pas un article. Et comme certaines sont longues et bien
    remplies, elles remontaient : audit du 2026-09-14 sur les 8174
    entrées archivées, 3 des 442 étaient classées C et 86 en D — dont
    "Vacancy: Project Evaluator" à 39/100.
    """

    def _article(self, url, title, **overrides):
        article = {
            "title": title, "summary": "", "body": "",
            "source": "Test", "url": url, "language": "en",
        }
        article.update(overrides)
        return article

    def test_section_page_is_level_f(self):
        for url, titre in (
            ("https://cpj.org/africa/burkina-faso/", "Burkina Faso"),
            ("https://eurasianet.org/region/central-asia", "Central Asia"),
            ("https://www.amnesty.org/en/media-centre/", "Media Centre"),
            ("https://timesca.com/author/askar-alimzhanov", "Askar Alimzhanov"),
        ):
            with self.subTest(url=url):
                article = self._article(url, titre)
                classify_article(article)
                self.assertEqual(article["level"], "F")

    def test_f_wins_over_regional_geography(self):
        # Une page pays mentionne évidemment son pays : les tests de
        # géographie la valideraient à tort, d'où la décision en tête.
        article = self._article(
            "https://cpj.org/asia/kazakhstan/", "Kazakhstan",
            body="Kazakhstan Almaty Astana journalists detained arrested" * 40,
        )
        classify_article(article)
        self.assertEqual(article["level"], "F")

    def test_a_real_article_keeps_its_level(self):
        article = self._article(
            "https://example.com/news/kazakh-journalist-jailed-ten-years",
            "Kazakh Journalist Jailed For Ten Years Over Protest Coverage",
            body=(
                "A journalist was arrested in Almaty, Kazakhstan, and "
                "sentenced to ten years after covering a protest."
            ),
        )
        classify_article(article)
        self.assertNotEqual(article["level"], "F")

    def test_the_score_itself_is_untouched(self):
        # F décrit la NATURE de la page, pas sa qualité : le score
        # reste celui que le texte mérite, pour rester auditable.
        page = self._article("https://cpj.org/africa/sierra-leone/", "Sierra Leone")
        classify_article(page)
        self.assertIn("score", page)
        self.assertTrue(page["signals"]["section_page"])


class PlafondsSousLesSeuilsTests(unittest.TestCase):
    """
    Un plafond posé exactement sur un seuil de niveau ne retient rien :
    le test étant ">=", l'article plafonné atteint pile le niveau qu'on
    voulait lui refuser. Mesuré le 2026-09-14 avant correction : 85 des
    102 articles de niveau B étaient à exactement 55/100 avec la raison
    "plafond V9: confirmation HR dans le body".
    """

    def test_caps_sit_below_the_thresholds_they_guard(self):
        from scoring import LEVEL_B_MIN_SCORE, LEVEL_C_MIN_SCORE
        import inspect
        import scoring

        source = inspect.getsource(scoring.classify_article)

        self.assertNotIn("min(score, 55)", source)
        self.assertNotIn("min(score, 35)", source)
        self.assertIn("min(score, LEVEL_B_MIN_SCORE - 1)", source)
        self.assertIn("min(score, LEVEL_C_MIN_SCORE - 1)", source)
        self.assertLess(LEVEL_B_MIN_SCORE - 1, LEVEL_B_MIN_SCORE)
        self.assertLess(LEVEL_C_MIN_SCORE - 1, LEVEL_C_MIN_SCORE)

    def test_a_capped_article_never_reaches_the_guarded_level(self):
        from scoring import decide_level, LEVEL_B_MIN_SCORE, LEVEL_C_MIN_SCORE

        signals = {"regional_context": True}
        self.assertNotEqual(decide_level(LEVEL_B_MIN_SCORE - 1, signals), "B")
        self.assertNotEqual(decide_level(LEVEL_C_MIN_SCORE - 1, signals), "C")


class FrontieresDeMotsTests(unittest.TestCase):
    """
    _alternation_pattern ne bornait pas ses alternatives : "forced"
    matchait dans "reinforced", "ngo" dans "Congo". Comme elle alimente
    relation_present() et donc target_repression_relation, une
    occurrence interne suffisait à déclarer une relation cible/action
    sur un article sans rapport — et ce signal déclenche le plafond.
    """

    def test_a_term_never_matches_inside_another_word(self):
        from matching import _alternation_pattern

        motif = _alternation_pattern(("forced", "ngo", "convicted"))
        for texte in ("reinforced concrete", "the congo river", "unconvicted"):
            with self.subTest(texte=texte):
                self.assertIsNone(motif.search(texte))

    def test_whole_words_still_match(self):
        from matching import _alternation_pattern

        motif = _alternation_pattern(("forced", "ngo", "convicted"))
        for texte in ("forced labour", "an ngo worker", "convicted today"):
            with self.subTest(texte=texte):
                self.assertIsNotNone(motif.search(texte))

    def test_truncated_cyrillic_stems_still_match_their_inflections(self):
        # La raison de la règle asymétrique : ces radicaux sont
        # volontairement tronqués. Un (?!\w) en fin les rendrait muets
        # sur toute forme fléchie, c'est-à-dire sur le texte réel.
        from matching import _alternation_pattern

        motif = _alternation_pattern(("задержан", "преследова"))
        for texte in ("задержана активистка", "задержаны трое", "преследования"):
            with self.subTest(texte=texte):
                self.assertIsNotNone(motif.search(texte))

class AncrageRepressionNuTests(unittest.TestCase):
    """
    Régression du 2026-09-14. La catégorisation décrivait déjà
    parfaitement ces articles — "Kazakhstan: Crackdown on Government
    Critics" ressortait acteur=opposant,
    traitement=pression_administrative — mais le score restait bloqué à
    34, soit LEVEL_C_MIN_SCORE - 1 : sans ancrage répressif dans le
    titre+chapô, classify_article() plafonne (branche
    `elif regional_context and not primary_hr_anchor`).
    REPRESSION_TERMS_V9 contenait "political crackdown" mais pas
    "crackdown" nu, ni aucune des formules standard des rapports
    HRW/Amnesty sur les mauvais traitements en détention.

    Les termes ont été retenus sur audit des titres réellement
    déclenchés dans le corpus ; deux candidats ont été REJETÉS pour
    généricité, et les tests de rejet ci-dessous les tiennent dehors.
    """

    def _ancrage(self, titre):
        article = {
            "title": titre,
            "summary": "",
            "source": "Human Rights Watch",
            "url": "https://www.hrw.org/news/test",
        }
        classify_article(article)
        return article

    def test_crackdown_nu_ancre_la_repression(self):
        # 18 titres du corpus contiennent "crackdown", les 18 sont des
        # contextes de répression réels ("unprecedented crackdown on
        # free press", "dissidents fear crackdown in Turkish exile").
        from scoring import LEVEL_C_MIN_SCORE

        article = self._ancrage("Kazakhstan: Crackdown on Government Critics")
        self.assertTrue(article["signals"]["primary_hr_anchor"])
        self.assertGreaterEqual(article["score"], LEVEL_C_MIN_SCORE)

    def test_mauvais_traitements_en_detention_ancrent_la_repression(self):
        # Formule standard des rapports : 3 titres du corpus, 3 justes.
        for titre in (
            "Azerbaijan: Armenian POWs Abused in Custody",
            "Uzbekistan: Ill-Treatment of Detainees Documented",
        ):
            with self.subTest(titre=titre):
                self.assertTrue(self._ancrage(titre)["signals"]["primary_hr_anchor"])

    def test_disparu_nu_reste_dehors(self):
        # Candidats mesurés puis rejetés : sur 5 titres déclenchés par
        # "disappeared" / "missing after" nus, 3 étaient faux. Ce test
        # est le garde-fou qui empêche de les réintroduire.
        for titre in (
            "The Aral Sea has all but disappeared",
            "More than 30 missing after ferry sinks off Bali",
        ):
            with self.subTest(titre=titre):
                self.assertFalse(self._ancrage(titre)["signals"]["primary_hr_anchor"])

    def test_la_forme_qualifiee_de_disparition_entre_bien(self):
        article = self._ancrage("Turkmenistan: Activist Forcibly Disappeared")
        self.assertTrue(article["signals"]["primary_hr_anchor"])


class VocabulaireFrancaisHRWTests(unittest.TestCase):
    """
    Régression du 2026-09-14. Sur 251 articles HRW en zone de veille
    sans corps — hrw.org renvoie 403 aux runners GitHub Actions, donc
    ces articles sont notés sur leur seul titre — 221 restaient en
    niveau E. Deux trous distincts, tous deux en français :

    REPRESSION_TERMS_V9 contenait "répression policière" et
    "répression politique", les formes qualifiées, mais pas
    "répression" seul — exactement la forme du trou "crackdown" nu
    corrigé le même jour en anglais.

    ACTIVIST_TERMS ne comptait que 4 entrées françaises, toutes des
    variantes de "défenseur des droits humains". Or c'est has_activist
    qui fait monter target_score, pas TARGET_TERMS_V9 : les titres
    gagnaient un ancrage sans jamais trouver de cible.
    """

    def _article(self, titre, source="Human Rights Watch"):
        article = {
            "title": titre,
            "summary": "",
            "source": source,
            "url": "https://www.hrw.org/news/test",
        }
        classify_article(article)
        return article

    def test_repression_nue_ancre_en_francais(self):
        # 7 titres du corpus, 7 justes ; 15 corps, 15 justes.
        # Contrairement à "crackdown", le mot n'a pas d'usage anodin
        # en français — ni sens sportif, ni idiome.
        for titre in (
            "Ouzbékistan : Répression létale au Karakalpakstan",
            "Géorgie : Répression de manifestations pro-UE",
            "Tanzanie : Répression meurtrière suite aux élections contestées",
        ):
            with self.subTest(titre=titre):
                self.assertTrue(
                    self._article(titre)["signals"]["primary_hr_anchor"]
                )

    def test_ancrage_plus_cible_francais_fait_monter_le_score(self):
        from scoring import LEVEL_B_MIN_SCORE

        article = self._article(
            "Azerbaïdjan : Répression virulente contre les détracteurs du gouvernement"
        )
        self.assertGreaterEqual(article["score"], LEVEL_B_MIN_SCORE)

    def test_forcibly_suivi_d_un_verbe(self):
        # "Turkmenistan Forcibly Hospitalizes Human Rights Defender"
        # n'avait aucun ancrage : l'adverbe porte toute la contrainte.
        for titre in (
            "Turkmenistan Forcibly Hospitalizes Human Rights Defender",
            "Azerbaijan Rearrests Journalist Forcibly Returned from Georgia",
        ):
            with self.subTest(titre=titre):
                self.assertTrue(
                    self._article(titre)["signals"]["primary_hr_anchor"]
                )

    def test_le_participe_present_opposant_reste_dehors(self):
        # Le garde-fou. Le singulier "opposant" est aussi le participe
        # présent du verbe opposer : sur les corps du corpus, 1 des 2
        # occurrences était "une querelle de voisinage opposant un
        # éleveur porcin au maire". Seul le pluriel entre, un
        # participe présent étant invariable.
        article = self._article(
            "Une querelle de voisinage opposant un éleveur porcin au maire du village",
            source="Reporters Without Borders",
        )
        self.assertFalse(article["signals"].get("confirmed_activist_pressure"))

    def test_militant_le_faux_ami_est_retire(self):
        # "militant" était dans TARGET_TERMS_V9 et s'y comportait en
        # faux ami : sur les 7 articles dont c'était le SEUL
        # terme-cible, les 7 étaient le sens anglais d'insurgé armé
        # (Houthis, CENTCOM, route pétrolière saoudienne, pertes
        # ukrainiennes). Le retrait ne coûte aucune détection
        # légitime — vérifié avant, leçon de "disappeared".
        from scoring import TARGET_TERMS_V9

        minuscules = [terme.lower() for terme in TARGET_TERMS_V9]
        self.assertNotIn("militant", minuscules)
        self.assertNotIn("militants", minuscules)


class VocabulaireRusseHRWTests(unittest.TestCase):
    """
    Suite du travail sur les titres HRW sans corps : 93 des 323 restés
    en niveau E sont en russe.

    Le piège principal n'était pas le vocabulaire mais l'outil.
    find_terms() n'est PAS _alternation_pattern() : il impose une
    limite de mot APRÈS le terme, pour tous les termes, cyrilliques
    compris. Une racine tronquée y est donc totalement inerte —
    "депортаци" ne matche ni "депортация" ni "депортации". Les formes
    sont énumérées une par une, et ces tests le vérifient.
    """

    def _article(self, titre):
        article = {
            "title": titre,
            "summary": "",
            "source": "Human Rights Watch — russe",
            "url": "https://www.hrw.org/ru/news/test",
        }
        classify_article(article)
        return article

    def test_les_formes_flechies_sont_bien_enumerees(self):
        # Le test qui aurait attrapé l'erreur : avec des racines
        # tronquées, ces quatre titres passaient tous à ancre=False
        # sans que rien ne le signale.
        for titre in (
            "Турция: Туркменской активистке угрожает депортация",
            "Россия: Журналисту грозит выдворение в Узбекистан",
            "Казахстан: Изоляция и нарушения прав детей в интернатах",
            "Туркменистан: Родственников активиста не выпускают из страны",
        ):
            with self.subTest(titre=titre):
                self.assertTrue(
                    self._article(titre)["signals"]["primary_hr_anchor"]
                )

    def test_ekspluataciya_est_un_faux_ami(self):
        # Dans les corps du corpus, le mot signifie "mise en service"
        # 9 fois sur 11 : "сдали в эксплуатацию", "срок эксплуатации",
        # "ввели в эксплуатацию". Rejeté pour ça.
        article = self._article("Многоквартирный дом сдали в эксплуатацию")
        self.assertFalse(article["signals"]["primary_hr_anchor"])

    def test_napadenie_reste_dehors(self):
        # Le sens militaire ou criminel domine largement : attaque de
        # la Russie contre l'Ukraine, morsures de chien, attaques
        # d'infrastructures énergétiques.
        article = self._article("Нападение России на Украину освещают по-разному")
        self.assertFalse(article["signals"]["primary_hr_anchor"])

    def test_ischeznovenie_nu_reste_dehors(self):
        # Même piège que "disappeared" en anglais : dans les corps, le
        # mot parle d'oiseaux dont l'habitat disparaît, de Telegram
        # retiré de l'App Store, d'un bâtiment aimé des habitants.
        # Seule la forme qualifiée "насильственное исчезновение" entre.
        article = self._article("Осушение болот приведет к исчезновению птиц")
        self.assertFalse(article["signals"]["primary_hr_anchor"])

    def test_la_disparition_forcee_qualifiee_entre_bien(self):
        article = self._article(
            "Туркменистан: насильственные исчезновения активистов продолжаются"
        )
        self.assertTrue(article["signals"]["primary_hr_anchor"])

    def test_nesoglasnye_est_une_cible_pas_un_ancrage(self):
        # "несогласные" désigne ceux qui ne sont pas d'accord avec le
        # pouvoir : c'est un RÔLE, donc il alimente la cible, pas
        # l'ancrage répressif. Vérifié explicitement pour que la
        # distinction ne se perde pas.
        from matching import find_terms
        import keywords

        self.assertEqual(
            find_terms("чеченские власти против несогласных", keywords.ACTIVIST_TERMS),
            ["несогласных"],
        )


class CiblesManquantesHRWTests(unittest.TestCase):
    """
    Régression du 2026-09-17. Sur les 585 titres HRW restés en niveau
    E, 35 avaient géographie + ancrage répressif confirmés
    (primary_hr_anchor) mais aucune cible reconnue (target_score=0) :
    has_activist/has_journalist sont les deux seuls canaux qui
    alimentent target_score, pas TARGET_TERMS_V9 lui-même.

    "lawyer" et le prisonnier de guerre étaient déjà couverts côté
    catégorisation (AVOCAT_TERMS, DETENU_TERMS dans categorisation.py)
    sans jamais atteindre le scoring — deux listes séparées pour une
    même notion. Le français manquait "prisonnier politique" alors
    que l'anglais et le russe l'avaient déjà.
    """

    def _article(self, titre, source="Human Rights Watch"):
        article = {
            "title": titre,
            "summary": "",
            "source": source,
            "url": "https://www.hrw.org/news/test",
        }
        classify_article(article)
        return article

    def test_lawyer_est_une_cible(self):
        # 9 titres du corpus contiennent "lawyer(s)", 8 justes (le
        # seul faux, Sandusky, est une affaire pénale américaine sans
        # rapport et hors zone de veille de toute façon).
        from scoring import LEVEL_A_MIN_SCORE

        for titre in (
            "Uzbekistan Should Free Imprisoned Lawyer",
            "Uzbekistan Convicts Karakalpak Lawyer – Again",
        ):
            with self.subTest(titre=titre):
                article = self._article(titre)
                self.assertTrue(article["signals"]["has_activist"])
                self.assertGreaterEqual(article["score"], LEVEL_A_MIN_SCORE)

    def test_yurist_advokat_nus_restent_dehors(self):
        # Garde-fou : mesurés puis REJETÉS. "юрист"/"адвокат" seuls
        # sont dominés par les chroniques juridiques grand public
        # (Izvestia : divorce, stationnement, achat immobilier), 2
        # titres HR sur 12-16. Les ajouter ferait basculer ces
        # chroniques de E à D via global_hr_signal.
        for titre in (
            "Юрист объяснила права родителей после развода",
            "Юрист заявил о незаконности платы за парковку во дворе",
            "Адвокат предупредил россиян о признаках мошенничества со стороны риелторов",
        ):
            with self.subTest(titre=titre):
                article = self._article(titre, source="Izvestia")
                self.assertFalse(article["signals"]["has_activist"])
                self.assertEqual(article["level"], "E")

    def test_pow_est_une_cible(self):
        # 4 titres du corpus, 4 justes. "Azerbaijan: Armenian POWs
        # Abused in Custody" passait de E (23) à B avant/après.
        from scoring import LEVEL_B_MIN_SCORE

        for titre in (
            "Azerbaijan: Armenian POWs Abused in Custody",
            "Азербайджан: Грубые нарушения в обращении с армянскими военнопленными",
        ):
            with self.subTest(titre=titre):
                article = self._article(titre, source="Human Rights Watch — russe")
                self.assertTrue(article["signals"]["has_activist"])

        article = self._article("Azerbaijan: Armenian POWs Abused in Custody")
        self.assertGreaterEqual(article["score"], LEVEL_B_MIN_SCORE)

    def test_prisonnier_politique_francais_ancre_le_score(self):
        from scoring import LEVEL_C_MIN_SCORE

        article = self._article(
            "Ouzbékistan : Le calvaire des prisonniers politiques",
            source="Human Rights Watch — français",
        )
        self.assertTrue(article["signals"]["primary_political_prisoner"])
        self.assertGreaterEqual(article["score"], LEVEL_C_MIN_SCORE)

    def test_farmer_nu_reste_dehors(self):
        # Garde-fou : mesuré puis REJETÉ. 3-4 titres HR justes sur 8
        # ("Cotton, Wheat Farmers Exploited") contre du bruit agricole
        # massif hors zone (Chine, Kosovo, Afrique) : Xinhua "Farmers
        # busy with autumn harvesting", China Daily "smart
        # agricultural tech", UN Women Kosovo.
        for titre, source in (
            ("Farmers busy with autumn harvesting across China", "Xinhua"),
            (
                "Women farmers in Kosovo are empowered to shape the future of agriculture",
                "UN Women — Europe & Asie centrale",
            ),
        ):
            with self.subTest(titre=titre):
                article = self._article(titre, source=source)
                self.assertFalse(article["signals"]["has_activist"])


class PageDeRubriqueTests(unittest.TestCase):
    """
    Élargissement du 2026-09-14, en réponse au recensement des
    articles sans catégories : 4368 des 9556 entrées archivées n'ont
    aucune géographie, et une large part n'est pas constituée
    d'articles mais de pages de navigation — éditions du Guardian,
    "Donate Now" d'Amnesty, pages pays de CIVICUS, bandeau cookies.

    L'égalité stricte entre le slug du titre et le dernier segment
    d'URL en ratait 88, pour deux raisons mesurées : une décoration
    accrochée au titre, ou un mot de liaison présent dans le slug
    d'URL et jeté par slugify().
    """

    def test_les_pages_de_navigation_sont_reconnues(self):
        from matching import looks_like_section_page

        for url, titre in (
            ("https://www.theguardian.com/preference/edition/us", "US edition"),
            ("https://www.amnesty.org/en/donate/", "Donate Now"),
            ("https://www.occrp.org/en/project/bad-practice", "Explore this project"),
            ("https://monitor.civicus.org/country/macedonia/", "North Macedonia"),
            ("https://eurasianet.org/region/the-baltics", "The Baltics"),
        ):
            with self.subTest(url=url):
                self.assertTrue(looks_like_section_page(url, titre))

    def test_une_url_datee_n_est_jamais_une_rubrique(self):
        # Le garde-fou qui compte, et qui manquait. La règle du slug
        # est fragile sur les titres courts : "Kazakhstan: Protesters
        # Arbitrarily Arrested, Beaten" fait exactement
        # SECTION_TITLE_MAX_WORDS mots, et l'URL d'origine chez HRW
        # reprend le slug du titre. Sans l'exclusion des chemins
        # datés, un vrai article — de la forme la plus typique du
        # corpus — tomberait en niveau F.
        from matching import looks_like_section_page

        self.assertFalse(
            looks_like_section_page(
                "https://www.hrw.org/news/2026/09/12/"
                "kazakhstan-protesters-arbitrarily-arrested-beaten",
                "Kazakhstan: Protesters Arbitrarily Arrested, Beaten",
            )
        )

    def test_l_inclusion_reste_bornee(self):
        # Sans la borne, un slug court serait contenu dans n'importe
        # quel segment : "us" se retrouve dans
        # "kazakhstan-jails-us-citizen".
        from matching import looks_like_section_page

        self.assertFalse(
            looks_like_section_page(
                "https://example.org/world/kazakhstan-jails-us-citizen", "US"
            )
        )

    def test_un_titre_long_reste_un_article(self):
        from matching import looks_like_section_page

        self.assertFalse(
            looks_like_section_page(
                "https://example.org/uzbekistan-cotton-wheat-farmers-exploited-abused",
                "Uzbekistan: Cotton, Wheat Farmers Exploited, Abused",
            )
        )


class HautKarabakhGeographieTests(unittest.TestCase):
    """
    Même trou côté scoring que côté categorisation.py (voir
    HautKarabakhTests) : CAUCASUS_TERMS ne contenait aucune forme du
    Haut-Karabakh, donc regional_context restait False sur des titres
    HRW qui n'ont pourtant aucune autre géographie à offrir.
    """

    def test_regional_context_bascule_sur_karabakh_seul(self):
        article = {
            "title": "La crise du Karabakh",
            "summary": "",
            "source": "Human Rights Watch",
            "url": "https://www.hrw.org/news/test",
        }
        classify_article(article)
        self.assertTrue(article["signals"]["regional_context"])

    def test_morphologie_russe_flechie_cote_scoring(self):
        article = {
            "title": "Незаконные нападения на медицинские объекты в Нагорном Карабахе",
            "summary": "",
            "source": "Human Rights Watch",
            "url": "https://www.hrw.org/news/test",
        }
        classify_article(article)
        self.assertTrue(article["signals"]["regional_context"])


class GeographieAllemandeScoringTests(unittest.TestCase):
    """
    Même trou côté scoring que côté categorisation.py (voir
    GeographieAllemandeTests) : CENTRAL_ASIA_TERMS/CAUCASUS_TERMS sont
    partagées entre les deux modules, donc regional_context restait
    False sur les titres allemands qui ne nomment le pays que dans sa
    forme allemande.
    """

    def test_regional_context_bascule_sur_forme_allemande(self):
        article = {
            "title": "Kasachstan: Anti-Kriegs-Priester in psychiatrische Klinik eingewiesen",
            "summary": "",
            "source": "Novastan — allemand",
            "url": "https://novastan.org/de/test",
        }
        classify_article(article)
        self.assertTrue(article["signals"]["regional_context"])

    def test_zentralasien_nu_bascule_regional_context(self):
        article = {
            "title": "Zentralasien & Europa: eine neue Partnerschaft",
            "summary": "",
            "source": "Novastan — allemand",
            "url": "https://novastan.org/de/test",
        }
        classify_article(article)
        self.assertTrue(article["signals"]["regional_context"])


class GeographieNativeCyrilliqueScoringTests(unittest.TestCase):
    """
    Même trou côté scoring que côté categorisation.py (voir
    GeographieNativeCyrilliqueTests) : CENTRAL_ASIA_TERMS/
    CAUCASUS_TERMS sont partagées entre les deux modules, donc
    regional_context restait False sur les titres kazakh/tadjik/
    ouzbek qui ne nomment le pays que dans son écriture native.
    """

    def test_regional_context_bascule_sur_tadjikistan_en_tadjik(self):
        article = {
            "title": "Нақшаи нави ислоҳот дар зиндонҳои Тоҷикистон",
            "summary": "",
            "source": "Radio Ozodi",
            "url": "https://example.org/test",
        }
        classify_article(article)
        self.assertTrue(article["signals"]["regional_context"])

    def test_fonctionne_sans_filtre_de_langue(self):
        # Même si le champ language est resté "ru" par erreur.
        article = {
            "title": "Ўзбекистонда қоидабузар ҳайдовчилар жазоланди",
            "summary": "",
            "source": "Qalampir.uz",
            "language": "ru",
            "url": "https://example.org/test",
        }
        classify_article(article)
        self.assertTrue(article["signals"]["regional_context"])
