import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import juge_llm
from verite_terrain import (
    a_arbitrer,
    charger_verite,
    comparer,
    ecrire_a_arbitrer,
    mesurer,
    resume,
)


def article(cle, relevant, level="E", titre="Titre", score=0):
    return {
        "url": cle,
        "title": titre,
        "source": "Source",
        "level": level,
        "score": score,
        "relevant": relevant,
        "reasons": [],
    }


def verdict(cle, pertinent, **extra):
    base = {"cle": cle, "pertinent": pertinent, "raison": "r", "confiance": "haute"}
    base.update(extra)
    return base


class ComparerTests(unittest.TestCase):
    def test_sorts_each_case_into_the_right_cell(self):
        articles = [
            article("a", True), article("b", False),
            article("c", True), article("d", False),
        ]
        verdicts = [
            verdict("a", True), verdict("b", False),
            verdict("c", False), verdict("d", True),
        ]

        resultat = comparer(articles, verdicts)

        self.assertEqual([c["cle"] for c in resultat["accord_retenu"]], ["a"])
        self.assertEqual([c["cle"] for c in resultat["accord_rejete"]], ["b"])
        self.assertEqual([c["cle"] for c in resultat["faux_positif_possible"]], ["c"])
        self.assertEqual([c["cle"] for c in resultat["faux_negatif_possible"]], ["d"])

    def test_unusable_verdict_is_never_counted_as_rejection(self):
        # Le compter comme "non pertinent" gonflerait silencieusement
        # les faux positifs du scanner.
        resultat = comparer(
            [article("a", True)],
            [{"cle": "a", "erreur": "modèle indisponible"}],
        )

        self.assertEqual(resultat["faux_positif_possible"], [])
        self.assertEqual(len(resultat["sans_verdict"]), 1)

    def test_verdict_for_an_unknown_article_is_ignored(self):
        resultat = comparer([article("a", True)], [verdict("inconnu", True)])
        self.assertEqual(resume(resultat)["articles_juges"], 0)

    def test_summary_reports_agreement_rate(self):
        articles = [article(str(i), True) for i in range(4)]
        verdicts = [verdict("0", True), verdict("1", True),
                    verdict("2", False), verdict("3", False)]

        chiffres = resume(comparer(articles, verdicts))

        self.assertEqual(chiffres["articles_juges"], 4)
        self.assertEqual(chiffres["taux_accord"], 0.5)


class ArbitrageTests(unittest.TestCase):
    def test_every_disagreement_is_included(self):
        articles = [article("a", True), article("b", False)]
        verdicts = [verdict("a", False), verdict("b", True)]

        cas = a_arbitrer(comparer(articles, verdicts), echantillon_accords=0)

        self.assertEqual({c["cle"] for c in cas}, {"a", "b"})

    def test_disagreements_are_ranked_by_severity(self):
        # Un A contredit est en haut du site ; un E contredit est noyé.
        articles = [
            article("faible", True, level="E"),
            article("grave", True, level="A"),
        ]
        verdicts = [verdict("faible", False), verdict("grave", False)]

        cas = a_arbitrer(comparer(articles, verdicts), echantillon_accords=0)

        self.assertEqual([c["cle"] for c in cas], ["grave", "faible"])

    def test_control_sample_of_agreements_is_included(self):
        # Sans lui, les cas où les DEUX se trompent restent invisibles.
        articles = [article(str(i), True) for i in range(50)]
        verdicts = [verdict(str(i), True) for i in range(50)]

        cas = a_arbitrer(comparer(articles, verdicts), echantillon_accords=10)

        self.assertEqual(len(cas), 10)
        self.assertTrue(
            all(c["motif_arbitrage"] == "échantillon de contrôle" for c in cas)
        )

    def test_sample_is_deterministic(self):
        articles = [article(str(i), True) for i in range(50)]
        verdicts = [verdict(str(i), True) for i in range(50)]

        premier = a_arbitrer(comparer(articles, verdicts), echantillon_accords=10)
        second = a_arbitrer(comparer(articles, verdicts), echantillon_accords=10)

        self.assertEqual([c["cle"] for c in premier], [c["cle"] for c in second])

    def test_sample_larger_than_population_does_not_raise(self):
        articles = [article("a", True)]
        cas = a_arbitrer(comparer(articles, [verdict("a", True)]),
                         echantillon_accords=500)
        self.assertEqual(len(cas), 1)


