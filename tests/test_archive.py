import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from archive import (
    ARCHIVE_FIELDS,
    backfill_bodies,
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

    def test_body_kept_for_level_e(self):
        # Inversé le 2026-09-14. Le corps du niveau E était jeté alors
        # qu'on venait de le télécharger, et c'est exactement là que
        # les catégories sont vides : sans corps, 73% des articles qui
        # portent un "traitement" le perdent.
        entry = entry_from_article(article(level="E"), "cle")
        self.assertTrue(entry["body"])

    def test_body_levels_remain_configurable(self):
        # Échappatoire si l'archive devient trop lourde : on doit
        # pouvoir revenir au comportement d'avant sans toucher au code.
        import importlib
        import os
        from unittest.mock import patch

        import archive as archive_module

        # Le rechargement de restauration doit avoir lieu HORS du
        # patch : à l'intérieur, il relit la variable encore patchée et
        # laisse le module pollué pour tous les tests suivants.
        try:
            with patch.dict(os.environ, {"SCANNER_BODY_KEEP_LEVELS": "A,B"}):
                recharge = importlib.reload(archive_module)
                self.assertEqual(recharge.BODY_KEEP_LEVELS, frozenset({"A", "B"}))
                self.assertEqual(
                    recharge.entry_from_article(article(level="E"), "cle")["body"],
                    "",
                )
        finally:
            importlib.reload(archive_module)

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


class MergeFilesTests(unittest.TestCase):
    """
    Deux runs concurrents : celui qui pousse en second doit ajouter ses
    lignes à celles de l'autre, jamais les écraser.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.base = Path(self.dir.name) / "base.jsonl"
        self.incoming = Path(self.dir.name) / "incoming.jsonl"

    def tearDown(self):
        self.dir.cleanup()

    def test_union_of_both_files(self):
        from archive import merge_files

        append_entries([entry_from_article(article(), "a")], self.base)
        append_entries([entry_from_article(article(), "b")], self.incoming)

        ajoutees, corps = merge_files(self.base, self.incoming)

        self.assertEqual(ajoutees, 1)
        self.assertEqual(corps, 0)
        self.assertEqual(set(load_archive(self.base)), {"a", "b"})

    def test_entries_already_present_are_not_duplicated(self):
        from archive import merge_files

        append_entries([entry_from_article(article(), "a")], self.base)
        append_entries([entry_from_article(article(), "a")], self.incoming)

        self.assertEqual(merge_files(self.base, self.incoming), (0, 0))
        self.assertEqual(len(load_archive(self.base)), 1)

    def test_concurrent_run_lines_survive(self):
        from archive import merge_files

        # L'autre run a poussé "concurrent" pendant que nous tournions.
        append_entries([entry_from_article(article(), "concurrent")], self.base)
        append_entries(
            [entry_from_article(article(), k) for k in ("a", "b")],
            self.incoming,
        )

        merge_files(self.base, self.incoming)
        self.assertEqual(set(load_archive(self.base)), {"concurrent", "a", "b"})

    def test_missing_incoming_file_is_harmless(self):
        from archive import merge_files

        append_entries([entry_from_article(article(), "a")], self.base)
        self.assertEqual(merge_files(self.base, self.incoming), (0, 0))


class BackfillBodiesTests(unittest.TestCase):
    """
    merge_scanned() n'écrit que les nouveautés : sans backfill, un
    article déjà archivé qui reçoit enfin son corps ne verrait jamais
    sa ligne changer. Run du 2026-09-14 : 914 corps téléchargés, 18
    conservés, le reste retéléchargé à chaque run pour rien.
    """

    def _archive(self, body=""):
        entry = entry_from_article(article(level="A"), "cle")
        entry["body"] = body
        return {"cle": entry}

    def test_fills_a_missing_body_on_an_existing_entry(self):
        arch = self._archive(body="")
        scanned = [("cle", article(level="A", body="texte complet"))]

        self.assertEqual(backfill_bodies(arch, scanned), 1)
        self.assertEqual(arch["cle"]["body"], "texte complet")

    def test_never_replaces_a_body_with_a_shorter_one(self):
        # Une extraction partielle (mur payant, redirection) ne doit
        # pas dégrader un texte déjà complet.
        arch = self._archive(body="un texte complet et long")
        scanned = [("cle", article(level="A", body="court"))]

        self.assertEqual(backfill_bodies(arch, scanned), 0)
        self.assertEqual(arch["cle"]["body"], "un texte complet et long")

    def test_ignores_articles_absent_from_the_archive(self):
        arch = self._archive(body="")
        scanned = [("inconnue", article(level="A", body="texte"))]

        self.assertEqual(backfill_bodies(arch, scanned), 0)
        self.assertEqual(arch["cle"]["body"], "")

    def test_respects_the_configured_levels(self):
        import importlib
        import os
        from unittest.mock import patch

        import archive as archive_module

        # Restauration hors du patch — voir la note dans
        # test_body_levels_remain_configurable.
        try:
            with patch.dict(os.environ, {"SCANNER_BODY_KEEP_LEVELS": "A"}):
                recharge = importlib.reload(archive_module)
                entry = recharge.entry_from_article(article(level="A"), "cle")
                entry["body"] = ""
                arch = {"cle": entry}
                scanned = [("cle", article(level="E", body="texte"))]
                self.assertEqual(recharge.backfill_bodies(arch, scanned), 0)
        finally:
            importlib.reload(archive_module)

    def test_empty_body_is_not_counted_as_an_update(self):
        arch = self._archive(body="")
        scanned = [("cle", article(level="A", body=""))]

        self.assertEqual(backfill_bodies(arch, scanned), 0)


class ModuleStateIsRestoredTests(unittest.TestCase):
    """
    Les tests qui rechargent archive.py avec une variable
    d'environnement patchée doivent rendre le module intact.

    Sans ce garde-fou, la fuite ne se voit qu'à l'ordre d'exécution :
    elle est passée sous pytest en local et n'a cassé qu'en CI, sous
    "python -m unittest discover".
    """

    def test_body_keep_levels_are_back_to_the_default(self):
        import archive as archive_module

        self.assertEqual(
            archive_module.BODY_KEEP_LEVELS,
            frozenset({"A", "B", "C", "D", "E"}),
        )

    def test_an_entry_still_keeps_a_level_e_body(self):
        import archive as archive_module

        entry = archive_module.entry_from_article(article(level="E"), "cle")
        self.assertTrue(entry["body"])


class MergeCarriesBodiesTests(unittest.TestCase):
    """
    L'union doit porter sur les corps, pas seulement sur les clés.

    Le cas se produit dès qu'un run perd la course au push : il se
    remet sur la version distante puis refusionne la sienne, et ses
    corps fraîchement téléchargés portent justement sur des clés déjà
    archivées des deux côtés.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.base = Path(self.dir.name) / "base.jsonl"
        self.incoming = Path(self.dir.name) / "incoming.jsonl"

    def tearDown(self):
        self.dir.cleanup()

    def _ecrire(self, path, key, body):
        entry = entry_from_article(article(level="A"), key)
        entry["body"] = body
        append_entries([entry], path)

    def test_body_is_recovered_for_a_key_present_on_both_sides(self):
        from archive import merge_files

        self._ecrire(self.base, "a", "")
        self._ecrire(self.incoming, "a", "le texte complet")

        ajoutees, corps = merge_files(self.base, self.incoming)

        self.assertEqual((ajoutees, corps), (0, 1))
        self.assertEqual(load_archive(self.base)["a"]["body"], "le texte complet")

    def test_a_shorter_body_never_wins(self):
        from archive import merge_files

        self._ecrire(self.base, "a", "un texte complet et long")
        self._ecrire(self.incoming, "a", "court")

        self.assertEqual(merge_files(self.base, self.incoming), (0, 0))
        self.assertEqual(
            load_archive(self.base)["a"]["body"], "un texte complet et long"
        )

    def test_missing_entries_and_bodies_merge_in_one_pass(self):
        from archive import merge_files

        self._ecrire(self.base, "a", "")
        self._ecrire(self.incoming, "a", "texte de a")
        self._ecrire(self.incoming, "b", "texte de b")

        ajoutees, corps = merge_files(self.base, self.incoming)

        self.assertEqual((ajoutees, corps), (1, 1))
        relu = load_archive(self.base)
        self.assertEqual(set(relu), {"a", "b"})
        self.assertEqual(relu["a"]["body"], "texte de a")
        self.assertEqual(relu["b"]["body"], "texte de b")

    def test_concurrent_lines_survive_a_body_merge(self):
        from archive import merge_files

        # La réécriture déclenchée par les corps ne doit rien perdre.
        self._ecrire(self.base, "concurrent", "texte concurrent")
        self._ecrire(self.base, "a", "")
        self._ecrire(self.incoming, "a", "texte de a")

        merge_files(self.base, self.incoming)

        relu = load_archive(self.base)
        self.assertEqual(set(relu), {"concurrent", "a"})
        self.assertEqual(relu["concurrent"]["body"], "texte concurrent")


class BackfillDatesTests(unittest.TestCase):
    """
    Même angle mort que pour les corps : merge_scanned() n'écrit que
    les nouveautés, donc une date extraite après coup ne rejoignait
    jamais sa ligne. 5829 entrées sur 8824 sans date au 2026-09-14,
    dont 3545 dont la page avait pourtant été téléchargée.
    """

    def _archive(self, date=None):
        from archive import entry_from_article

        entry = entry_from_article(article(level="A"), "cle")
        entry["date"] = date
        return {"cle": entry}

    def test_fills_a_missing_date(self):
        from archive import backfill_dates

        arch = self._archive(date=None)
        scanned = [("cle", {"date": "2026-09-10T08:00:00+00:00"})]

        self.assertEqual(backfill_dates(arch, scanned), 1)
        self.assertEqual(arch["cle"]["date"], "2026-09-10T08:00:00+00:00")

    def test_never_overwrites_a_known_date(self):
        # Une date déjà connue vient du flux RSS, plus fiable qu'une
        # date devinée dans une page HTML.
        from archive import backfill_dates

        arch = self._archive(date="2026-01-01T00:00:00+00:00")
        scanned = [("cle", {"date": "2026-09-10T08:00:00+00:00"})]

        self.assertEqual(backfill_dates(arch, scanned), 0)
        self.assertEqual(arch["cle"]["date"], "2026-01-01T00:00:00+00:00")

    def test_serialises_a_datetime(self):
        from datetime import datetime, timezone

        from archive import backfill_dates

        arch = self._archive(date=None)
        moment = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)

        backfill_dates(arch, [("cle", {"date": moment})])

        self.assertEqual(arch["cle"]["date"], moment.isoformat())
        json.dumps(arch["cle"])  # doit rester sérialisable

    def test_ignores_absent_keys_and_empty_dates(self):
        from archive import backfill_dates

        arch = self._archive(date=None)

        self.assertEqual(backfill_dates(arch, [("inconnue", {"date": "x"})]), 0)
        self.assertEqual(backfill_dates(arch, [("cle", {"date": None})]), 0)
        self.assertIsNone(arch["cle"]["date"])
