import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup

from article_ingestion import (
    build_article,
    extract_body,
    extract_published_date,
    looks_like_article_link,
    parse_rss,
)


class LooksLikeArticleLinkTests(unittest.TestCase):
    def test_rejects_empty_url_or_title(self):
        self.assertFalse(looks_like_article_link("", "Some title"))
        self.assertFalse(looks_like_article_link("https://example.com/news/1", ""))

    def test_rejects_short_title(self):
        self.assertFalse(looks_like_article_link("https://example.com/news/1", "Hi"))

    def test_rejects_generic_link_text(self):
        self.assertFalse(
            looks_like_article_link("https://example.com/news/1", "Read more")
        )

    def test_rejects_navigation_paths(self):
        self.assertFalse(
            looks_like_article_link(
                "https://example.com/tag/politics", "Politics articles here"
            )
        )

    def test_accepts_article_path(self):
        self.assertTrue(
            looks_like_article_link(
                "https://example.com/news/some-story", "A real headline here"
            )
        )

    def test_accepts_dated_path(self):
        self.assertTrue(
            looks_like_article_link(
                "https://example.com/2024/03/some-story", "A real headline here"
            )
        )

    def test_rejects_root_path(self):
        self.assertFalse(
            looks_like_article_link("https://example.com/", "A real headline here")
        )

    def test_rejects_single_segment_path(self):
        self.assertFalse(
            looks_like_article_link("https://example.com/story", "A real headline here")
        )

    def test_rejects_bare_monthly_archive_path(self):
        self.assertFalse(
            looks_like_article_link(
                "https://example.com/2024/03/", "March news archive"
            )
        )

    def test_accepts_dated_path_with_slug(self):
        self.assertTrue(
            looks_like_article_link(
                "https://example.com/2024/03/some-real-story",
                "A real headline here",
            )
        )

    def test_rejects_expert_profile_pages(self):
        self.assertFalse(
            looks_like_article_link(
                "https://www.hudson.org/experts/1346-riley-walters",
                "Riley Walters",
            )
        )

    def test_rejects_contributor_profile_pages(self):
        self.assertFalse(
            looks_like_article_link(
                "https://www.fpri.org/contributor/bram-wells/",
                "Bram Wells",
            )
        )

    def test_rejects_team_and_people_pages(self):
        self.assertFalse(
            looks_like_article_link(
                "https://eurasianet.org/people/alexander-thompson",
                "Alexander Thompson",
            )
        )
        self.assertFalse(
            looks_like_article_link(
                "https://novastan.org/de/team/", "Unser Team"
            )
        )

    def test_rejects_topic_and_tool_pages(self):
        # Régression : Amnesty/RSF/CPJ ont des pages thématiques/outils
        # (pas un article précis) avec un titre assez long pour passer
        # le filtre générique — l'utilisateur les a repérées sur le
        # site publié comme des "articles" qui n'en sont pas.
        cases = [
            (
                "https://www.amnesty.org/en/what-we-do/armed-conflict/",
                "Armed Conflict",
            ),
            (
                "https://www.amnesty.org/en/human-rights-education/",
                "Human Rights Education",
            ),
            (
                "https://www.amnesty.org/en/petition/ban-stun-grenades/",
                "Ban stun grenades in policing protests in Greece",
            ),
            (
                "https://rsf.org/fr/pays-r%C3%A9publique-d%C3%A9mocratique-du-congo",
                "République démocratique du Congo",
            ),
            ("https://rsf.org/fr/classement", "Classement mondial"),
            ("https://rsf.org/fr/barometre", "Baromètre en temps réel"),
            (
                "https://cpj.org/issue/press-freedom-in-the-us/",
                "Press freedom in the US",
            ),
            ("https://cpj.org/data/missing", "Missing Journalists"),
        ]

        for url, title in cases:
            with self.subTest(url=url):
                self.assertFalse(looks_like_article_link(url, title))


