import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from archive import (
    ARCHIVE_FIELDS,
    BODY_KEEP_LEVELS,
    append_entries,
    derniere_vue,
    entry_from_article,
    iter_articles,
    load_archive,
    load_state,
    merge_scanned,
    rewrite_archive,
    save_state,
)


def article(**overrides):
    base = {
        "url": "https://www.hrw.org/news/2026/09/12/kazakhstan",
        "title": "Kazakhstan jails activist",
        "summary": "Un tribunal d'Almaty a condamné un activiste.",
        "source": "Human Rights Watch",
        "source_label": "HRW",
        "language": "en",
        "date": None,
        "body": "Le corps complet de l'article.",
        "level": "E",
    }
    base.update(overrides)
    return base


class EntryShapeTests(unittest.TestCase):
    def test_entry_carries_only_immutable_facts(self):
        entry = entry_from_article(article(score=87, level="A"), "cle")
        self.assertEqual(set(entry), set(ARCHIVE_FIELDS))
        for volatile in ("score", "level", "theme", "relevant", "signals"):
            self.assertNotIn(volatile, entry)

    def test_body_kept_for_significant_levels(self):
        for level in sorted(BODY_KEEP_LEVELS):
            entry = entry_from_article(article(level=level), "cle")
            self.assertTrue(entry["body"], f"corps perdu pour le niveau {level}")

    def test_body_dropped_for_level_e(self):
        # 95 % du corpus : stocker leur corps ferait des dizaines de Mo.
        entry = entry_from_article(article(level="E"), "cle")
        self.assertEqual(entry["body"], "")

    def test_datetime_date_is_serialized(self):
        from datetime import datetime, timezone

        moment = datetime(2026, 9, 12, 15, 13, tzinfo=timezone.utc)
        entry = entry_from_article(article(date=moment), "cle")
        self.assertEqual(entry["date"], moment.isoformat())
        json.dumps(entry)  # doit rester sérialisable


class RoundTripTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "archive.jsonl"
        self.state_path = Path(self.dir.name) / "state.json"

    def tearDown(self):
        self.dir.cleanup()

    def test_append_then_load(self):
        append_entries([entry_from_article(article(), "a")], self.path)
        append_entries([entry_from_article(article(), "b")], self.path)

        loaded = load_archive(self.path)
        self.assertEqual(set(loaded), {"a", "b"})

    def test_append_never_rewrites_existing_lines(self):
        # C'est toute la raison d'être du format : git ne doit stocker
        # que les lignes ajoutées, pas une copie entière du fichier.
        append_entries([entry_from_article(article(), "a")], self.path)
        premiere_ligne = self.path.read_text(encoding="utf-8").splitlines()[0]

        append_entries([entry_from_article(article(), "b")], self.path)
        lignes = self.path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(lignes[0], premiere_ligne)
        self.assertEqual(len(lignes), 2)

    def test_missing_file_loads_as_empty(self):
        self.assertEqual(load_archive(self.path), {})

    def test_corrupted_line_does_not_lose_the_others(self):
        append_entries([entry_from_article(article(), "a")], self.path)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write("{ceci n'est pas du json\n")
        append_entries([entry_from_article(article(), "b")], self.path)

        loaded = load_archive(self.path)
        self.assertEqual(set(loaded), {"a", "b"})

    def test_rewrite_replaces_everything(self):
        append_entries([entry_from_article(article(), "a")], self.path)
        rewrite_archive([entry_from_article(article(), "z")], self.path)
        self.assertEqual(set(load_archive(self.path)), {"z"})

    def test_state_round_trip(self):
        save_state({"dernier_scan": "2026-09-13T11:00:00+00:00",
                    "vus_avant": {"a": "2026-09-01T11:00:00+00:00"}},
                   self.state_path)
        state = load_state(self.state_path)
        self.assertEqual(state["vus_avant"]["a"], "2026-09-01T11:00:00+00:00")

    def test_missing_state_has_usable_shape(self):
        state = load_state(self.state_path)
        self.assertEqual(state["dernier_scan"], "")
        self.assertEqual(state["vus_avant"], {})

    def test_corrupted_state_is_reset_not_fatal(self):
        self.state_path.write_text("{pas du json", encoding="utf-8")
        state = load_state(self.state_path)
        self.assertEqual(state["vus_avant"], {})


