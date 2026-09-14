import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from news_scanner import (
    CorpusCollapseError,
    merge_with_archive,
    check_corpus_not_collapsed,
    build_audit,
    build_csv_rows,
    build_title_vocabulary,
    canonical_article_key,
    collect_articles,
    compute_seen_keys,
    deduplicate,
    enrich_articles,
    final_sort_key,
    get_cached_body,
    load_seen_keys,
    score_first_pass,
    update_body_cache,
)
from html_template import render_audit_row
from scoring import classify_article


class CanonicalArticleKeyTests(unittest.TestCase):
    def test_uses_url_when_present(self):
        article = {"url": "https://Example.com/News/1/", "title": "Title"}
        self.assertEqual(canonical_article_key(article), "example.com/news/1")

    def test_falls_back_to_title_when_no_url(self):
        article = {"url": "", "title": "Some Title! With Punctuation."}
        self.assertEqual(
            canonical_article_key(article), "some title with punctuation"
        )

    def test_empty_article_returns_empty_key(self):
        self.assertEqual(canonical_article_key({}), "")

    def test_distinguishes_articles_by_query_string(self):
        article_a = {"url": "https://example.com/news?id=1"}
        article_b = {"url": "https://example.com/news?id=2"}
        self.assertNotEqual(
            canonical_article_key(article_a),
            canonical_article_key(article_b),
        )


class BuildTitleVocabularyTests(unittest.TestCase):
    def test_filters_out_french_stopwords(self):
        # Régression : les stopwords français ("les", "des", "une"...)
        # remontaient dans le nuage de mots car _load_stopwords()
        # ne chargeait que en/ru/fa, pas fr, alors que plusieurs
        # sources (RSF, FIDH...) publient en français.
        articles = [
            {"title": "Les autorités arrêtent une journaliste des droits humains"},
            {"title": "Une répression sévère contre les militants dans la région"},
        ]

        vocabulary = build_title_vocabulary(articles, limit=50)
        words = {entry["word"] for entry in vocabulary}

        for stopword in ("les", "des", "une", "la", "dans"):
            self.assertNotIn(stopword, words)


class DeduplicateTests(unittest.TestCase):
    def test_removes_duplicate_urls(self):
        articles = [
            {"url": "https://example.com/news/1", "title": "A"},
            {"url": "https://example.com/news/1", "title": "A duplicate"},
            {"url": "https://example.com/news/2", "title": "B"},
        ]
        result = deduplicate(articles)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "A")

    def test_skips_articles_without_key(self):
        articles = [{"url": "", "title": ""}]
        self.assertEqual(deduplicate(articles), [])

    def test_empty_list(self):
        self.assertEqual(deduplicate([]), [])


