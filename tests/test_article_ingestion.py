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
            # Repéré en audit réel le 2026-09-11 : "Take Action" (page
            # de campagne générique Amnesty) et deux pages-outils
            # OHCHR Special Procedures atteignaient le niveau B avec
            # un faux score de répression, faute d'être reconnues
            # comme des non-articles.
            (
                "https://www.amnesty.org/en/get-involved/take-action/",
                "Take Action",
            ),
            (
                "https://spcommreports.ohchr.org/Tmsearch/TMDocuments",
                "Communication search",
            ),
            (
                "http://spinternet.ohchr.org/_Layouts/SpecialProceduresInternet/"
                "ViewAllCountryMandates.aspx?Type=TM",
                "Thematic mandates",
            ),
            # Niveau C, même audit : pages de listing/agrégation et
            # contenu hors-sujet (sport) atteignant un faux score.
            (
                "https://uhrp.org/news_cat/uhrp-in-the-news/",
                "UHRP in the News",
            ),
            (
                "https://www.hronikatm.com/other-media/iz-drugih-smi/",
                "Из других источников",
            ),
            (
                "https://www.aljazeera.com/sports/2026/8/14/"
                "swiatek-defeats-rybakina-to-claim-canadian-open",
                "Swiatek defeats Rybakina to claim Canadian Open title",
            ),
            (
                "https://www.uscirf.gov/news-room/uscirf-spotlight",
                "USCIRF Spotlight Podcast",
            ),
        ]

        for url, title in cases:
            with self.subTest(url=url):
                self.assertFalse(looks_like_article_link(url, title))

    def test_rejects_url_with_repeated_path_prefix(self):
        # Régression réelle : FIDH sert des liens relatifs sans "/"
        # initial depuis une page-liste déjà profonde, ce qui produit
        # une URL cassée avec le préfixe de chemin dupliqué.
        self.assertFalse(
            looks_like_article_link(
                "https://www.fidh.org/en/region/europe-central-asia/"
                "en/region/europe-central-asia/azerbaijan/"
                "azerbaijan-serious-concerns",
                "Azerbaijan: Serious concerns over the ill-treatment",
            )
        )

    def test_accepts_url_without_repeated_prefix(self):
        self.assertTrue(
            looks_like_article_link(
                "https://www.fidh.org/en/region/europe-central-asia/"
                "azerbaijan/azerbaijan-serious-concerns",
                "Azerbaijan: Serious concerns over the ill-treatment",
            )
        )


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

    def test_reads_json_ld_date_published(self):
        # Régression réelle : Al Jazeera/HRF exposent leur date
        # uniquement via un bloc JSON-LD schema.org, sans balise
        # meta/time classique — l'article était enrichi (corps
        # récupéré, score correct) mais restait sans date affichée.
        soup = BeautifulSoup(
            '<html><head><script type="application/ld+json">'
            '{"@context": "https://schema.org", "@type": "NewsArticle", '
            '"datePublished": "2021-11-12T08:00:00+00:00"}'
            "</script></head><body></body></html>",
            "html.parser",
        )
        date = extract_published_date(soup)
        self.assertIsNotNone(date)
        self.assertEqual(date.year, 2021)
        self.assertEqual(date.month, 11)
        self.assertEqual(date.day, 12)

    def test_reads_json_ld_date_inside_graph(self):
        soup = BeautifulSoup(
            '<html><head><script type="application/ld+json">'
            '{"@context": "https://schema.org", "@graph": ['
            '{"@type": "WebPage"}, '
            '{"@type": "NewsArticle", "datePublished": "2026-05-15"}'
            "]}"
            "</script></head><body></body></html>",
            "html.parser",
        )
        date = extract_published_date(soup)
        self.assertIsNotNone(date)
        self.assertEqual(date.year, 2026)
        self.assertEqual(date.month, 5)

    def test_ignores_malformed_json_ld(self):
        soup = BeautifulSoup(
            '<html><head><script type="application/ld+json">'
            "not valid json"
            "</script></head><body>No date here</body></html>",
            "html.parser",
        )
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

    def test_strips_google_news_source_suffix(self):
        # Google News agrège hrw.org (contournement de son blocage
        # 403) mais ajoute " - <site>" à chaque titre.
        content = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
        <item>
          <title>Man Sentenced to Prison - Human Rights Watch</title>
          <link>https://news.google.com/rss/articles/abc123</link>
          <description>Summary</description>
        </item>
        </channel></rss>
        """
        articles = parse_rss(
            content,
            {"name": "Human Rights Watch"},
            feed_url="https://news.google.com/rss/search?q=site:hrw.org",
        )
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "Man Sentenced to Prison")

    def test_does_not_strip_suffix_for_non_google_feeds(self):
        # Un vrai titre se terminant par un tiret ne doit pas être
        # tronqué en dehors d'un flux Google News.
        content = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
        <item>
          <title>Report Covers 2020 - 2025</title>
          <link>https://example.com/news/1</link>
          <description>Summary</description>
        </item>
        </channel></rss>
        """
        articles = parse_rss(
            content,
            {"name": "Test"},
            feed_url="https://example.com/rss",
        )
        self.assertEqual(articles[0]["title"], "Report Covers 2020 - 2025")

    def test_discards_google_news_html_description(self):
        # Régression réelle : la <description> Google News n'est
        # jamais un vrai résumé, juste le titre ré-empaqueté en lien
        # HTML + le nom de la source
        # ('<a href="...">Titre</a> <font ...>Source</font>'), affiché
        # tel quel sur le site (visible dans le HTML et le CSV
        # exportés) au lieu d'un vrai résumé.
        content = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
        <item>
          <title>Kazakhstan Activist Arrested - Human Rights Watch</title>
          <link>https://news.google.com/rss/articles/abc123</link>
          <description>
            &lt;a href="https://news.google.com/rss/articles/abc123" target="_blank"&gt;Kazakhstan Activist Arrested&lt;/a&gt; &lt;font color="#6f6f6f"&gt;Human Rights Watch&lt;/font&gt;
          </description>
        </item>
        </channel></rss>
        """
        articles = parse_rss(
            content,
            {"name": "Human Rights Watch"},
            feed_url="https://news.google.com/rss/search?q=site:hrw.org",
        )
        self.assertEqual(articles[0]["summary"], "")

    def test_keeps_real_description_for_non_google_feeds(self):
        content = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
        <item>
          <title>Real article</title>
          <link>https://example.com/news/1</link>
          <description>A genuine summary of the article.</description>
        </item>
        </channel></rss>
        """
        articles = parse_rss(
            content,
            {"name": "Test"},
            feed_url="https://example.com/rss",
        )
        self.assertEqual(
            articles[0]["summary"], "A genuine summary of the article."
        )

    def test_rejects_navigation_pages_from_google_news(self):
        # Régression réelle : le flux Google News (site:hrw.org...)
        # indexe aussi de vieilles pages de navigation du site
        # ("Table of Contents Europe & Central Asia", "Countries"),
        # jamais filtrées car looks_like_article_link() n'était
        # jamais appliqué aux entrées RSS.
        content = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
        <item>
          <title>Table of Contents Europe &amp; Central Asia - Human Rights Watch</title>
          <link>https://news.google.com/rss/articles/abc1</link>
          <description>Summary</description>
        </item>
        <item>
          <title>Countries - Human Rights Watch</title>
          <link>https://news.google.com/rss/articles/abc2</link>
          <description>Summary</description>
        </item>
        <item>
          <title>Kazakhstan Jails Activists for Peaceful Protest - Human Rights Watch</title>
          <link>https://news.google.com/rss/articles/abc3</link>
          <description>Summary</description>
        </item>
        </channel></rss>
        """
        articles = parse_rss(
            content,
            {"name": "Human Rights Watch"},
            feed_url="https://news.google.com/rss/search?q=site:hrw.org",
        )
        titles = [a["title"] for a in articles]
        self.assertEqual(
            titles, ["Kazakhstan Jails Activists for Peaceful Protest"]
        )

    def test_google_news_redirect_url_does_not_trigger_rss_path_rejection(self):
        # Le lien de redirection Google (.../rss/articles/<hash>)
        # contient littéralement "/rss", un motif normalement exclu
        # (liens de découverte de flux) — il ne doit pas être jugé
        # sur son URL opaque, seulement sur son titre.
        content = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
        <item>
          <title>A perfectly legitimate headline here - Human Rights Watch</title>
          <link>https://news.google.com/rss/articles/xyz789</link>
          <description>Summary</description>
        </item>
        </channel></rss>
        """
        articles = parse_rss(
            content,
            {"name": "Human Rights Watch"},
            feed_url="https://news.google.com/rss/search?q=site:hrw.org",
        )
        self.assertEqual(len(articles), 1)


if __name__ == "__main__":
    unittest.main()
