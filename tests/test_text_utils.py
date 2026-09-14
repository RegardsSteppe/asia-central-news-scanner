import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from text_utils import (
    clean_text,
    clean_title,
    normalize_url,
    parse_date,
    article_date_timestamp,
    strip_boilerplate,
    strip_related_blocks,
)


class CleanTextTests(unittest.TestCase):
    def test_none_returns_empty_string(self):
        self.assertEqual(clean_text(None), "")

    def test_collapses_whitespace(self):
        self.assertEqual(clean_text("  hello   world  "), "hello world")

    def test_unescapes_html_entities(self):
        self.assertEqual(clean_text("Tom &amp; Jerry"), "Tom & Jerry")

    def test_strips_zero_width_characters(self):
        self.assertEqual(clean_text("hello\u200bworld"), "helloworld")

    def test_repairs_mojibake(self):
        # "café" mis-decoded as latin1/cp1252 then re-encoded UTF-8.
        mojibake = "café".encode("utf-8").decode("latin1")
        self.assertEqual(clean_text(mojibake), "café")

    def test_non_string_input_is_stringified(self):
        self.assertEqual(clean_text(123), "123")


class CleanTitleTests(unittest.TestCase):
    def test_collapses_and_strips(self):
        self.assertEqual(clean_title("  Some   Title\n"), "Some Title")

    def test_empty_input(self):
        self.assertEqual(clean_title(""), "")


class NormalizeUrlTests(unittest.TestCase):
    def test_removes_fragment(self):
        self.assertEqual(
            normalize_url("https://example.com/a?x=1#section"),
            "https://example.com/a?x=1",
        )

    def test_missing_scheme_returns_empty(self):
        self.assertEqual(normalize_url("/relative/path"), "")

    def test_resolves_relative_with_base(self):
        self.assertEqual(
            normalize_url("/a/b", base_url="https://example.com"),
            "https://example.com/a/b",
        )

    def test_empty_input(self):
        self.assertEqual(normalize_url(""), "")

    def test_none_input(self):
        self.assertEqual(normalize_url(None), "")

    def test_strips_tracking_params(self):
        self.assertEqual(
            normalize_url(
                "https://example.com/a?utm_source=x&utm_medium=y&fbclid=z"
            ),
            "https://example.com/a",
        )

    def test_keeps_non_tracking_query_params(self):
        self.assertEqual(
            normalize_url("https://example.com/a?id=123&utm_source=x"),
            "https://example.com/a?id=123",
        )


class ParseDateTests(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(parse_date(None))

    def test_iso_with_z_suffix(self):
        dt = parse_date("2024-03-15T10:00:00Z")
        self.assertEqual(dt, datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc))

    def test_rfc2822(self):
        dt = parse_date("Fri, 15 Mar 2024 10:00:00 GMT")
        self.assertEqual(dt.year, 2024)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 15)

    def test_invalid_string_returns_none(self):
        self.assertIsNone(parse_date("not a date"))

    def test_struct_time_input(self):
        import time

        struct = time.strptime("2024-03-15", "%Y-%m-%d")
        dt = parse_date(struct)
        self.assertEqual(dt.year, 2024)

    def test_naive_datetime_gets_utc(self):
        dt = parse_date(datetime(2024, 1, 1))
        self.assertEqual(dt.tzinfo, timezone.utc)


class ArticleDateTimestampTests(unittest.TestCase):
    def test_missing_date_returns_zero(self):
        self.assertEqual(article_date_timestamp({}), 0)

    def test_datetime_value(self):
        article = {"date": datetime(2024, 1, 1, tzinfo=timezone.utc)}
        self.assertGreater(article_date_timestamp(article), 0)


if __name__ == "__main__":
    unittest.main()


class StripRelatedBlocksTests(unittest.TestCase):
    """
    Régression du 2026-09-14, trouvée par le harnais de
    caractérisation : « Turkmenistan leader's son wins presidential
    election » montait de E à C parce que son corps contenait
    "Recommended Stories ... Turkmenistan's dissidents fear crackdown
    in Turkish exile ... end of list" — le titre d'un AUTRE article.
    Le scoring lisait un ancrage répressif qui n'appartenait pas à
    l'article scoré.
    """

    def test_retire_le_bloc_recommande_delimite(self):
        # Le cas réel, abrégé. Les bornes sont explicites, donc la
        # coupe est chirurgicale et le texte se referme proprement.
        corps = (
            "Serdar Berdymukhamedov won the election on Tuesday. "
            "Recommended Stories list of 1 item list 1 of 1 "
            "Turkmenistan's dissidents fear crackdown in Turkish exile "
            "end of list "
            "His nearest rival was a little-known official."
        )
        propre = strip_related_blocks(corps)
        self.assertNotIn("crackdown", propre)
        self.assertIn("won the election on Tuesday", propre)
        self.assertIn("His nearest rival", propre)

    def test_tronque_un_marqueur_de_pied_de_page(self):
        corps = "Le tribunal a condamné l'activiste. " * 20 + "Читайте также Активист осужден"
        propre = strip_related_blocks(corps)
        self.assertNotIn("Читайте также", propre)
        self.assertIn("Le tribunal a condamné", propre)

    def test_ne_tronque_pas_un_renvoi_en_plein_article(self):
        # Le garde-fou qui compte. Sur Novastan, « Lire aussi » et ses
        # équivalents arrivent au tiers de l'article, avec des
        # milliers de caractères de corps réel derrière : tronquer là
        # détruirait l'article. Seuls les marqueurs des derniers 20 %
        # sont traités comme du pied de page.
        suite = "Le déplacement de populations fut un instrument du pouvoir soviétique. " * 30
        corps = "Un reportage sur la frontière. Related Articles Nettoyage ethnique " + suite
        propre = strip_related_blocks(corps)
        self.assertIn("Related Articles", propre)
        self.assertIn("instrument du pouvoir soviétique", propre)

    def test_est_idempotent(self):
        # Condition de l'application en rattrapage sur l'archive :
        # repasser sur un corps déjà nettoyé ne doit rien changer,
        # sinon chaque run réécrirait l'archive entière.
        corps = (
            "Texte réel. Recommended Stories list of 2 items list 1 of 2 "
            "Autre titre end of list Suite du texte réel."
        )
        une_fois = strip_related_blocks(corps)
        self.assertEqual(strip_related_blocks(une_fois), une_fois)

    def test_accepte_les_valeurs_vides(self):
        self.assertEqual(strip_related_blocks(""), "")
        self.assertEqual(strip_related_blocks(None), "")