class BuildAuditTests(unittest.TestCase):
    def test_preserves_url_date_and_theme(self):
        # Régression : le tableau d'audit du site (render_audit_row)
        # affiche url/date/theme, mais build_audit() ne les copiait
        # pas dans les dicts qu'il construit — chaque ligne du tableau
        # avait donc un lien mort (href=""), aucune date et aucun
        # thème, pour la quasi-totalité des articles (les D, jamais
        # affichés ailleurs que dans ce tableau).
        from datetime import datetime, timezone

        date = datetime(2026, 3, 15, tzinfo=timezone.utc)
        articles = [
            {
                "title": "Some article",
                "source": "Test Source",
                "url": "https://example.com/article",
                "date": date,
                "theme": "Politique intérieure",
                "score": 14,
                "level": "D",
                "relevant": False,
                "signals": {},
            }
        ]

        audit = build_audit(articles)

        self.assertEqual(audit[0]["url"], "https://example.com/article")
        self.assertEqual(audit[0]["date"], date)
        self.assertEqual(audit[0]["theme"], "Politique intérieure")

    def test_preserves_categorisation_fields(self):
        # Régression du 2026-09-12 : même bug que ci-dessus, pour les
        # champs categorisation.py/regles_editoriales.py ajoutés
        # ensuite — build_audit() ne les copiait pas non plus, donc la
        # colonne "Catégorisation" du tableau d'audit était vide pour
        # les ~6750 articles du site (confirmé en HTML publié), alors
        # que les cartes articles (qui utilisent l'article original,
        # pas cette copie filtrée) l'affichaient correctement.
        articles = [
            {
                "title": "Some article",
                "source": "Test Source",
                "url": "https://example.com/article",
                "categorisation": {
                    "geo": ["kazakhstan"],
                    "acteur": ["defenseur"],
                    "traitement": ["detention"],
                    "type": "evenement_date",
                },
                "categorisation_pertinent": True,
                "categorisation_reason": "pertinent",
            }
        ]

        audit = build_audit(articles)

        self.assertEqual(
            audit[0]["categorisation"]["geo"], ["kazakhstan"]
        )
        self.assertTrue(audit[0]["categorisation_pertinent"])
        self.assertEqual(audit[0]["categorisation_reason"], "pertinent")

    def test_end_to_end_audit_row_never_empty_after_score_first_pass(self):
        # Test bout-en-bout (score_first_pass -> build_audit ->
        # render_audit_row) qui aurait directement attrapé la
        # régression ci-dessus : un test qui appelle render_audit_row()
        # sur l'article brut (contournant build_audit()) ne la
        # détecte pas, puisque les cartes articles (qui utilisent
        # l'article original) fonctionnaient bien — seul le chemin
        # complet via build_audit() révèle le problème.
        import re

        articles = [
            {
                "title": "Kazakhstan Jails Activist for Ten Years",
                "summary": "A court sentenced a human rights activist to prison.",
                "body": "",
                "source": "Human Rights Watch",
                "source_label": "HRW",
                "url": "https://www.hrw.org/news/example",
                "language": "en",
                "date": None,
            }
        ]

        score_first_pass(articles)
        audit = build_audit(articles)
        row_html = render_audit_row(audit[0])

        cell = re.search(
            r'<td class="audit-categorisation">(.*?)</td>', row_html, re.S
        )
        self.assertIsNotNone(cell)
        self.assertTrue(cell.group(1).strip())

    def test_maps_source_to_display_category(self):
        # La table d'audit du site regroupe les milliers de lignes de
        # niveau D par catégorie de source (voir PROFILE_GROUPS dans
        # sources.py) plutôt que de tout lister à plat.
        articles = [
            {"title": "A", "source": "Human Rights Watch"},
            {"title": "B", "source": "RAND Corporation"},
            {"title": "C", "source": "Unknown Source"},
        ]

        audit = build_audit(articles)

        self.assertEqual(audit[0]["category"], "Droits humains & presse")
        self.assertEqual(
            audit[1]["category"],
            "Sécurité & géopolitique (think tanks)",
        )
        self.assertEqual(audit[2]["category"], "Autres")


class FinalSortKeyTests(unittest.TestCase):
    """
    Décidé avec l'utilisateur le 2026-09-11 : le tri final groupe par
    niveau (A > B > C > D > E), puis trie par date décroissante à
    l'intérieur d'un même niveau — jamais par score brut, pour ne pas
    faire remonter un vieux rapport pertinent devant un article frais
    équivalent au sein de la même section.
    """

    def test_higher_level_always_outranks_lower_level_regardless_of_score(self):
        now = datetime(2026, 9, 11, tzinfo=timezone.utc)

        level_b_high_score = {
            "relevant": True, "level": "B", "score": 95,
            "date": now,
        }
        level_a_low_score = {
            "relevant": True, "level": "A", "score": 76,
            "date": now - timedelta(days=10),
        }

        self.assertGreater(
            final_sort_key(level_a_low_score),
            final_sort_key(level_b_high_score),
        )

    def test_within_same_level_more_recent_outranks_higher_score(self):
        now = datetime(2026, 9, 11, tzinfo=timezone.utc)

        old_high_score = {
            "relevant": True, "level": "A", "score": 99,
            "date": now - timedelta(days=90),
        }
        recent_lower_score = {
            "relevant": True, "level": "A", "score": 76,
            "date": now,
        }

        self.assertGreater(
            final_sort_key(recent_lower_score),
            final_sort_key(old_high_score),
        )


