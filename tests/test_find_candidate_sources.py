import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from find_candidate_sources import (
    domain_of,
    extract_outbound_domains,
    find_candidates,
    is_excluded,
    is_same_organization,
    known_domains,
)


class DomainOfTests(unittest.TestCase):
    def test_strips_www_prefix(self):
        self.assertEqual(
            domain_of("https://www.example.com/a/b"),
            "example.com",
        )

    def test_keeps_subdomain(self):
        self.assertEqual(
            domain_of("https://en.example.com/a"),
            "en.example.com",
        )


class IsExcludedTests(unittest.TestCase):
    def test_excludes_known_social_domain(self):
        self.assertTrue(is_excluded("facebook.com"))

    def test_excludes_subdomain_of_excluded(self):
        self.assertTrue(is_excluded("ads.doubleclick.net"))

    def test_does_not_exclude_unrelated_domain(self):
        self.assertFalse(is_excluded("ohchr.org"))


class IsSameOrganizationTests(unittest.TestCase):
    def test_same_label_different_tld_is_same_org(self):
        # Cas réel observé : un article sur aljazeera.com pointe vers
        # careers.aljazeera.net (son propre réseau, pas une source tierce).
        self.assertTrue(
            is_same_organization("careers.aljazeera.net", "aljazeera.com")
        )

    def test_same_apex_different_subdomain_is_same_org(self):
        self.assertTrue(
            is_same_organization("about.rferl.org", "rferl.org")
        )

    def test_different_organization_is_not_same_org(self):
        self.assertFalse(
            is_same_organization("ohchr.org", "rferl.org")
        )


class KnownDomainsTests(unittest.TestCase):
    def test_includes_real_source_domains(self):
        domains = known_domains()

        self.assertIn("hrw.org", domains)
        self.assertIn("eurasianet.org", domains)


class ExtractOutboundDomainsTests(unittest.TestCase):
    def test_excludes_own_domain_and_boilerplate(self):
        html = """
        <a href="https://example.com/other-article">same site</a>
        <a href="https://facebook.com/share">share</a>
        <a href="https://ohchr.org/report">the actual citation</a>
        <a href="/relative/path">relative link</a>
        """

        domains = extract_outbound_domains(html, own_domain="example.com")

        self.assertEqual(domains, {"ohchr.org"})

    def test_excludes_same_organization_under_other_domain(self):
        html = """
        <a href="https://training.aljazeera.net/careers">same org</a>
        <a href="https://ohchr.org/report">real citation</a>
        """

        domains = extract_outbound_domains(html, own_domain="aljazeera.com")

        self.assertEqual(domains, {"ohchr.org"})


class FindCandidatesTests(unittest.TestCase):
    def test_counts_citations_across_articles_and_skips_known_domains(self):
        html_with_new_and_known_link = (
            '<a href="https://newngo.org/report">ref</a>'
            '<a href="https://hrw.org/report">known</a>'
        )
        rows = [
            {"url": "https://source-a.example/1", "title": "Article 1"},
            {"url": "https://source-b.example/2", "title": "Article 2"},
        ]

        import find_candidate_sources as module

        original_fetch_url = module.fetch_url
        module.fetch_url = lambda *a, **k: html_with_new_and_known_link
        try:
            counts, examples = find_candidates(rows, known_domains())
        finally:
            module.fetch_url = original_fetch_url

        self.assertEqual(counts["newngo.org"], 2)
        self.assertNotIn("hrw.org", counts)
        self.assertEqual(examples["newngo.org"][0], "Article 1")


if __name__ == "__main__":
    unittest.main()