class MesureTests(unittest.TestCase):
    def test_perfect_scanner(self):
        articles = [article("a", True), article("b", False)]
        chiffres = mesurer(articles, {"a": True, "b": False})

        self.assertEqual(chiffres["precision"], 1.0)
        self.assertEqual(chiffres["rappel"], 1.0)
        self.assertEqual(chiffres["f1"], 1.0)

    def test_missed_article_lowers_recall_only(self):
        # Le scanner rate un article réellement pertinent.
        articles = [article("a", True), article("b", False)]
        chiffres = mesurer(articles, {"a": True, "b": True})

        self.assertEqual(chiffres["precision"], 1.0)
        self.assertEqual(chiffres["rappel"], 0.5)
        self.assertEqual(chiffres["faux_negatifs"], 1)

    def test_noise_lowers_precision_only(self):
        articles = [article("a", True), article("b", True)]
        chiffres = mesurer(articles, {"a": True, "b": False})

        self.assertEqual(chiffres["precision"], 0.5)
        self.assertEqual(chiffres["rappel"], 1.0)
        self.assertEqual(chiffres["faux_positifs"], 1)

    def test_unlabelled_articles_are_ignored(self):
        articles = [article("a", True), article("inconnu", True)]
        chiffres = mesurer(articles, {"a": True})
        self.assertEqual(chiffres["etiquetes"], 1)

    def test_no_labels_yields_zeros_not_a_crash(self):
        chiffres = mesurer([article("a", True)], {})
        self.assertEqual(chiffres["etiquetes"], 0)
        self.assertEqual(chiffres["f1"], 0.0)


class FichierVeriteTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "verite.json"

    def tearDown(self):
        self.dir.cleanup()

    def test_round_trip_through_the_arbitration_file(self):
        articles = [article("a", True), article("b", False)]
        verdicts = [verdict("a", False), verdict("b", True)]
        cas = a_arbitrer(comparer(articles, verdicts), echantillon_accords=0)

        ecrire_a_arbitrer(cas, self.path)

        # Non arbitré : rien ne compte encore.
        self.assertEqual(charger_verite(self.path), {})

        brut = json.loads(self.path.read_text(encoding="utf-8"))
        brut["etiquettes"]["a"]["pertinent"] = True
        self.path.write_text(json.dumps(brut), encoding="utf-8")

        self.assertEqual(charger_verite(self.path), {"a": True})

    def test_accepts_a_plain_key_to_bool_mapping(self):
        self.path.write_text(json.dumps({"a": True, "b": False}), encoding="utf-8")
        self.assertEqual(charger_verite(self.path), {"a": True, "b": False})

    def test_missing_file_is_empty_not_fatal(self):
        self.assertEqual(charger_verite(self.path), {})

    def test_corrupted_file_is_empty_not_fatal(self):
        self.path.write_text("{pas du json", encoding="utf-8")
        self.assertEqual(charger_verite(self.path), {})


class JugeReponseTests(unittest.TestCase):
    """
    Un petit modèle quantifié encadre souvent son JSON de prose : le
    parseur doit être tolérant, mais jamais au point d'inventer un
    verdict.
    """

    def test_parses_clean_json(self):
        lu = juge_llm.analyser_reponse(
            '{"pertinent": true, "raison": "activiste détenu", "confiance": "haute"}'
        )
        self.assertTrue(lu["pertinent"])
        self.assertEqual(lu["confiance"], "haute")

    def test_parses_json_wrapped_in_prose(self):
        lu = juge_llm.analyser_reponse(
            'Voici ma réponse :\n```json\n{"pertinent": false, "raison": "sport"}\n```'
        )
        self.assertFalse(lu["pertinent"])

    def test_unknown_confidence_falls_back_to_medium(self):
        lu = juge_llm.analyser_reponse('{"pertinent": true, "confiance": "totale"}')
        self.assertEqual(lu["confiance"], "moyenne")

    def test_missing_field_is_an_error_not_a_rejection(self):
        lu = juge_llm.analyser_reponse('{"raison": "je ne sais pas"}')
        self.assertIn("erreur", lu)
        self.assertNotIn("pertinent", lu)

    def test_non_boolean_verdict_is_an_error(self):
        lu = juge_llm.analyser_reponse('{"pertinent": "oui"}')
        self.assertIn("erreur", lu)

    def test_empty_response_is_an_error(self):
        self.assertIn("erreur", juge_llm.analyser_reponse(""))

    def test_prose_without_json_is_an_error(self):
        self.assertIn("erreur", juge_llm.analyser_reponse("Je ne peux pas répondre."))

    def test_prompt_carries_title_source_and_text(self):
        messages = juge_llm.construire_invite(
            {"title": "Titre T", "summary": "Résumé R", "source": "Source S"}
        )
        envoye = messages[-1]["content"]
        for attendu in ("Titre T", "Résumé R", "Source S"):
            self.assertIn(attendu, envoye)

    def test_prompt_falls_back_to_body_when_summary_is_empty(self):
        # Les articles passés par Google News ont un résumé vidé.
        messages = juge_llm.construire_invite(
            {"title": "T", "summary": "", "body": "Corps complet"}
        )
        self.assertIn("Corps complet", messages[-1]["content"])

    def test_model_failure_becomes_an_error_verdict(self):
        from unittest.mock import patch

        with patch.object(juge_llm, "_load_model", side_effect=RuntimeError("pas de GPU")):
            lu = juge_llm.juger_article({"title": "T"})

        self.assertIn("erreur", lu)
        self.assertNotIn("pertinent", lu)