class CsvExportTests(unittest.TestCase):
    def test_rows_include_article_data_scores_and_keywords(self):
        rows = build_csv_rows(
            [
                {
                    "date": None,
                    "source": "Example",
                    "title": "A title",
                    "url": "https://example.com/article",
                    "summary": "Summary",
                    "score": 82,
                    "level": "A",
                    "priority": "high",
                    "relevant": True,
                    "theme": "Rights",
                    "reasons": ["human rights"],
                    "signals": {
                        "human_rights": ["freedom"],
                        "repression": ["arrested", "freedom"],
                        "geography_score": 12,
                    },
                }
            ]
        )

        self.assertEqual(rows[0]["title"], "A title")
        self.assertEqual(rows[0]["score"], 82)
        self.assertEqual(rows[0]["keywords"], "freedom; arrested")
        self.assertEqual(rows[0]["geography_score"], 12)


class EnrichArticlesTests(unittest.TestCase):
    @patch("news_scanner.extract_body")
    def test_priority_profiles_get_guaranteed_enrichment_slots(
        self, mock_extract
    ):
        # Régression : un article régional précis (ex : Amnesty sur une
        # condamnation nommément ciblée) peut avoir un score titre-seul
        # trop bas pour entrer dans le top ENRICH_LIMIT une fois noyé
        # sous le volume d'une source généraliste — il ne recevrait
        # alors jamais son corps complet et resterait plafonné pour
        # toujours. Les profils human_rights/press_freedom/investigative
        # doivent avoir des créneaux garantis, indépendants du score.
        mock_extract.return_value = ("full body text", None)

        sources = [
            {"name": "Generic Source", "profile": "regional_media"},
            {"name": "Amnesty International", "profile": "human_rights"},
        ]

        articles = [
            {"source": "Generic Source", "score": 90, "url": "https://example.com/1", "title": "A" * 10},
            {"source": "Generic Source", "score": 89, "url": "https://example.com/2", "title": "B" * 10},
            {"source": "Generic Source", "score": 88, "url": "https://example.com/3", "title": "C" * 10},
            {"source": "Amnesty International", "score": 15, "url": "https://example.com/4", "title": "D" * 10},
        ]

        with patch("news_scanner.SOURCES", new=sources), patch(
            "news_scanner.ENRICH_LIMIT", 2
        ), patch("news_scanner.ENRICH_PER_SOURCE_LIMIT", 10):
            enrich_articles(articles)

        self.assertEqual(articles[3]["body"], "full body text")

    @patch("news_scanner.extract_body")
    def test_general_score_ranking_still_applies_beyond_priority_profiles(
        self, mock_extract
    ):
        mock_extract.return_value = ("full body text", None)

        sources = [
            {"name": "Generic Source", "profile": "regional_media"},
        ]

        articles = [
            {"source": "Generic Source", "score": 90, "url": "https://example.com/1", "title": "A" * 10},
            {"source": "Generic Source", "score": 10, "url": "https://example.com/2", "title": "B" * 10},
        ]

        with patch("news_scanner.SOURCES", new=sources), patch(
            "news_scanner.ENRICH_LIMIT", 1
        ), patch("news_scanner.ENRICH_PER_SOURCE_LIMIT", 10):
            enrich_articles(articles)

        self.assertEqual(articles[0]["body"], "full body text")
        self.assertNotIn("body", articles[1])

    @patch("news_scanner.extract_body")
    def test_high_volume_priority_source_does_not_crowd_out_sibling_sources(
        self, mock_extract
    ):
        # Régression réelle : le contournement Google News de HRW
        # déverse des centaines d'articles/run. Si les sources
        # prioritaires partageaient un même pool classé par score,
        # HRW pouvait à elle seule remplir ce pool et laisser Al
        # Jazeera/HRF (même groupe de profil, bien plus modestes en
        # volume) sans aucun créneau — donc sans date affichée.
        mock_extract.return_value = ("full body text", None)

        sources = [
            {"name": "Human Rights Watch", "profile": "human_rights"},
            {"name": "Al Jazeera — Turkmenistan", "profile": "international_independent"},
        ]

        articles = [
            {
                "source": "Human Rights Watch",
                "score": 20,
                "url": f"https://example.com/hrw/{i}",
                "title": f"HRW headline number {i}",
            }
            for i in range(50)
        ] + [
            {
                "source": "Al Jazeera — Turkmenistan",
                "score": 15,
                "url": "https://example.com/aj/1",
                "title": "Turkmenistan dissidents fear crackdown in exile",
            }
        ]

        with patch("news_scanner.SOURCES", new=sources), patch(
            "news_scanner.ENRICH_LIMIT", 0
        ), patch("news_scanner.ENRICH_PER_SOURCE_LIMIT", 15):
            enrich_articles(articles)

        self.assertEqual(articles[-1]["body"], "full body text")

    @patch("news_scanner.extract_body")
    def test_skips_network_fetch_when_body_already_cached(
        self, mock_extract
    ):
        # Décidé avec l'utilisateur le 2026-09-11 : un article déjà
        # enrichi lors d'un run récent (il reste souvent visible dans
        # un flux plusieurs runs de suite) ne doit pas être retéléchargé
        # — son corps est réutilisé depuis memory["body_cache"].
        sources = [{"name": "Generic Source", "profile": "regional_media"}]
        articles = [
            {
                "source": "Generic Source",
                "score": 90,
                "url": "https://example.com/1",
                "title": "A" * 10,
                "date": None,
            }
        ]
        memory = {
            "body_cache": {
                "https://example.com/1": {
                    "body": "cached body text",
                    "date": None,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            }
        }

        with patch("news_scanner.SOURCES", new=sources), patch(
            "news_scanner.ENRICH_LIMIT", 5
        ), patch("news_scanner.ENRICH_PER_SOURCE_LIMIT", 15):
            enrich_articles(articles, memory=memory)

        self.assertEqual(articles[0]["body"], "cached body text")
        mock_extract.assert_not_called()

    @patch("news_scanner.extract_body")
    def test_refetches_when_cached_body_is_stale(self, mock_extract):
        mock_extract.return_value = ("fresh body text", None)

        sources = [{"name": "Generic Source", "profile": "regional_media"}]
        articles = [
            {
                "source": "Generic Source",
                "score": 90,
                "url": "https://example.com/1",
                "title": "A" * 10,
            }
        ]
        stale_timestamp = (
            datetime.now(timezone.utc) - timedelta(hours=72)
        ).isoformat()
        memory = {
            "body_cache": {
                "https://example.com/1": {
                    "body": "old cached body text",
                    "date": None,
                    "fetched_at": stale_timestamp,
                }
            }
        }

        with patch("news_scanner.SOURCES", new=sources), patch(
            "news_scanner.ENRICH_LIMIT", 5
        ), patch("news_scanner.ENRICH_PER_SOURCE_LIMIT", 15):
            enrich_articles(articles, memory=memory)

        self.assertEqual(articles[0]["body"], "fresh body text")
        mock_extract.assert_called_once()

    @patch("news_scanner.extract_body")
    def test_force_refresh_bypasses_body_cache(self, mock_extract):
        mock_extract.return_value = ("fresh body text", None)

        sources = [{"name": "Generic Source", "profile": "regional_media"}]
        articles = [
            {
                "source": "Generic Source",
                "score": 90,
                "url": "https://example.com/1",
                "title": "A" * 10,
            }
        ]
        memory = {
            "body_cache": {
                "https://example.com/1": {
                    "body": "cached body text",
                    "date": None,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            }
        }

        with patch("news_scanner.SOURCES", new=sources), patch(
            "news_scanner.ENRICH_LIMIT", 5
        ), patch("news_scanner.ENRICH_PER_SOURCE_LIMIT", 15):
            enrich_articles(articles, force_refresh=True, memory=memory)

        self.assertEqual(articles[0]["body"], "fresh body text")
        mock_extract.assert_called_once()

    @patch("news_scanner.extract_body")
    def test_newly_fetched_bodies_are_written_back_to_memory(
        self, mock_extract
    ):
        mock_extract.return_value = ("fresh body text", None)

        sources = [{"name": "Generic Source", "profile": "regional_media"}]
        articles = [
            {
                "source": "Generic Source",
                "score": 90,
                "url": "https://example.com/1",
                "title": "A" * 10,
            }
        ]
        memory: dict = {}

        with patch("news_scanner.SOURCES", new=sources), patch(
            "news_scanner.ENRICH_LIMIT", 5
        ), patch("news_scanner.ENRICH_PER_SOURCE_LIMIT", 15):
            enrich_articles(articles, memory=memory)

        cached = memory["body_cache"]["https://example.com/1"]
        self.assertEqual(cached["body"], "fresh body text")


class BodyCacheTests(unittest.TestCase):
    """
    Cache du corps déjà extrait par URL, dans memory.json — voir
    enrich_articles(). Contrairement au cache HTTP de http_utils.py
    (jamais persisté entre les runs GitHub Actions, gitignored), celui-
    ci vit dans memory.json, recommité après chaque run.
    """

    def test_get_cached_body_returns_none_when_missing(self):
        self.assertIsNone(get_cached_body({}, "https://example.com/x", time.time()))

    def test_get_cached_body_returns_fresh_entry(self):
        cache = {
            "https://example.com/x": {
                "body": "some body",
                "date": None,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        }

        result = get_cached_body(cache, "https://example.com/x", time.time())

        self.assertEqual(result, ("some body", None))

    def test_get_cached_body_returns_none_when_expired(self):
        stale_timestamp = (
            datetime.now(timezone.utc) - timedelta(hours=72)
        ).isoformat()
        cache = {
            "https://example.com/x": {
                "body": "some body",
                "date": None,
                "fetched_at": stale_timestamp,
            }
        }

        result = get_cached_body(cache, "https://example.com/x", time.time())

        self.assertIsNone(result)

    def test_update_body_cache_truncates_and_bounds_entries(self):
        memory: dict = {}

        with patch("news_scanner.BODY_CACHE_MAX_CHARS", 10), patch(
            "news_scanner.BODY_CACHE_MAX_ENTRIES", 1
        ):
            update_body_cache(
                memory,
                {"https://example.com/1": ("a" * 100, None)},
            )
            update_body_cache(
                memory,
                {"https://example.com/2": ("b" * 100, None)},
            )

        self.assertEqual(len(memory["body_cache"]), 1)
        cached = next(iter(memory["body_cache"].values()))
        self.assertEqual(len(cached["body"]), 10)


class MemorySeenKeysTests(unittest.TestCase):
    def test_load_seen_keys_filters_invalid_entries(self):
        memory = {"seen_article_keys": ["a", "", None, 42, "b"]}
        self.assertEqual(load_seen_keys(memory), {"a", "b"})

    def test_compute_seen_keys_normal_run_uses_memory(self):
        memory = {"seen_article_keys": ["a", "b"]}
        self.assertEqual(
            compute_seen_keys(memory, force_refresh=False), {"a", "b"}
        )

    def test_compute_seen_keys_force_refresh_ignores_memory(self):
        # Régression : --scan (force_refresh) doit repartir de zéro,
        # sinon un "re-scan forcé" continue de filtrer silencieusement
        # tout ce qui a déjà été traité lors d'un run précédent.
        memory = {"seen_article_keys": ["a", "b"]}
        self.assertEqual(
            compute_seen_keys(memory, force_refresh=True), set()
        )


class CollectArticlesTests(unittest.TestCase):
    @patch("news_scanner.diagnose_source_content")
    @patch("news_scanner.parse_rss")
    @patch("news_scanner.fetch_url")
    def test_skips_previously_seen_keys_early(
        self,
        mock_fetch,
        mock_parse,
        mock_diag,
    ):
        with patch(
            "news_scanner.SOURCES",
            new=[
                {"name": "S1", "url": "https://example.com/rss", "type": "rss"},
            ],
        ):
            mock_fetch.return_value = "<rss></rss>"
            mock_parse.return_value = [
                {"url": "https://example.com/keep", "title": "Keep"},
                {"url": "https://example.com/old", "title": "Old"},
            ]

            articles, ok, total, skipped = collect_articles(
                seen_keys={"example.com/old"}
            )

        self.assertEqual(ok, 1)
        self.assertEqual(total, 1)
        self.assertEqual(skipped, 1)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["url"], "https://example.com/keep")

    @patch("news_scanner.diagnose_source_content")
    @patch("news_scanner.parse_rss")
    @patch("news_scanner.fetch_url")
    def test_aggregates_all_configured_feeds(
        self,
        mock_fetch,
        mock_parse,
        mock_diag,
    ):
        with patch(
            "news_scanner.SOURCES",
            new=[
                {
                    "name": "Multi",
                    "url": "https://example.com/",
                    "type": "rss",
                    "feeds": [
                        "https://example.com/feed1",
                        "https://example.com/feed2",
                    ],
                },
            ],
        ):
            mock_fetch.return_value = "<rss></rss>"
            mock_parse.side_effect = [
                [{"url": "https://example.com/a", "title": "A"}],
                [{"url": "https://example.com/b", "title": "B"}],
            ]

            articles, ok, total, skipped = collect_articles()

        self.assertEqual(ok, 1)
        self.assertEqual(mock_fetch.call_count, 2)
        fetched_urls = {call.args[0] for call in mock_fetch.call_args_list}
        self.assertEqual(
            fetched_urls,
            {"https://example.com/feed1", "https://example.com/feed2"},
        )
        self.assertEqual(len(articles), 2)

    @patch("news_scanner.diagnose_source_content")
    @patch("news_scanner.extract_links_from_html")
    @patch("news_scanner.fetch_url")
    def test_falls_back_when_primary_url_fails(
        self,
        mock_fetch,
        mock_extract,
        mock_diag,
    ):
        with patch(
            "news_scanner.SOURCES",
            new=[
                {
                    "name": "HTML Source",
                    "url": "https://example.com/down",
                    "type": "html",
                    "fallbacks": ["https://example.com/mirror"],
                },
            ],
        ):
            mock_fetch.side_effect = [
                RuntimeError("HTTP error: 404"),
                "<html></html>",
            ]
            mock_extract.return_value = [
                {"url": "https://example.com/mirror/a", "title": "A"}
            ]

            articles, ok, total, skipped = collect_articles()

        self.assertEqual(ok, 1)
        self.assertEqual(mock_fetch.call_count, 2)
        self.assertEqual(len(articles), 1)

    @patch("news_scanner.diagnose_source_content")
    @patch("news_scanner.parse_rss")
    @patch("news_scanner.fetch_url")
    def test_skips_fetch_for_recently_scanned_source(
        self,
        mock_fetch,
        mock_parse,
        mock_diag,
    ):
        from datetime import datetime, timezone

        memory = {
            "sources": {
                "S1": {
                    "last_scanned_at": datetime.now(timezone.utc).isoformat(),
                    "ok": True,
                    "articles": [
                        {
                            "source": "S1",
                            "source_label": "S1",
                            "title": "Cached",
                            "summary": "",
                            "url": "https://example.com/cached",
                            "date": None,
                        }
                    ],
                }
            }
        }

        with patch(
            "news_scanner.SOURCES",
            new=[{"name": "S1", "url": "https://example.com/rss", "type": "rss"}],
        ):
            articles, ok, total, skipped = collect_articles(memory=memory)

        mock_fetch.assert_not_called()
        mock_parse.assert_not_called()
        self.assertEqual(ok, 1)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["url"], "https://example.com/cached")

    @patch("news_scanner.diagnose_source_content")
    @patch("news_scanner.parse_rss")
    @patch("news_scanner.fetch_url")
    def test_rescans_source_after_min_interval_elapsed(
        self,
        mock_fetch,
        mock_parse,
        mock_diag,
    ):
        from datetime import datetime, timedelta, timezone

        stale = datetime.now(timezone.utc) - timedelta(hours=3)
        memory = {
            "sources": {
                "S1": {
                    "last_scanned_at": stale.isoformat(),
                    "ok": True,
                    "articles": [],
                }
            }
        }

        with patch(
            "news_scanner.SOURCES",
            new=[{"name": "S1", "url": "https://example.com/rss", "type": "rss"}],
        ):
            mock_fetch.return_value = "<rss></rss>"
            mock_parse.return_value = [
                {"url": "https://example.com/fresh", "title": "Fresh"}
            ]

            articles, ok, total, skipped = collect_articles(memory=memory)

        mock_fetch.assert_called_once()
        self.assertEqual(articles[0]["url"], "https://example.com/fresh")

    @patch("news_scanner.diagnose_source_content")
    @patch("news_scanner.parse_rss")
    @patch("news_scanner.fetch_url")
    def test_cached_articles_are_not_dropped_as_previously_seen(
        self,
        mock_fetch,
        mock_parse,
        mock_diag,
    ):
        # Régression : un article servi depuis le cache par-source a, par
        # construction, déjà été enregistré dans seen_article_keys lors du
        # scan qui a rempli ce cache. S'il était filtré comme "déjà vu",
        # une source dans sa fenêtre de fraîcheur ne contribuerait jamais
        # rien et le site publié se retrouverait vide.
        from datetime import datetime, timezone

        memory = {
            "sources": {
                "S1": {
                    "last_scanned_at": datetime.now(timezone.utc).isoformat(),
                    "ok": True,
                    "articles": [
                        {
                            "source": "S1",
                            "source_label": "S1",
                            "title": "Cached",
                            "summary": "",
                            "url": "https://example.com/cached",
                            "date": None,
                        }
                    ],
                }
            }
        }

        with patch(
            "news_scanner.SOURCES",
            new=[{"name": "S1", "url": "https://example.com/rss", "type": "rss"}],
        ):
            articles, ok, total, skipped = collect_articles(
                seen_keys={"example.com/cached"},
                memory=memory,
            )

        mock_fetch.assert_not_called()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["url"], "https://example.com/cached")
        self.assertEqual(skipped, 0)


