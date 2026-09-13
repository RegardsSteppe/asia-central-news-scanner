import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categorisation import categoriser
from regles_editoriales import est_pertinent


class CategoriserOutputShapeTests(unittest.TestCase):
    """categoriser() ne doit jamais juger de la pertinence ni muter l'article."""

    def _article(self, **overrides):
        article = {
            "title": "Kazakhstan Jails Activist for Ten Years Over Peaceful Protest",
            "summary": "A court in Almaty sentenced a human rights activist.",
            "body": "The activist was detained last month.",
            "source": "Human Rights Watch",
            "url": "https://www.hrw.org/news/2026/09/12/kazakhstan-activist-sentenced",
            "language": "en",
            "date": None,
        }
        article.update(overrides)
        return article

    def test_no_relevance_fields_in_output(self):
        result = categoriser(self._article())
        for forbidden in ("score", "level", "relevant", "retenu", "priority"):
            self.assertNotIn(forbidden, result)

    def test_does_not_mutate_input_article(self):
        article = self._article()
        original = dict(article)
        categoriser(article)
        self.assertEqual(article, original)

    def test_expected_top_level_keys(self):
        result = categoriser(self._article())
        self.assertEqual(
            set(result.keys()),
            {
                "geo", "geo_role", "acteur", "traitement",
                "relation_acteur_traitement", "type", "age_jours",
                "source_specialisee", "preuves",
            },
        )