class StripBoilerplateTests(unittest.TestCase):
    """
    strip_related_blocks() travaille par marqueur ("Читайте также",
    "Recommended Stories") et ne couvre donc que les sites qui en ont
    un. Asia-Plus termine par un fil "Recent News" sans aucun
    marqueur, 24.kg par un bloc "Popular" : un marqueur par site ne
    passe pas à l'échelle.

    La table de boilerplate.py est dérivée mécaniquement du corpus par
    tools/detecter_boilerplate.py — un texte identique d'un article à
    l'autre d'une même source ne peut pas être le contenu de cet
    article-là.
    """

    def test_retire_le_pied_de_page_de_la_source(self):
        from boilerplate import BOILERPLATE_PAR_SOURCE

        source, suffixe = next(iter(BOILERPLATE_PAR_SOURCE.items()))
        corps = "Le tribunal a condamné l'activiste à huit ans. " + suffixe
        propre = strip_boilerplate(corps, source)
        self.assertNotIn(suffixe, propre)
        self.assertIn("condamné l'activiste", propre)

    def test_ne_touche_pas_au_corps_d_une_autre_source(self):
        # Le pied de page est indexé par source : l'appliquer
        # aveuglément retirerait du texte réel à qui ne l'a pas.
        from boilerplate import BOILERPLATE_PAR_SOURCE

        source, suffixe = next(iter(BOILERPLATE_PAR_SOURCE.items()))
        corps = "Un article d'une tout autre source. " + suffixe
        self.assertEqual(
            strip_boilerplate(corps, "Source Inconnue"), corps.strip()
        )

    def test_ne_retire_que_le_suffixe_pas_une_occurrence_interne(self):
        # Seul un suffixe est retiré. Le même texte au MILIEU d'un
        # article est du contenu cité, pas un pied de page.
        from boilerplate import BOILERPLATE_PAR_SOURCE

        source, suffixe = next(iter(BOILERPLATE_PAR_SOURCE.items()))
        corps = "Début. " + suffixe + " Et la suite du vrai article."
        propre = strip_boilerplate(corps, source)
        self.assertIn(suffixe, propre)

    def test_est_idempotent(self):
        # Condition du rattrapage sur l'archive : repasser sur un
        # corps déjà nettoyé ne doit rien changer, sinon chaque run
        # réécrirait l'archive entière.
        from boilerplate import BOILERPLATE_PAR_SOURCE

        source, suffixe = next(iter(BOILERPLATE_PAR_SOURCE.items()))
        corps = "Texte réel. " + suffixe
        une_fois = strip_boilerplate(corps, source)
        self.assertEqual(strip_boilerplate(une_fois, source), une_fois)

    def test_accepte_les_valeurs_vides(self):
        self.assertEqual(strip_boilerplate("", "Asia-Plus"), "")
        self.assertEqual(strip_boilerplate(None, "Asia-Plus"), "")
        self.assertEqual(strip_boilerplate("texte", None), "texte")


class TableBoilerplateTests(unittest.TestCase):
    """
    Garde-fous sur la table générée elle-même. Elle est produite par
    une heuristique, donc c'est ici qu'on vérifie que l'heuristique
    n'a pas dérapé.
    """

    def test_aucun_suffixe_absurdement_court(self):
        # En dessous de 120 caractères, une correspondance est une
        # coïncidence (deux articles finissant par la même phrase
        # banale), pas un pied de page.
        from boilerplate import BOILERPLATE_PAR_SOURCE

        for source, suffixe in BOILERPLATE_PAR_SOURCE.items():
            with self.subTest(source=source):
                self.assertGreaterEqual(len(suffixe), 120)

    def test_aucun_suffixe_de_taille_d_article(self):
        # Le garde-fou qui compte. Sans plafond, Kommersant ressortait
        # avec 4475 caractères partagés par 4 articles sur 180 : ce
        # n'était pas un pied de page mais le même discours du Kremlin
        # republié quatre fois.
        from boilerplate import BOILERPLATE_PAR_SOURCE

        for source, suffixe in BOILERPLATE_PAR_SOURCE.items():
            with self.subTest(source=source):
                self.assertLessEqual(len(suffixe), 4000)