if __name__ == "__main__":
    unittest.main()


class CorpusCollapseGuardTests(unittest.TestCase):
    """
    Le site est intégralement régénéré à chaque run : un run qui ne
    ramène qu'une fraction des articles écrase silencieusement la
    version complète. Arrivé le 2026-09-13 (2086 publiés au lieu de
    6706, run vert).
    """

    def test_passes_when_corpus_is_stable(self):
        check_corpus_not_collapsed(6700, {"last_corpus_size": 6706})

    def test_passes_when_corpus_grows(self):
        check_corpus_not_collapsed(9000, {"last_corpus_size": 6706})

    def test_passes_on_first_ever_run(self):
        check_corpus_not_collapsed(120, {})

    def test_raises_on_the_real_2026_09_13_collapse(self):
        with self.assertRaises(CorpusCollapseError) as caught:
            check_corpus_not_collapsed(2086, {"last_corpus_size": 6706})

        message = str(caught.exception)
        self.assertIn("2086", message)
        self.assertIn("6706", message)

    def test_tolerates_a_moderate_drop(self):
        # Une source majeure en panne ne doit pas bloquer la publication.
        check_corpus_not_collapsed(4000, {"last_corpus_size": 6706})

    def test_ignores_corrupted_reference(self):
        for bogus in (None, 0, -5, "6706"):
            check_corpus_not_collapsed(10, {"last_corpus_size": bogus})


