import re
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from html_template import (
    ARCHIVAL_AGE_DAYS,
    article_age_days,
    create_web_page,
    format_relative_age,
    render_article_card,
)
from sources import PROFILE_GROUP_ORDER


EMPTY_STATS = {
    "analyzed": 0,
    "retained": 0,
    "avg_score": 0.0,
    "level_a": 0,
    "level_b": 0,
    "level_c": 0,
    "level_d": 0,
    "level_e": 0,
    "sources_successful": 0,
    "sources_total": 0,
    "relevance_rate": 0.0,
}


def make_audit_row(title, category):
    return {
        "title": title,
        "source": "Test Source",
        "category": category,
        "url": "https://example.com/a",
        "date": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "theme": "Faible priorité",
        "score": 10,
        "level": "D",
        "relevant": False,
        "signals": {},
    }


class AuditGroupingTests(unittest.TestCase):
    def test_audit_rows_are_grouped_by_category_in_fixed_order(self):
        # Les catégories doivent apparaître dans PROFILE_GROUP_ORDER,
        # pas dans l'ordre d'arrivée des articles (ici volontairement
        # inversé par rapport à cet ordre).
        audit = [
            make_audit_row("Z", "Médias officiels (contrepoint)"),
            make_audit_row("Y", "Investigation"),
            make_audit_row("X", "Droits humains & presse"),
        ]

        html_out = create_web_page(
            articles=[],
            audit=audit,
            stats=EMPTY_STATS,
            title_words=[],
            synthesis="",
        )

        groups_found = re.findall(
            r'<h3>\s*([^<]+?)\s*<span class="audit-group-count">',
            html_out,
        )

        self.assertEqual(
            groups_found,
            ["Droits humains &amp; presse", "Investigation",
             "Médias officiels (contrepoint)"],
        )

    def test_unknown_category_still_rendered(self):
        audit = [make_audit_row("W", "Autres")]

        html_out = create_web_page(
            articles=[],
            audit=audit,
            stats=EMPTY_STATS,
            title_words=[],
            synthesis="",
        )

        self.assertIn("Autres", html_out)
        self.assertIn("1 article", html_out)

    def test_empty_audit_produces_no_groups(self):
        html_out = create_web_page(
            articles=[],
            audit=[],
            stats=EMPTY_STATS,
            title_words=[],
            synthesis="",
        )

        self.assertNotIn('<div class="audit-group">', html_out)


def make_article(title, date, score=80, level="A"):
    return {
        "title": title,
        "source": "Test Source",
        "source_label": "Test profile",
        "url": "https://example.com/a",
        "summary": "Summary.",
        "theme": "Theme",
        "reasons": ["r1"],
        "date": date,
        "score": score,
        "level": level,
    }


class ArticleAgeDisplayTests(unittest.TestCase):
    """
    Décidé avec l'utilisateur le 2026-09-11 : le score/niveau d'un
    article reste purement sémantique (voir scoring.py — le vieux
    freshness_score, jamais réellement alimenté, a été retiré du
    calcul), mais l'affichage doit quand même permettre de repérer
    d'un coup d'œil un article ancien qui refait surface — d'où
    l'indicateur d'âge relatif et le badge "republié" sur chaque
    carte, purement informatifs.
    """

    def test_relative_age_for_recent_article(self):
        now = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
        yesterday = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)

        self.assertEqual(format_relative_age(yesterday, now=now), "hier")

    def test_relative_age_for_old_article(self):
        now = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
        three_months_ago = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)

        self.assertIn("mois", format_relative_age(three_months_ago, now=now))

    def test_relative_age_empty_for_missing_date(self):
        self.assertEqual(format_relative_age(None), "")

    def test_archival_badge_shown_past_threshold(self):
        now = datetime(2026, 9, 11, tzinfo=timezone.utc)
        old_date = now - timedelta(days=ARCHIVAL_AGE_DAYS + 1)

        self.assertGreaterEqual(
            article_age_days(old_date, now=now), ARCHIVAL_AGE_DAYS
        )

        html_out = render_article_card(
            make_article("Old republished report", old_date)
        )

        self.assertIn("badge-archival", html_out)

    def test_archival_badge_absent_for_recent_article(self):
        now = datetime(2026, 9, 11, tzinfo=timezone.utc)
        recent_date = now - timedelta(days=2)

        html_out = render_article_card(
            make_article("Recent case", recent_date)
        )

        self.assertNotIn("badge-archival", html_out)

    def test_score_and_level_are_untouched_by_age(self):
        # Le point de départ de cette fonctionnalité : deux articles
        # identiques en score/niveau, l'un frais et l'autre ancien,
        # doivent afficher exactement le même score et le même niveau
        # — seul l'affichage de fraîcheur doit différer.
        now = datetime(2026, 9, 11, tzinfo=timezone.utc)

        fresh_html = render_article_card(
            make_article("Fresh case", now - timedelta(days=1), score=92, level="A")
        )
        old_html = render_article_card(
            make_article("Old case", now - timedelta(days=200), score=92, level="A")
        )

        self.assertIn("92/100", fresh_html)
        self.assertIn("92/100", old_html)
        self.assertIn('badge-A', fresh_html)
        self.assertIn('badge-A', old_html)


if __name__ == "__main__":
    unittest.main()


