"""
Test de caractérisation : verrouille la sortie de classify_article() sur
478 articles réels (corpus publié du 2026-09-13, échantillon stratifié
couvrant tous les niveaux A-E, 69 sources et 166 articles avec corps).

Ce test ne dit PAS que le scoring est correct — il dit qu'il n'a pas
changé. C'est le filet qui permet de refactorer scoring.py (880 lignes,
complexité ~201 dans classify_article) en prouvant que la sortie reste
identique, article par article.

Quand un changement de score est VOULU, régénérer le snapshot :

    python tests/fixtures/rebuild_scoring_snapshot.py

et relire le diff : il montre exactement quels articles changent de
score, de niveau et pour quelles raisons.
"""

import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scoring import classify_article

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def signals_digest(signals):
    """Empreinte stable du dict de signaux (trop volumineux à stocker)."""
    payload = json.dumps(
        signals,
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def load_corpus():
    return json.loads(
        (FIXTURES / "scoring_corpus.json").read_text(encoding="utf-8")
    )


def load_snapshot():
    return json.loads(
        (FIXTURES / "scoring_snapshot.json").read_text(encoding="utf-8")
    )


class ScoringCharacterizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = load_corpus()
        cls.snapshot = load_snapshot()
        cls.scored = [
            classify_article(dict(article, date=None)) for article in cls.corpus
        ]

    def test_corpus_and_snapshot_stay_aligned(self):
        self.assertEqual(len(self.corpus), len(self.snapshot))
        for article, expected in zip(self.corpus, self.snapshot):
            self.assertEqual(article["url"], expected["url"])

    def test_scores_are_unchanged(self):
        drifted = [
            (expected["url"], expected["score"], actual["score"])
            for expected, actual in zip(self.snapshot, self.scored)
            if expected["score"] != actual["score"]
        ]
        self.assertEqual(
            drifted,
            [],
            f"{len(drifted)} article(s) ont changé de score "
            f"(attendu -> obtenu) : {drifted[:10]}",
        )

    def test_levels_are_unchanged(self):
        drifted = [
            (expected["url"], expected["level"], actual["level"])
            for expected, actual in zip(self.snapshot, self.scored)
            if expected["level"] != actual["level"]
        ]
        self.assertEqual(drifted, [], f"{len(drifted)} changement(s) de niveau : {drifted[:10]}")

    def test_relevance_theme_and_priority_are_unchanged(self):
        for field in ("relevant", "theme", "priority"):
            drifted = [
                (expected["url"], expected[field], actual[field])
                for expected, actual in zip(self.snapshot, self.scored)
                if expected[field] != actual[field]
            ]
            self.assertEqual(
                drifted, [], f"{len(drifted)} changement(s) sur '{field}' : {drifted[:5]}"
            )

    def test_reasons_are_unchanged(self):
        drifted = [
            expected["url"]
            for expected, actual in zip(self.snapshot, self.scored)
            if expected["reasons"] != actual["reasons"]
        ]
        self.assertEqual(drifted, [], f"{len(drifted)} article(s) ont changé de raisons : {drifted[:5]}")

    def test_signals_are_unchanged(self):
        """
        Les signaux sont stockés sous forme d'empreinte (60+ clés par
        article) ; en cas d'écart on rejoue le diff clé par clé pour
        pointer le signal fautif plutôt qu'un hash illisible.
        """
        for expected, actual in zip(self.snapshot, self.scored):
            actual_digest = signals_digest(actual["signals"])
            if expected["signals_sha256"] == actual_digest:
                continue

            self.fail(
                f"signaux modifiés sur {expected['url']} — "
                f"score {expected['score']} -> {actual['score']}, "
                f"raisons {expected['reasons']} -> {actual['reasons']}. "
                "Si le changement est voulu, régénérer le snapshot via "
                "tests/fixtures/rebuild_scoring_snapshot.py"
            )


class CorpusShapeTests(unittest.TestCase):
    """Le corpus doit rester représentatif, sinon le filet ne protège rien."""

    def test_covers_every_level(self):
        levels = {entry["level"] for entry in load_snapshot()}
        self.assertEqual(levels, {"A", "B", "C", "D", "E"})

    def test_covers_articles_with_and_without_body(self):
        corpus = load_corpus()
        self.assertGreater(sum(1 for a in corpus if a["body"]), 100)
        self.assertGreater(sum(1 for a in corpus if not a["body"]), 100)

    def test_covers_multiple_languages_and_sources(self):
        corpus = load_corpus()
        self.assertGreaterEqual(len({a["source"] for a in corpus}), 20)
        self.assertGreaterEqual(len({a["language"] for a in corpus}), 3)


if __name__ == "__main__":
    unittest.main()