class MergeWithArchiveTests(unittest.TestCase):
    """
    Le corpus publié devient l'historique complet, pas seulement ce que
    les sources affichent aujourd'hui.
    """

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        base = Path(self.dir.name)
        self.patchers = [
            patch("archive.ARCHIVE_FILE", base / "archive.jsonl"),
            patch("archive.ARCHIVE_STATE_FILE", base / "state.json"),
        ]
        for p in self.patchers:
            p.start()

    def tearDown(self):
        for p in self.patchers:
            p.stop()
        self.dir.cleanup()

    def _article(self, url, title="Kazakhstan jails activist"):
        return {
            "url": url,
            "title": title,
            "summary": "Un tribunal d'Almaty a condamné un activiste.",
            "source": "Human Rights Watch",
            "source_label": "HRW",
            "language": "en",
            "date": None,
            "body": "",
        }

    def test_first_run_publishes_exactly_what_was_scanned(self):
        articles = [self._article("https://a.org/1"), self._article("https://a.org/2")]
        for a in articles:
            classify_article(a)

        published = merge_with_archive(articles)
        self.assertEqual(len(published), 2)

    def test_article_gone_from_its_source_stays_published(self):
        # Le cœur du sujet : avant, il disparaissait du site.
        first = [self._article("https://a.org/1"), self._article("https://a.org/2")]
        for a in first:
            classify_article(a)
        merge_with_archive(first)

        second = [self._article("https://a.org/1")]
        for a in second:
            classify_article(a)
        published = merge_with_archive(second)

        urls = {a["url"] for a in published}
        self.assertEqual(urls, {"https://a.org/1", "https://a.org/2"})

    def test_archived_articles_are_rescored_with_current_rules(self):
        first = [self._article("https://a.org/1")]
        for a in first:
            classify_article(a)
        merge_with_archive(first)

        published = merge_with_archive([])
        self.assertEqual(len(published), 1)
        # Rescoré : il ressort avec un score, pas avec un champ manquant.
        self.assertIn("score", published[0])
        self.assertIn("categorisation", published[0])

    def test_freshly_scanned_articles_keep_their_enriched_body(self):
        # L'archive ne garde le corps que des niveaux A-D : rescorer un
        # article enrichi aujourd'hui lui ferait perdre sa profondeur.
        fresh = self._article("https://a.org/1")
        fresh["body"] = "Un corps téléchargé aujourd'hui. " * 40
        classify_article(fresh)

        published = merge_with_archive([fresh])
        self.assertEqual(len(published), 1)
        self.assertIn("téléchargé aujourd'hui", published[0]["body"])

    def test_no_duplicates_when_the_same_article_is_rescanned(self):
        articles = [self._article("https://a.org/1")]
        for a in articles:
            classify_article(a)

        merge_with_archive(list(articles))
        again = [self._article("https://a.org/1")]
        for a in again:
            classify_article(a)
        published = merge_with_archive(again)

        self.assertEqual(len(published), 1)

    def test_published_articles_carry_the_last_scan_date(self):
        articles = [self._article("https://a.org/1")]
        for a in articles:
            classify_article(a)
        published = merge_with_archive(articles)

        self.assertTrue(published[0]["dernier_scan"])
        self.assertTrue(published[0]["derniere_vue"])