class SafeUrlTests(unittest.TestCase):
    """
    Les URL affichées proviennent du HTML scrapé de sites tiers. Un
    site compromis peut servir un href "javascript:..." que le scanner
    republierait en lien cliquable sur le site public — l'échappement
    HTML ne protège pas du schéma, seulement du texte.
    """

    def _card(self, url):
        from html_template import render_article_card

        return render_article_card(
            {
                "title": "Titre",
                "summary": "resume",
                "url": url,
                "source": "Source",
                "level": "A",
                "score": 80,
                "reasons": ["raison"],
                "theme": "theme",
                "date": None,
            }
        )

    def _href(self, html_output):
        found = re.search(r'href="([^"]*)"', html_output)
        return found.group(1) if found else None

    def test_keeps_legitimate_http_urls(self):
        for url in (
            "https://www.hrw.org/news/2026/09/12/kazakhstan",
            "http://example.org/article",
        ):
            self.assertEqual(self._href(self._card(url)), url)

    def test_drops_javascript_scheme(self):
        self.assertEqual(self._href(self._card("javascript:alert(1)")), "")

    def test_drops_data_scheme(self):
        self.assertEqual(self._href(self._card("data:text/html;base64,SGk=")), "")

    def test_scheme_check_is_case_insensitive(self):
        self.assertEqual(self._href(self._card("JavaScript:alert(1)")), "")

    def test_drops_scheme_hidden_behind_whitespace(self):
        self.assertEqual(self._href(self._card("  javascript:alert(1)")), "")


class CategorisationDashboardTests(unittest.TestCase):
    """Tableau de bord des catégories descriptives (categorisation.py)."""

    def _stats(self):
        from categorisation import agreger_categorisations

        cats = [
            {
                "geo": ["kazakhstan"], "acteur": ["journaliste"],
                "traitement": ["detention"], "type": "evenement_date",
            },
            {
                "geo": ["kazakhstan", "russie"], "acteur": ["aucun"],
                "traitement": ["aucun"], "type": "indetermine",
            },
            {
                "geo": [], "acteur": ["aucun"],
                "traitement": ["aucun"], "type": "indetermine",
            },
        ]
        return agreger_categorisations(cats)

    def test_every_schema_class_has_a_readable_label(self):
        # Sans ce garde-fou, une classe ajoutée au schéma s'affiche
        # telle quelle ("minorite_ethnique") sur le site public.
        #
        # Le test porte sur _libelle_classe() et non sur la table :
        # depuis l'ajout de tous les pays du monde, les libellés ont
        # deux sources (la table curée et pays_monde.py générée), et
        # c'est la fonction qui doit les réconcilier.
        from html_template import _libelle_classe
        from categorisation import (
            ACTEUR_TYPE_TERMS,
            TRAITEMENT_TYPE_TERMS,
            _GEO_TERM_COUNTRY,
        )

        classes = (
            set(ACTEUR_TYPE_TERMS)
            | set(TRAITEMENT_TYPE_TERMS)
            | set(_GEO_TERM_COUNTRY.values())
            | {"autre", "evenement_date", "rapport_analyse",
               "plaidoyer_communique", "navigation", "indetermine",
               "page_thematique"}
        )

        # Un libellé lisible ne contient pas d'underscore et commence
        # par une majuscule : c'est ce qui distingue "Minorité
        # ethnique" de l'identifiant brut qui fuirait sur le site.
        bruts = sorted(
            c for c in classes
            if "_" in _libelle_classe(c) or not _libelle_classe(c)[:1].isupper()
        )
        self.assertEqual(bruts, [], f"{len(bruts)} classe(s) sans libellé")

    def test_coverage_counts_articles_not_classes(self):
        # Un article "Kazakhstan + Russie" porte deux valeurs mais reste
        # un seul article décrit : la couverture ne doit pas le compter
        # deux fois et dépasser 100%.
        stats = self._stats()
        geo = next(a for a in stats["axes"] if a["cle"] == "geo")
        self.assertEqual(geo["decrits"], 2)
        self.assertAlmostEqual(geo["couverture"], 66.7, places=1)

    def test_null_class_is_excluded_from_the_bars(self):
        # "aucun" pèse plus que toutes les vraies classes réunies ;
        # le laisser dans le graphique écraserait tout le reste.
        stats = self._stats()
        for cle in ("acteur", "traitement"):
            axe = next(a for a in stats["axes"] if a["cle"] == cle)
            self.assertNotIn("aucun", [c["nom"] for c in axe["classes"]])

        type_axe = next(a for a in stats["axes"] if a["cle"] == "type")
        self.assertNotIn("indetermine", [c["nom"] for c in type_axe["classes"]])

    def test_renders_labels_values_and_no_raw_identifiers(self):
        from html_template import render_categorisation_dashboard

        html_output = render_categorisation_dashboard(self._stats())
        self.assertIn("Kazakhstan", html_output)
        self.assertIn("Journaliste", html_output)
        self.assertNotIn("evenement_date", html_output)

    def test_empty_stats_render_nothing(self):
        from html_template import render_categorisation_dashboard

        self.assertEqual(render_categorisation_dashboard(None), "")
        self.assertEqual(
            render_categorisation_dashboard({"total": 0, "axes": []}), ""
        )

    def test_bar_widths_are_relative_to_the_axis_maximum(self):
        from html_template import render_categorisation_axe

        axe = {
            "libelle": "Test", "couverture": 50.0, "decrits": 5,
            "classes": [
                {"nom": "kazakhstan", "effectif": 100},
                {"nom": "russie", "effectif": 25},
            ],
        }
        html_output = render_categorisation_axe(axe, total=10)
        self.assertIn("width: 100.0%", html_output)
        self.assertIn("width: 25.0%", html_output)
