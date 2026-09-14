import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categorisation import categoriser
from regles_editoriales import est_pertinent


class CategoriserOutputShapeTests(unittest.TestCase):
    """categoriser() ne doit jamais juger de la pertinence ni muter l'article."""

    def _article(self, **overrides):
        article = {
            "title": "Kazakhstan Jails Activist for Ten Years Over Peaceful Protest",
            "summary": "A court in Almaty sentenced a human rights activist.",
            "body": "The activist was detained last month.",
            "source": "Human Rights Watch",
            "url": "https://www.hrw.org/news/2026/09/12/kazakhstan-activist-sentenced",
            "language": "en",
            "date": None,
        }
        article.update(overrides)
        return article

    def test_no_relevance_fields_in_output(self):
        result = categoriser(self._article())
        for forbidden in ("score", "level", "relevant", "retenu", "priority"):
            self.assertNotIn(forbidden, result)

    def test_does_not_mutate_input_article(self):
        article = self._article()
        original = dict(article)
        categoriser(article)
        self.assertEqual(article, original)

    def test_expected_top_level_keys(self):
        result = categoriser(self._article())
        self.assertEqual(
            set(result.keys()),
            {
                "geo", "geo_role", "acteur", "traitement",
                "relation_acteur_traitement", "type", "age_jours",
                "source_specialisee", "preuves",
            },
        )