class MergeTests(unittest.TestCase):
    def test_new_articles_are_returned_for_appending(self):
        archive = {}
        state = {"vus_avant": {}}
        nouvelles = merge_scanned(
            archive, state,
            [("a", article()), ("b", article())],
            scan_date="2026-09-13T11:00:00+00:00",
        )
        self.assertEqual(len(nouvelles), 2)
        self.assertEqual(set(archive), {"a", "b"})

    def test_known_article_is_not_duplicated(self):
        archive = {}
        state = {"vus_avant": {}}
        merge_scanned(archive, state, [("a", article())],
                      scan_date="2026-09-13T10:00:00+00:00")
        nouvelles = merge_scanned(archive, state, [("a", article())],
                                  scan_date="2026-09-13T11:00:00+00:00")

        self.assertEqual(nouvelles, [])
        self.assertEqual(len(archive), 1)

    def test_first_seen_date_never_moves(self):
        archive = {}
        state = {"vus_avant": {}}
        merge_scanned(archive, state, [("a", article())],
                      scan_date="2026-09-13T10:00:00+00:00")
        merge_scanned(archive, state, [("a", article())],
                      scan_date="2026-09-20T10:00:00+00:00")

        self.assertEqual(archive["a"]["premiere_vue"], "2026-09-13T10:00:00+00:00")

    def test_last_seen_date_moves_and_lives_in_state_only(self):
        archive = {}
        state = {"vus_avant": {}}
        merge_scanned(archive, state, [("a", article())],
                      scan_date="2026-09-13T10:00:00+00:00")
        merge_scanned(archive, state, [("a", article())],
                      scan_date="2026-09-20T10:00:00+00:00")

        self.assertEqual(derniere_vue(state, "a"), "2026-09-20T10:00:00+00:00")
        # L'entrée d'archive ne doit porter aucune date mutable, sinon
        # chaque run réécrirait toutes les lignes du fichier.
        self.assertNotIn("derniere_vue", archive["a"])
        self.assertNotIn("dernier_scan", archive["a"])

    def test_article_absent_from_this_run_keeps_its_old_last_seen(self):
        archive = {}
        state = {"vus_avant": {}}
        merge_scanned(archive, state,
                      [("a", article()), ("b", article())],
                      scan_date="2026-09-13T10:00:00+00:00")
        merge_scanned(archive, state, [("a", article())],
                      scan_date="2026-09-20T10:00:00+00:00")

        self.assertEqual(derniere_vue(state, "b"), "2026-09-13T10:00:00+00:00")
        self.assertEqual(derniere_vue(state, "a"), "2026-09-20T10:00:00+00:00")

    def test_only_vanished_articles_are_listed_in_the_state(self):
        # Tout l'intérêt : la règle est "vu au dernier scan", seules les
        # exceptions coûtent de la place.
        archive = {}
        state = {"vus_avant": {}}
        vus = [(str(i), article()) for i in range(50)]
        merge_scanned(archive, state, vus, scan_date="2026-09-13T10:00:00+00:00")
        self.assertEqual(state["vus_avant"], {})

        merge_scanned(archive, state, vus[:49],
                      scan_date="2026-09-20T10:00:00+00:00")
        self.assertEqual(list(state["vus_avant"]), ["49"])

    def test_a_vanished_article_date_never_moves_again(self):
        # Sa ligne dans l'état est écrite une fois, donc git ne la
        # stocke qu'une fois.
        archive = {}
        state = {"vus_avant": {}}
        merge_scanned(archive, state, [("a", article()), ("b", article())],
                      scan_date="2026-09-13T10:00:00+00:00")
        for jour in ("14", "15", "16"):
            merge_scanned(archive, state, [("a", article())],
                          scan_date=f"2026-09-{jour}T10:00:00+00:00")

        self.assertEqual(state["vus_avant"]["b"], "2026-09-13T10:00:00+00:00")

    def test_reappearing_article_leaves_the_exception_list(self):
        archive = {}
        state = {"vus_avant": {}}
        merge_scanned(archive, state, [("a", article()), ("b", article())],
                      scan_date="2026-09-13T10:00:00+00:00")
        merge_scanned(archive, state, [("a", article())],
                      scan_date="2026-09-14T10:00:00+00:00")
        self.assertIn("b", state["vus_avant"])

        merge_scanned(archive, state, [("a", article()), ("b", article())],
                      scan_date="2026-09-15T10:00:00+00:00")
        self.assertEqual(state["vus_avant"], {})
        self.assertEqual(derniere_vue(state, "b"), "2026-09-15T10:00:00+00:00")

    def test_empty_keys_are_skipped(self):
        archive = {}
        state = {"vus_avant": {}}
        merge_scanned(archive, state, [("", article())])
        self.assertEqual(archive, {})


class IterArticlesTests(unittest.TestCase):
    def test_yields_rescorable_articles_with_both_dates(self):
        archive = {}
        state = {"vus_avant": {}}
        merge_scanned(archive, state, [("a", article())],
                      scan_date="2026-09-13T10:00:00+00:00")

        articles = list(iter_articles(archive, state))
        self.assertEqual(len(articles), 1)

        found = articles[0]
        self.assertEqual(found["title"], "Kazakhstan jails activist")
        self.assertEqual(found["premiere_vue"], "2026-09-13T10:00:00+00:00")
        self.assertEqual(found["derniere_vue"], "2026-09-13T10:00:00+00:00")
        self.assertEqual(found["dernier_scan"], "2026-09-13T10:00:00+00:00")

    def test_yielded_articles_carry_no_stale_score(self):
        # Le score est recalculé à chaque run : le servir depuis
        # l'archive ferait mentir un rescore.
        archive = {}
        state = {"vus_avant": {}}
        merge_scanned(archive, state, [("a", article(score=99, level="A"))])

        found = next(iter(iter_articles(archive, state)))
        for volatile in ("score", "level", "theme", "relevant"):
            self.assertNotIn(volatile, found)


if __name__ == "__main__":
    unittest.main()