class ExtractPublishedDateTests(unittest.TestCase):
    def test_reads_article_published_time_meta(self):
        soup = BeautifulSoup(
            '<html><head><meta property="article:published_time" '
            'content="2024-03-15T10:00:00Z"></head><body></body></html>',
            "html.parser",
        )
        date = extract_published_date(soup)
        self.assertIsNotNone(date)
        self.assertEqual(date.year, 2024)
        self.assertEqual(date.month, 3)
        self.assertEqual(date.day, 15)

    def test_reads_time_tag_datetime_attribute(self):
        soup = BeautifulSoup(
            '<html><body><time datetime="2024-03-15">15 mars</time></body></html>',
            "html.parser",
        )
        date = extract_published_date(soup)
        self.assertIsNotNone(date)
        self.assertEqual(date.year, 2024)

    def test_returns_none_when_no_date_found(self):
        soup = BeautifulSoup("<html><body>No date here</body></html>", "html.parser")
        self.assertIsNone(extract_published_date(soup))


class ExtractBodySoftRedirectTests(unittest.TestCase):
    """
    Régression : certains sites répondent 200 OK mais redirigent
    silencieusement une URL d'article cassée vers leur page d'accueil
    (ou une autre page générique) — un code HTTP seul ne peut pas
    détecter ça. extract_body() doit reconnaître que le titre attendu
    n'apparaît nulle part sur la page reçue et refuser ce contenu
    plutôt que de le traiter comme le corps de l'article.
    """

    @patch("article_ingestion.fetch_url")
    def test_returns_empty_body_when_page_does_not_match_title(self, mock_fetch):
        mock_fetch.return_value = (
            "<html><head><title>Hudson Institute — Home</title></head>"
            "<body><h1>Welcome to Hudson Institute</h1>"
            "<p>Unrelated homepage content.</p></body></html>"
        )

        body, date = extract_body(
            "https://www.hudson.org/foreign-policy/some-removed-article",
            expected_title="Mr. Trump, Take the Golden Road to Samarkand",
        )

        self.assertEqual(body, "")
        self.assertIsNone(date)

    @patch("article_ingestion.fetch_url")
    def test_returns_body_when_page_matches_title(self, mock_fetch):
        mock_fetch.return_value = (
            "<html><head><title>Mr. Trump, Take the Golden Road to "
            "Samarkand | Hudson Institute</title></head>"
            "<body><article>Full article text about Samarkand.</article>"
            "</body></html>"
        )

        body, date = extract_body(
            "https://www.hudson.org/foreign-policy/mr-trump-take-golden-road-samarkand",
            expected_title="Mr. Trump, Take the Golden Road to Samarkand",
        )

        self.assertIn("Samarkand", body)


class BuildArticleTests(unittest.TestCase):
    def test_builds_expected_shape(self):
        article = build_article(
            source={"name": "Test Source", "label": "Test"},
            title="  A Title  ",
            summary="A summary",
            url="https://example.com/news/1",
            published="2024-03-15T10:00:00Z",
        )

        self.assertEqual(article["source"], "Test Source")
        self.assertEqual(article["source_label"], "Test")
        self.assertEqual(article["title"], "A Title")
        self.assertEqual(article["summary"], "A summary")
        self.assertEqual(article["url"], "https://example.com/news/1")
        self.assertEqual(article["body"], "")
        self.assertIsNotNone(article["date"])

    def test_missing_source_name_defaults_to_empty(self):
        article = build_article(
            source={},
            title="Title",
            summary="",
            url="https://example.com/news/1",
            published=None,
        )
        self.assertEqual(article["source"], "")
        self.assertEqual(article["source_label"], "")


class ParseRssTests(unittest.TestCase):
    def test_valid_feed_returns_articles(self):
        content = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
        <item>
          <title>Headline One</title>
          <link>https://example.com/news/1</link>
          <description>Summary one</description>
        </item>
        </channel></rss>
        """
        articles = parse_rss(content, {"name": "Test"})
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "Headline One")

    def test_entry_missing_link_is_skipped(self):
        content = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
        <item>
          <title>No link here</title>
          <description>Summary</description>
        </item>
        </channel></rss>
        """
        articles = parse_rss(content, {"name": "Test"})
        self.assertEqual(articles, [])

    def test_empty_content_returns_no_articles(self):
        self.assertEqual(parse_rss("", {"name": "Test"}), [])

    def test_malformed_content_does_not_raise(self):
        # Not XML at all; feedparser should not crash, and we should get [].
        articles = parse_rss("this is not xml at all", {"name": "Test"})
        self.assertEqual(articles, [])


if __name__ == "__main__":
    unittest.main()