class RussianStemTraitementTests(unittest.TestCase):
    """
    Régression du 2026-09-12 : plusieurs des listes de traitement
    (REPRESSION_TERMS notamment, réutilisée telle quelle pour
    "pression_administrative") contiennent des racines russes
    délibérément incomplètes ("пытк", "давлен", "репресс"...), que
    find_terms() ne peut jamais matcher (il exige une limite de mot
    juste après le terme). Cas réel : un article HRW russe
    ("Киргизия: пытки и произвольные аресты нагнетают напряженность")
    ressortait traitement=aucun malgré "пытки"/"аресты" dans le titre.
    """

    def test_torture_stem_detected_in_inflected_russian_form(self):
        article = {
            "title": "Пытки заключенных продолжаются в тюрьмах региона",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/news/1",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertIn("torture_mauvais_traitement", cat["traitement"])

    def test_arbitrary_arrests_plural_detected_as_detention(self):
        # "аресты" (pluriel) ne matche pas "арест" (singulier) via
        # find_terms — corrigé via _TRAITEMENT_STEM_PATTERNS.
        article = {
            "title": "Власти продолжают произвольные аресты активистов",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/news/2",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertIn("detention", cat["traitement"])

    def test_administrative_pressure_stem_detected_in_russian(self):
        # REPRESSION_TERMS (réutilisée en entier pour
        # "pression_administrative") est presque uniquement composée
        # de racines russes incomplètes pour sa partie russe — ce test
        # confirme qu'au moins une forme réelle ("давление") est
        # désormais détectée.
        article = {
            "title": "Власти усилили давление на оппозицию",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/news/3",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertIn("pression_administrative", cat["traitement"])

    def test_real_reported_article_no_longer_shows_aucun(self):
        # L'article exact signalé par l'utilisateur le 2026-09-12.
        article = {
            "title": (
                "Киргизия: пытки и произвольные аресты нагнетают "
                "напряженность"
            ),
            "summary": "",
            "body": "",
            "source": "Human Rights Watch",
            "url": "https://www.hrw.org/ru/news/2010/07/14/kyrgyzstan-example",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertNotEqual(cat["traitement"], ["aucun"])
        self.assertIn("kirghizistan", cat["geo"])

    def test_condamnation_stem_covers_participle_not_just_enumerated_forms(self):
        # "заключен" (racine) doit couvrir "заключенный"/"заключенным",
        # pas seulement les formes explicitement énumérées.
        article = {
            "title": "Правозащитник объявлен заключенным по политическому делу",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/news/4",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertIn("condamnation", cat["traitement"])


class GeoRegistryConsistencyTests(unittest.TestCase):
    def test_every_geo_term_maps_to_a_declared_country(self):
        # Sanity check : la table de correspondance interne ne doit
        # jamais mapper vers une valeur hors de l'énumération attendue.
        from categorisation import _GEO_TERM_COUNTRY

        allowed = {
            "kazakhstan", "ouzbekistan", "kirghizistan", "tadjikistan",
            "turkmenistan", "azerbaidjan", "armenie", "georgie",
            "caucase_nord", "xinjiang", "iran", "afghanistan", "russie",
        }
        self.assertTrue(set(_GEO_TERM_COUNTRY.values()) <= allowed)

    def test_modern_kyrgyz_adjective_maps_to_kirghizistan(self):
        # Régression du 2026-09-12 : "кыргыз" (adjectif moderne)
        # ajouté aux côtés de "кыргызстан"/"киргиз".
        article = {
            "title": "Кыргызские власти прокомментировали ситуацию",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/news/5",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertIn("kirghizistan", cat["geo"])


class EstPertinentPermissiveDefaultTests(unittest.TestCase):
    def test_permissive_when_no_rule_configured(self):
        cat = categoriser({
            "title": "Random article about nothing in particular",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/x",
            "language": "en",
            "date": None,
        })
        pertinent, reason = est_pertinent(cat)
        self.assertTrue(pertinent)
        self.assertEqual(reason, "pertinent")


if __name__ == "__main__":
    unittest.main()


class PortedIntelligenceTests(unittest.TestCase):
    """
    2026-09-13 : categorisation.py réimplémentait une détection plus
    faible que scoring.py au lieu de partager la sienne. Ces tests
    verrouillent ce qui a été porté via matching.py.
    """

    def _article(self, title, language="", body="", summary=""):
        return {
            "title": title,
            "summary": summary,
            "body": body,
            "source": "Test",
            "url": "https://example.com/news/1",
            "language": language,
            "date": None,
        }

    def test_farsi_journalist_repression_pattern_detects_actor(self):
        # Les listes d'acteurs sont quasi muettes en persan ; les motifs
        # "acteur + répression" de keywords.py, que scoring.py exploite
        # depuis toujours, sont désormais lus ici aussi.
        cat = categoriser(
            self._article("خبرنگار بازداشت شد در تهران", language="fa")
        )
        self.assertIn("journaliste", cat["acteur"])

    def test_farsi_pattern_establishes_actor_treatment_relation(self):
        # Le motif exige acteur et répression à moins de 100 caractères
        # l'un de l'autre : la relation est établie par construction.
        cat = categoriser(
            self._article("فعال حقوق بشر بازداشت شد", language="fa")
        )
        self.assertTrue(cat["relation_acteur_traitement"])
        self.assertTrue(
            cat["preuves"]["relation_acteur_traitement"]["via_motif_farsi"]
        )

    def test_farsi_patterns_not_run_on_non_farsi_articles(self):
        # Les vérifications propres à une langue coûtent cher et n'ont
        # aucun sens ailleurs : elles restent inertes hors persan.
        cat = categoriser(
            self._article("خبرنگار بازداشت شد در تهران", language="ru")
        )
        self.assertNotIn(
            "(motif farsi acteur+répression)",
            cat["preuves"]["acteur"].get("journaliste", []),
        )

    def test_stem_evidence_reports_the_actual_word_found(self):
        # Auditer une catégorisation surprenante suppose de savoir QUEL
        # mot a matché, pas seulement qu'une racine a matché.
        cat = categoriser(
            self._article("Произвольные аресты продолжаются", language="ru")
        )
        self.assertIn("detention", cat["traitement"])
        self.assertIn("аресты", cat["preuves"]["traitement"]["detention"])

    def test_untyped_russian_repression_is_flagged_for_audit(self):
        # Une répression décrite en russe qu'aucun type ne capture est
        # un trou de vocabulaire : il doit être visible, pas silencieux.
        cat = categoriser(
            self._article("Против него выдвинуты новые обвинения", language="ru")
        )
        self.assertEqual(cat["traitement"], ["aucun"])
        self.assertIn("_non_typé", cat["preuves"]["traitement"])

    def test_relation_evidence_uses_word_boundaries_not_substrings(self):
        # L'ancienne version testait "terme in texte" : elle listait des
        # preuves que la détection elle-même n'aurait jamais retenues.
        cat = categoriser(
            self._article(
                "Journalist arrested after covering the protest in Almaty",
            )
        )
        if cat["relation_acteur_traitement"]:
            preuves = cat["preuves"]["relation_acteur_traitement"]
            for terme in preuves["traitement_termes"]:
                self.assertNotIn(
                    terme,
                    ("arrest",),
                    "un terme sous-chaîne ne doit pas apparaître en preuve",
                )