if __name__ == "__main__":
    unittest.main()


class SansEtiquetageHumainTests(unittest.TestCase):
    """
    Le cas par défaut : personne n'arbitre. Il faut alors des chiffres
    honnêtes (un accord, pas une précision) et une sortie actionnable.
    """

    def test_agreement_is_never_called_precision(self):
        from verite_terrain import accord_avec_juge

        chiffres = accord_avec_juge(
            comparer([article("a", True)], [verdict("a", True)])
        )

        for interdit in ("precision", "rappel", "f1", "vrais_positifs"):
            self.assertNotIn(interdit, chiffres)
        self.assertIn("taux_accord", chiffres)

    def test_agreement_carries_its_own_warning(self):
        from verite_terrain import accord_avec_juge

        chiffres = accord_avec_juge(
            comparer([article("a", True)], [verdict("a", True)])
        )

        self.assertIn("avertissement", chiffres)
        self.assertIn("pas une mesure de justesse", chiffres["avertissement"])

    def test_cells_are_named_by_who_retained_not_by_who_is_right(self):
        from verite_terrain import accord_avec_juge

        chiffres = accord_avec_juge(
            comparer([article("a", False)], [verdict("a", True)])
        )

        self.assertEqual(chiffres["retenus_par_le_juge_seul"], 1)
        self.assertEqual(chiffres["retenus_par_le_scanner_seul"], 0)


class MotsSurRepresentesTests(unittest.TestCase):
    def test_finds_a_word_specific_to_disagreements(self):
        from verite_terrain import mots_sur_representes

        candidats = mots_sur_representes(
            ["militant torture prison"] * 4,
            ["football match stadium"] * 40,
        )

        mots = {c["mot"] for c in candidats}
        self.assertIn("torture", mots)
        self.assertNotIn("football", mots)

    def test_common_words_are_not_proposed(self):
        # Les mots-outils apparaissent des deux côtés : leur rapport
        # vaut ~1, donc pas besoin d'une liste de mots vides.
        from verite_terrain import mots_sur_representes

        candidats = mots_sur_representes(
            ["dans le pays une arrestation"] * 5,
            ["dans le pays une victoire"] * 50,
        )

        mots = {c["mot"] for c in candidats}
        self.assertIn("arrestation", mots)
        for outil in ("dans", "pays", "une"):
            self.assertNotIn(outil, mots)

    def test_rare_words_are_ignored_as_statistical_noise(self):
        from verite_terrain import mots_sur_representes

        candidats = mots_sur_representes(
            ["exceptionnel"], ["autre chose"] * 50
        )
        self.assertEqual(candidats, [])

    def test_empty_input_does_not_raise(self):
        from verite_terrain import mots_sur_representes

        self.assertEqual(mots_sur_representes([], []), [])


class AnalyseDesaccordsTests(unittest.TestCase):
    def test_groups_misses_by_source(self):
        from verite_terrain import analyser_desaccords

        articles = [
            article("a", False, titre="Militant arrêté"),
            article("b", False, titre="Militant condamné"),
        ]
        articles[0]["source"] = articles[1]["source"] = "HRW"
        verdicts = [verdict("a", True), verdict("b", True)]

        analyse = analyser_desaccords(comparer(articles, verdicts))

        self.assertEqual(analyse["rates"]["total"], 2)
        self.assertEqual(analyse["rates"]["par_source"][0]["source"], "HRW")
        self.assertEqual(analyse["rates"]["par_source"][0]["cas"], 2)

    def test_separates_misses_from_noise(self):
        from verite_terrain import analyser_desaccords

        articles = [article("rate", False), article("bruit", True)]
        verdicts = [verdict("rate", True), verdict("bruit", False)]

        analyse = analyser_desaccords(comparer(articles, verdicts))

        self.assertEqual(analyse["rates"]["total"], 1)
        self.assertEqual(analyse["bruit"]["total"], 1)

    def test_no_disagreement_yields_empty_analysis(self):
        from verite_terrain import analyser_desaccords

        analyse = analyser_desaccords(
            comparer([article("a", True)], [verdict("a", True)])
        )

        self.assertEqual(analyse["rates"]["total"], 0)
        self.assertEqual(analyse["rates"]["mots_candidats"], [])
