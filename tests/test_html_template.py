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