class RussianStemTraitementTests(unittest.TestCase):
    """
    Régression du 2026-09-12 : plusieurs des listes de traitement
    (REPRESSION_TERMS notamment, réutilisée telle quelle pour
    "pression_administrative") contiennent des racines russes
    délibérément incomplètes ("пытк", "давлен", "репресс"...), que
    find_terms() ne peut jamais matcher (il exige une limite de mot
    juste après le terme). Cas réel : un article HRW russe
    ("Киргизия: пытки и произвольные аресты нагнетают напряженность")
    ressortait traitement=aucun malgré "пытки"/"аресты" dans le titre.
    """

    def test_torture_stem_detected_in_inflected_russian_form(self):
        article = {
            "title": "Пытки заключенных продолжаются в тюрьмах региона",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/news/1",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertIn("torture_mauvais_traitement", cat["traitement"])

    def test_arbitrary_arrests_plural_detected_as_detention(self):
        # "аресты" (pluriel) ne matche pas "арест" (singulier) via
        # find_terms — corrigé via _TRAITEMENT_STEM_PATTERNS.
        article = {
            "title": "Власти продолжают произвольные аресты активистов",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/news/2",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertIn("detention", cat["traitement"])

    def test_administrative_pressure_stem_detected_in_russian(self):
        # REPRESSION_TERMS (réutilisée en entier pour
        # "pression_administrative") est presque uniquement composée
        # de racines russes incomplètes pour sa partie russe — ce test
        # confirme qu'au moins une forme réelle ("давление") est
        # désormais détectée.
        article = {
            "title": "Власти усилили давление на оппозицию",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/news/3",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertIn("pression_administrative", cat["traitement"])

    def test_real_reported_article_no_longer_shows_aucun(self):
        # L'article exact signalé par l'utilisateur le 2026-09-12.
        article = {
            "title": (
                "Киргизия: пытки и произвольные аресты нагнетают "
                "напряженность"
            ),
            "summary": "",
            "body": "",
            "source": "Human Rights Watch",
            "url": "https://www.hrw.org/ru/news/2010/07/14/kyrgyzstan-example",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertNotEqual(cat["traitement"], ["aucun"])
        self.assertIn("kirghizistan", cat["geo"])

    def test_condamnation_stem_covers_participle_not_just_enumerated_forms(self):
        # "заключен" (racine) doit couvrir "заключенный"/"заключенным",
        # pas seulement les formes explicitement énumérées.
        article = {
            "title": "Правозащитник объявлен заключенным по политическому делу",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/news/4",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertIn("condamnation", cat["traitement"])


class GeoRegistryConsistencyTests(unittest.TestCase):
    def test_every_geo_term_maps_to_a_declared_country(self):
        # La table couvre désormais tous les pays du monde (générés
        # dans pays_monde.py), donc l'énumération en dur ne tient plus.
        # Le garde-fou reste le même : aucune valeur ne doit sortir de
        # nulle part — soit elle est curée à la main, soit elle vient
        # de la table générée.
        from categorisation import _GEO_TERM_COUNTRY
        from pays_monde import PAYS_MONDE_LIBELLES

        cures = {
            "kazakhstan", "ouzbekistan", "kirghizistan", "tadjikistan",
            "turkmenistan", "azerbaidjan", "armenie", "georgie",
            "caucase_nord", "xinjiang", "iran", "afghanistan", "russie",
            "ukraine", "chine", "bielorussie", "turquie", "moldavie",
            "asie_centrale", "caucase", "ossetie", "autre",
        }
        inconnues = set(_GEO_TERM_COUNTRY.values()) - cures - set(PAYS_MONDE_LIBELLES)
        self.assertEqual(inconnues, set())

    def test_modern_kyrgyz_adjective_maps_to_kirghizistan(self):
        # Régression du 2026-09-12 : "кыргыз" (adjectif moderne)
        # ajouté aux côtés de "кыргызстан"/"киргиз".
        article = {
            "title": "Кыргызские власти прокомментировали ситуацию",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/news/5",
            "language": "ru",
            "date": None,
        }
        cat = categoriser(article)
        self.assertIn("kirghizistan", cat["geo"])


class EstPertinentPermissiveDefaultTests(unittest.TestCase):
    def test_permissive_when_no_rule_configured(self):
        cat = categoriser({
            "title": "Random article about nothing in particular",
            "summary": "",
            "body": "",
            "source": "Test",
            "url": "https://example.com/x",
            "language": "en",
            "date": None,
        })
        pertinent, reason = est_pertinent(cat)
        self.assertTrue(pertinent)
        self.assertEqual(reason, "pertinent")


if __name__ == "__main__":
    unittest.main()


class PortedIntelligenceTests(unittest.TestCase):
    """
    2026-09-13 : categorisation.py réimplémentait une détection plus
    faible que scoring.py au lieu de partager la sienne. Ces tests
    verrouillent ce qui a été porté via matching.py.
    """

    def _article(self, title, language="", body="", summary=""):
        return {
            "title": title,
            "summary": summary,
            "body": body,
            "source": "Test",
            "url": "https://example.com/news/1",
            "language": language,
            "date": None,
        }

    def test_farsi_journalist_repression_pattern_detects_actor(self):
        # Les listes d'acteurs sont quasi muettes en persan ; les motifs
        # "acteur + répression" de keywords.py, que scoring.py exploite
        # depuis toujours, sont désormais lus ici aussi.
        cat = categoriser(
            self._article("خبرنگار بازداشت شد در تهران", language="fa")
        )
        self.assertIn("journaliste", cat["acteur"])

    def test_farsi_pattern_establishes_actor_treatment_relation(self):
        # Le motif exige acteur et répression à moins de 100 caractères
        # l'un de l'autre : la relation est établie par construction.
        cat = categoriser(
            self._article("فعال حقوق بشر بازداشت شد", language="fa")
        )
        self.assertTrue(cat["relation_acteur_traitement"])
        self.assertTrue(
            cat["preuves"]["relation_acteur_traitement"]["via_motif_farsi"]
        )

    def test_farsi_patterns_not_run_on_non_farsi_articles(self):
        # Les vérifications propres à une langue coûtent cher et n'ont
        # aucun sens ailleurs : elles restent inertes hors persan.
        cat = categoriser(
            self._article("خبرنگار بازداشت شد در تهران", language="ru")
        )
        self.assertNotIn(
            "(motif farsi acteur+répression)",
            cat["preuves"]["acteur"].get("journaliste", []),
        )

    def test_stem_evidence_reports_the_actual_word_found(self):
        # Auditer une catégorisation surprenante suppose de savoir QUEL
        # mot a matché, pas seulement qu'une racine a matché.
        cat = categoriser(
            self._article("Произвольные аресты продолжаются", language="ru")
        )
        self.assertIn("detention", cat["traitement"])
        self.assertIn("аресты", cat["preuves"]["traitement"]["detention"])

    def test_untyped_russian_repression_is_flagged_for_audit(self):
        # Une répression décrite en russe qu'aucun type ne capture est
        # un trou de vocabulaire : il doit être visible, pas silencieux.
        cat = categoriser(
            self._article("Против него выдвинуты новые обвинения", language="ru")
        )
        self.assertEqual(cat["traitement"], ["aucun"])
        self.assertIn("_non_typé", cat["preuves"]["traitement"])

    def test_relation_evidence_uses_word_boundaries_not_substrings(self):
        # L'ancienne version testait "terme in texte" : elle listait des
        # preuves que la détection elle-même n'aurait jamais retenues.
        cat = categoriser(
            self._article(
                "Journalist arrested after covering the protest in Almaty",
            )
        )
        if cat["relation_acteur_traitement"]:
            preuves = cat["preuves"]["relation_acteur_traitement"]
            for terme in preuves["traitement_termes"]:
                self.assertNotIn(
                    terme,
                    ("arrest",),
                    "un terme sous-chaîne ne doit pas apparaître en preuve",
                )


class TypeArticleTests(unittest.TestCase):
    """
    Le champ "type" a été corrigé le 2026-09-14 après un audit sur les
    7795 articles publiés : il ne portait aucune information. 100% des
    "navigation" étaient des URL Google News, et 100% des URL Google
    News étaient "navigation" — le champ recopiait le nom d'hôte.
    """

    GOOGLE_NEWS_URL = (
        "https://news.google.com/rss/articles/CBMikwFBVV95cUxNSzNqODlVV2Zw"
    )

    def _article(self, **overrides):
        article = {
            "title": "Kazakh Journalist Detained After Covering Protest",
            "summary": "",
            "body": "",
            "source": "RFE/RL",
            "url": "https://www.rferl.org/a/kazakh-journalist/123.html",
            "language": "en",
            "date": None,
        }
        article.update(overrides)
        return article

    def test_google_news_url_is_not_navigation(self):
        # Son chemin contient littéralement "/rss", ce qui faisait
        # échouer looks_like_article_link() alors que ces liens
        # viennent de flux d'ARTICLES.
        cat = categoriser(self._article(url=self.GOOGLE_NEWS_URL))
        self.assertNotEqual(cat["type"], "navigation")

    def test_google_news_url_with_date_is_a_dated_event(self):
        cat = categoriser(
            self._article(
                url=self.GOOGLE_NEWS_URL,
                date="2026-09-06T11:34:14+00:00",
            )
        )
        self.assertEqual(cat["type"], "evenement_date")

    def test_unknown_falls_back_to_indetermine_not_institutional(self):
        # "page_institutionnelle" affirmait un fait ("c'est une page
        # institutionnelle") à partir d'une absence d'information
        # (ni date, ni corps). 64,5% du corpus était concerné.
        cat = categoriser(self._article(date=None, body=""))
        self.assertEqual(cat["type"], "indetermine")
        self.assertIn("sans date", cat["preuves"]["type"])

    def test_genuine_navigation_link_still_rejected(self):
        cat = categoriser(
            self._article(
                url="https://example.org/category/news/",
                title="Countries and regions",
            )
        )
        self.assertEqual(cat["type"], "navigation")


class VocabulaireEnrichiTests(unittest.TestCase):
    """
    Trois listes ne reposaient que sur des locutions de 2+ mots, qui
    n'apparaissent jamais telles quelles dans un titre. Audit du
    2026-09-14 : censure_blocage sortait 2 articles sur 7795.
    """

    def _article(self, title, **overrides):
        article = {
            "title": title,
            "summary": "",
            "body": "",
            "source": "RFE/RL",
            "url": "https://www.rferl.org/a/sujet/123.html",
            "language": "en",
            "date": None,
        }
        article.update(overrides)
        return article

    def test_single_word_censorship_is_detected(self):
        for titre in (
            "Uzbekistan tightens censorship of online media",
            "Цензура и свобода СМИ в Узбекистане",
            "Блокировка независимого сайта в Киргизии",
        ):
            with self.subTest(titre=titre):
                cat = categoriser(self._article(titre))
                self.assertIn("censure_blocage", cat["traitement"])

    def test_press_freedom_is_a_theme_not_a_treatment(self):
        # Déclenchait seul sur "Sierra Leone", "Protect journalists" ou
        # un guide RSF sur les drones : un thème, pas un fait subi.
        cat = categoriser(self._article("Services aux journalistes et aux médias"))
        self.assertNotIn("censure_blocage", cat["traitement"])

    def test_generic_farsi_blocked_does_not_mean_censorship(self):
        # "مسدود" seul : 4 détections sur 4 fausses, toutes routières.
        cat = categoriser(
            self._article("ترافیک ۷ کیلومتری در جاده کندوان؛ چالوس مسدود شد")
        )
        self.assertNotIn("censure_blocage", cat["traitement"])

    def test_religious_role_is_an_actor(self):
        cat = categoriser(self._article("Imam detained in Tajikistan over sermon"))
        self.assertIn("croyant", cat["acteur"])

    def test_bare_religious_demonym_is_not_an_actor(self):
        # "muslim" seul décrit une population, pas quelqu'un à qui on
        # fait subir quelque chose.
        cat = categoriser(
            self._article("How Central Asia navigates Russia's war on Ukraine")
        )
        self.assertNotIn("croyant", cat["acteur"])


class PageThematiqueTests(unittest.TestCase):
    """
    Les pages de rubrique (pays, région, thème) ne sont pas des
    articles. Audit du 2026-09-14 : 441 sur 8174, dont 80 étiquetées
    "rapport_analyse" ou "evenement_date" — on affirmait que c'était
    du contenu.
    """

    def _article(self, url, title, **overrides):
        article = {
            "title": title, "summary": "", "body": "",
            "source": "Committee to Protect Journalists",
            "url": url, "language": "en", "date": None,
        }
        article.update(overrides)
        return article

    def test_country_landing_page_is_thematic(self):
        for url, titre in (
            ("https://cpj.org/africa/burkina-faso/", "Burkina Faso"),
            ("https://eurasianet.org/region/central-asia", "Central Asia"),
            ("https://www.uscirf.gov/countries/north-korea", "North Korea"),
            ("https://eurasianet.org/voices/tamada-tales", "Tamada Tales"),
        ):
            with self.subTest(url=url):
                cat = categoriser(self._article(url, titre))
                self.assertEqual(cat["type"], "page_thematique")

    def test_wins_over_date_and_body_length(self):
        # 80 des 441 portaient une date de dernière modification ou un
        # corps long, et ressortaient comme du contenu réel.
        cat = categoriser(
            self._article(
                "https://cpj.org/africa/sierra-leone/", "Sierra Leone",
                date="2026-09-01T00:00:00+00:00", body="x" * 5000,
            )
        )
        self.assertEqual(cat["type"], "page_thematique")

    def test_site_furniture_is_caught_too(self):
        cat = categoriser(
            self._article(
                "https://www.amnesty.org/en/cookie-statement/", "Cookie Statement"
            )
        )
        self.assertEqual(cat["type"], "page_thematique")

    def test_a_real_article_is_not_mistaken_for_one(self):
        # Le slug d'un vrai article est tronqué ou daté : l'égalité
        # exacte avec le titre ne se produit pas.
        cat = categoriser(
            self._article(
                "https://thediplomat.com/2026/09/north-koreas-nicaragua-court",
                "North Korea’s Nicaragua Courtship",
                date="2026-09-01T00:00:00+00:00",
            )
        )
        self.assertNotEqual(cat["type"], "page_thematique")

    def test_a_long_title_is_never_a_section(self):
        titre = "Kazakhstan Jails Activist For Ten Years Over Peaceful Protest"
        cat = categoriser(
            self._article(
                "https://ex.org/news/"
                "kazakhstan-jails-activist-for-ten-years-over-peaceful-protest",
                titre,
            )
        )
        self.assertNotEqual(cat["type"], "page_thematique")


class PaysVoisinsGeoTests(unittest.TestCase):
    """
    Un pays nommé dans le titre ne doit pas ressortir geo=aucune.

    Cas réel du 2026-09-14 : "Украина: Пытки, исчезновения в ходе
    конфликта на востоке страны" (HRW russe) ressortait sans
    géographie alors que le pays est le premier mot. Audit : 706
    articles sur 8824 nommaient un pays absent du registre.
    """

    def _article(self, titre, **overrides):
        article = {
            "title": titre, "summary": "", "body": "",
            "source": "Human Rights Watch", "url": "https://ex.org/news/a",
            "language": "ru", "date": None,
        }
        article.update(overrides)
        return article

    def test_the_reported_article_now_has_a_geography(self):
        cat = categoriser(
            self._article(
                "Украина: Пытки, исчезновения в ходе конфликта на востоке страны"
            )
        )
        self.assertEqual(cat["geo"], ["ukraine"])
        self.assertIn("украина", cat["preuves"]["geo"])

    def test_neighbouring_countries_get_their_own_value(self):
        for titre, attendu in (
            ("Китай усиливает контроль", "chine"),
            ("Беларусь: новые аресты", "bielorussie"),
            ("Turkey jails opposition journalists", "turquie"),
            ("Moldova tightens media rules", "moldavie"),
        ):
            with self.subTest(titre=titre):
                cat = categoriser(self._article(titre))
                self.assertIn(attendu, cat["geo"])

    def test_every_country_gets_its_own_name(self):
        # Décidé le 2026-09-14 : plus de fourre-tout "autre". Un pays
        # nommé dans le texte sort sous son nom, où qu'il soit.
        for titre, attendu in (
            ("India passes new press law", "inde"),
            ("Israel restricts foreign media access", "israel"),
            ("Pakistan detains rights defenders", "pakistan"),
            ("Fire at nursing home in Chile kills 16", "chili"),
            ("Myanmar junta jails reporters", "birmanie"),
        ):
            with self.subTest(titre=titre):
                cat = categoriser(self._article(titre))
                self.assertIn(attendu, cat["geo"])
                self.assertNotIn("autre", cat["geo"])

    def test_a_country_name_inside_another_never_fires(self):
        # "Papua New Guinea" contient "Guinea" comme mot entier, et
        # "South Sudan" contient "Sudan" : sans résolution par
        # correspondance la plus longue, l'article ressortirait sous
        # deux pays dont un faux.
        for titre, attendu, interdit in (
            ("Papua New Guinea", "papouasie_nouvelle_guinee", "guinee"),
            ("South Sudan crackdown on journalists", "soudan_du_sud", "soudan"),
        ):
            with self.subTest(titre=titre):
                cat = categoriser(self._article(titre))
                self.assertIn(attendu, cat["geo"])
                self.assertNotIn(interdit, cat["geo"])

    def test_regions_are_named_as_regions(self):
        # "Asie centrale" n'est pas un pays, mais c'est le coeur du
        # périmètre : le verser dans "autre" (= ailleurs) était le
        # contraire de la vérité.
        cat = categoriser(self._article("Central Asia faces new water crisis"))
        self.assertIn("asie_centrale", cat["geo"])
        self.assertNotIn("autre", cat["geo"])

    def test_a_common_word_is_not_mistaken_for_a_country(self):
        # "Того" (Togo en russe) est le génitif de "тот" : il
        # déclenchait 446 articles avant d'être écarté du générateur.
        cat = categoriser(
            self._article("Из-за того что власти Казахстана усилили контроль")
        )
        self.assertNotIn("togo", cat["geo"])

    def test_neighbours_never_reach_the_scoring_gate(self):
        # La garantie qui compte : ces pays sont DESCRIPTIFS. S'ils
        # entraient dans la porte régionale de scoring.py, un article
        # ukrainien ou chinois serait traité comme régional et son
        # score gonflerait.
        from scoring import classify_article

        article = self._article("Украина: Пытки, исчезновения в ходе конфликта")
        classify_article(article)

        self.assertFalse(article["signals"]["regional_context"])


class PaysMondeEstGenereTests(unittest.TestCase):
    """pays_monde.py est généré ; pycountry ne doit jamais devenir une
    dépendance d'exécution du scanner."""

    def test_pycountry_is_only_imported_by_the_generator(self):
        import re
        from pathlib import Path

        racine = Path(__file__).resolve().parent.parent
        coupables = []

        for fichier in racine.glob("*.py"):
            texte = fichier.read_text(encoding="utf-8")
            if re.search(r"^\s*(import pycountry|from pycountry)", texte, re.M):
                coupables.append(fichier.name)

        self.assertEqual(coupables, [])

    def test_the_generated_table_is_consistent(self):
        from pays_monde import PAYS_MONDE_LIBELLES, PAYS_MONDE_TERMES

        self.assertGreater(len(PAYS_MONDE_LIBELLES), 150)
        orphelins = set(PAYS_MONDE_TERMES.values()) - set(PAYS_MONDE_LIBELLES)
        self.assertEqual(orphelins, set(), "des pays sans libellé")


class MinoriteSexuelleEtCriminalisationTests(unittest.TestCase):
    """
    Deux manques du schéma, trouvés sur "Le Burkina Faso criminalise
    les relations homosexuelles" : acteur=aucun et traitement=aucun
    sur un article qui décrit précisément les deux.
    """

    def _article(self, titre, langue="fr"):
        return {
            "title": titre, "summary": "", "body": "",
            "source": "Human Rights Watch", "url": "https://ex.org/news/a",
            "language": langue, "date": None,
        }

    def test_the_reported_article_is_fully_described(self):
        cat = categoriser(
            self._article("Le Burkina Faso criminalise les relations homosexuelles")
        )
        self.assertIn("burkina_faso", cat["geo"])
        self.assertIn("minorite_sexuelle", cat["acteur"])
        self.assertIn("criminalisation", cat["traitement"])
        self.assertTrue(cat["relation_acteur_traitement"])

    def test_regional_cases_are_caught(self):
        # Les articles que cette veille existe pour remonter.
        for titre in (
            "Ouzbékistan : Les hommes gays face au risque d'abus",
            "Turkménistan : Un homme gay porté disparu",
            "Kazakhstan's parliament passes law restricting LGBTQ+ content",
            "Казахстан: Как на ЛГБТИК+ сообществе обкатывают процесс",
        ):
            with self.subTest(titre=titre):
                self.assertIn(
                    "minorite_sexuelle", categoriser(self._article(titre))["acteur"]
                )

    def test_criminalisation_vocabulary_stays_narrow(self):
        # "banned"/"ban on"/"запретил" ont été testés puis écartés :
        # 62 détections majoritairement fausses ("Travel Bans", "UK
        # edition"), la même erreur que "press freedom" sur
        # censure_blocage.
        for titre in (
            "Criminal Cases, Travel Bans: Pressure Mounts On Kazakh Journalists",
            "Amid Setbacks, Putin Looks To Restore Russia's Standing",
        ):
            with self.subTest(titre=titre):
                self.assertNotIn(
                    "criminalisation",
                    categoriser(self._article(titre, langue="en"))["traitement"],
                )

    def test_a_repressive_law_is_a_criminalisation(self):
        cat = categoriser(
            self._article("Géorgie : Des lois répressives criminalisent les manifestations")
        )
        self.assertIn("criminalisation", cat["traitement"])