class EnrichmentTargetsNewGroundTests(unittest.TestCase):
    """
    Le budget d'enrichissement doit aller aux articles SANS corps.

    Sans ce filtre, la sélection par score reconduisait les mêmes têtes
    de classement d'un run à l'autre : 167 articles sur 7795 avaient un
    corps, et le reste n'était jamais couvert.
    """

    def _articles(self):
        return [
            {
                "source": "Generic Source", "score": 90,
                "url": "https://example.com/deja", "title": "A" * 10,
            },
            {
                "source": "Generic Source", "score": 10,
                "url": "https://example.com/neuf", "title": "B" * 10,
            },
        ]

    @patch("news_scanner.extract_body")
    def test_skips_articles_whose_body_is_already_archived(self, mock_extract):
        mock_extract.return_value = ("full body text", None)

        articles = self._articles()
        deja = {canonical_article_key(articles[0])}

        with patch("news_scanner.SOURCES", new=[
            {"name": "Generic Source", "profile": "regional_media"},
        ]), patch("news_scanner.ENRICH_LIMIT", 1), patch(
            "news_scanner.ENRICH_PER_SOURCE_LIMIT", 0
        ):
            enrich_articles(articles, deja_avec_corps=deja)

        # Le mieux classé est écarté : son corps est déjà archivé.
        self.assertNotIn("body", articles[0])
        # Le budget est allé au suivant, qui n'en avait pas.
        self.assertEqual(articles[1]["body"], "full body text")

    @patch("news_scanner.extract_body")
    def test_without_the_set_the_ranking_is_unchanged(self, mock_extract):
        mock_extract.return_value = ("full body text", None)

        articles = self._articles()

        with patch("news_scanner.SOURCES", new=[
            {"name": "Generic Source", "profile": "regional_media"},
        ]), patch("news_scanner.ENRICH_LIMIT", 1), patch(
            "news_scanner.ENRICH_PER_SOURCE_LIMIT", 0
        ):
            enrich_articles(articles)

        self.assertEqual(articles[0]["body"], "full body text")
        self.assertNotIn("body", articles[1])
