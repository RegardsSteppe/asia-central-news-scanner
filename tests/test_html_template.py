import re
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from html_template import create_web_page
from sources import PROFILE_GROUP_ORDER


EMPTY_STATS = {
    "analyzed": 0,
    "retained": 0,
    "avg_score": 0.0,
    "level_a": 0,
    "level_b": 0,
    "level_c": 0,
    "level_d": 0,
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


if __name__ == "__main__":
    unittest.main()
