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
                "geo", "geo_role", "acteur", "acteur_role",
                "traitement", "traitement_role",
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


class FormesFrancaisesTests(unittest.TestCase):
    """
    Audit par échantillon du 2026-09-14 : FEMME, CITOYEN,
    MINORITE_ETHNIQUE et DISPARITION n'avaient aucune forme française,
    pour 274 articles de sources francophones (HRW, Amnesty, RSF,
    FIDH). "Liban : Les femmes transgenres face à la discrimination"
    ressortait acteur=aucun.
    """

    def _article(self, titre):
        return {
            "title": titre, "summary": "", "body": "",
            "source": "Human Rights Watch — français",
            "url": "https://ex.org/news/a", "language": "fr", "date": None,
        }

    def test_french_women_are_detected(self):
        for titre in (
            "Ouzbékistan : Les droits des femmes en recul",
            "Une femme condamnée pour avoir manifesté",
            "Les filles privées d'école",
        ):
            with self.subTest(titre=titre):
                self.assertIn("femme", categoriser(self._article(titre))["acteur"])

    def test_the_reported_article_gets_both_actors(self):
        cat = categoriser(
            self._article("Liban : Les femmes transgenres face à la discrimination")
        )
        self.assertIn("femme", cat["acteur"])
        self.assertIn("minorite_sexuelle", cat["acteur"])

    def test_french_disappearance_is_detected(self):
        cat = categoriser(
            self._article("Turkménistan : Un homme gay porté disparu après son coming out")
        )
        self.assertIn("disparition", cat["traitement"])

    def test_french_ethnic_minority_is_detected(self):
        cat = categoriser(
            self._article("Chine : Répression d'une minorité ethnique au Xinjiang")
        )
        self.assertIn("minorite_ethnique", categoriser(
            self._article("Chine : Répression d'une minorité ethnique au Xinjiang")
        )["acteur"])
        self.assertIn("xinjiang", cat["geo"])


class RoleActeurEtTraitementTests(unittest.TestCase):
    """
    acteur_role / traitement_role : d'OÙ vient le signal.

    Un même mot ne vaut pas la même chose selon l'endroit où il
    apparaît. "journaliste" dans le titre désigne le sujet ;
    "journaliste" à la 4000e lettre du corps peut n'être qu'une
    signature. La géographie faisait déjà cette distinction parce
    qu'elle est cherchée deux fois ; les acteurs, cherchés une seule
    fois sur le texte fusionné, perdaient l'information à la détection.

    Mesuré le 2026-09-14 : 1424 des 1870 articles portant un acteur
    (76%) ne le tiennent que du corps.
    """

    def _article(self, titre, corps="", langue="en"):
        return {
            "title": titre, "summary": "", "body": corps,
            "source": "Test", "url": "https://ex.org/news/a",
            "language": langue, "date": None,
        }

    def test_an_actor_in_the_title_is_the_subject(self):
        cat = categoriser(self._article("Journalist jailed in Almaty, Kazakhstan"))
        self.assertEqual(cat["acteur_role"], "sujet_principal")

    def test_an_actor_only_in_the_body_is_a_mention(self):
        cat = categoriser(
            self._article(
                "Pickleball in China: how a tiny ball drives an industry",
                corps="The editor spoke to residents, men and women alike.",
            )
        )
        self.assertIn("journaliste", cat["acteur"])
        self.assertEqual(cat["acteur_role"], "mention_secondaire")

    def test_no_actor_means_absent(self):
        cat = categoriser(self._article("Weather forecast for tomorrow"))
        self.assertEqual(cat["acteur_role"], "absent")

    def test_treatment_role_works_the_same_way(self):
        titre = categoriser(self._article("Activist sentenced to ten years"))
        corps = categoriser(
            self._article("Pickleball tournament", corps="He was sentenced in 2019.")
        )
        self.assertEqual(titre["traitement_role"], "sujet_principal")
        self.assertEqual(corps["traitement_role"], "mention_secondaire")

    def test_the_strongest_role_wins_for_the_axis(self):
        # Un acteur dans le titre et un autre dans le corps : l'article
        # a bien un acteur pour sujet. C'est le détail par classe, dans
        # les preuves, qui dit lequel.
        cat = categoriser(
            self._article("Journalist detained", corps="Local residents watched.")
        )
        self.assertEqual(cat["acteur_role"], "sujet_principal")
        self.assertEqual(
            cat["preuves"]["acteur_role"]["citoyen_ordinaire"]["titre_ou_chapo"], []
        )

    def test_the_values_themselves_are_unchanged(self):
        # La promesse du correctif : purement additif. Vérifié sur le
        # corpus réel (203170 comparaisons, zéro divergence), et gardé
        # ici sur un cas représentatif.
        cat = categoriser(
            self._article(
                "Journalist detained in Almaty",
                corps="Human rights defenders and women protested.",
            )
        )
        for attendu in ("journaliste", "defenseur", "femme"):
            self.assertIn(attendu, cat["acteur"])

    def test_evidence_records_both_zones(self):
        cat = categoriser(
            self._article("Journalist detained", corps="Another journalist spoke.")
        )
        zones = cat["preuves"]["acteur_role"]["journaliste"]
        self.assertTrue(zones["titre_ou_chapo"])
        self.assertTrue(zones["corps"])


class ReglesRoleMinimumTests(unittest.TestCase):
    """Le réglage est exposé mais non décidé : il reste à None."""

    def test_the_constants_stay_undecided(self):
        import regles_editoriales as regles

        self.assertIsNone(regles.ACTEUR_ROLE_MINIMUM)
        self.assertIsNone(regles.TRAITEMENT_ROLE_MINIMUM)

    def test_a_mention_is_rejected_once_the_rule_is_set(self):
        from unittest.mock import patch

        import regles_editoriales as regles

        categorisation = {
            "geo": ["kazakhstan"], "geo_role": "sujet_principal",
            "acteur": ["journaliste"], "acteur_role": "mention_secondaire",
            "traitement": ["aucun"], "traitement_role": "absent",
            "type": "evenement_date", "age_jours": 1,
            "relation_acteur_traitement": False,
        }

        with patch.object(regles, "ACTEUR_ROLE_MINIMUM", "sujet_principal"):
            pertinent, raison = regles.est_pertinent(categorisation)

        self.assertFalse(pertinent)
        self.assertIn("acteur_role", raison)


class RoleHeriteDuXinjiangTests(unittest.TestCase):
    """
    La minorité ethnique déduite de geo=xinjiang hérite du rôle du
    XINJIANG, pas de celui de l'axe géo entier.

    Bug attrapé à l'écriture du correctif, sur un cas réel : "The
    Horrors Of Aktas Mental Hospital: Inside Kazakhstan's Secretive
    Asylum" a geo_role=sujet_principal (le Kazakhstan est dans le
    titre) alors que le Xinjiang n'apparaît que dans le corps. Faire
    hériter geo_role donnait à la minorité le statut de sujet sans
    qu'aucun terme la concernant soit dans le titre — et remontait
    tout l'axe acteur avec elle.
    """

    def _article(self, titre, corps=""):
        return {
            "title": titre, "summary": "", "body": corps,
            "source": "Test", "url": "https://ex.org/news/a",
            "language": "en", "date": None,
        }

    def test_xinjiang_in_the_body_only_is_a_mention(self):
        cat = categoriser(
            self._article(
                "Inside Kazakhstan's Secretive Asylum",
                corps="Reports from Xinjiang describe similar conditions.",
            )
        )
        self.assertIn("minorite_ethnique", cat["acteur"])
        self.assertEqual(cat["acteur_role"], "mention_secondaire")

    def test_xinjiang_in_the_title_is_the_subject(self):
        cat = categoriser(self._article("Uyghur activists detained in Xinjiang"))
        self.assertIn("minorite_ethnique", cat["acteur"])
        self.assertEqual(cat["acteur_role"], "sujet_principal")

    def test_another_country_in_the_title_does_not_promote_it(self):
        # Le coeur du bug : un pays en titre ne doit pas hisser une
        # minorité déduite d'un pays cité seulement dans le corps.
        cat = categoriser(
            self._article(
                "Kazakhstan opens new hospital",
                corps="Xinjiang was mentioned once in passing.",
            )
        )
        self.assertEqual(cat["acteur_role"], "mention_secondaire")


class FenetreRelationTests(unittest.TestCase):
    """
    La fenêtre de relation est un réglage nommé, plus un nombre magique
    enfoui dans une signature de fonction.

    Elle est restée trois mois sans justification (commit "improve").
    Mesurée le 2026-09-14 : la courbe a un coude à 140 et la
    distribution des écarts est bimodale (q1=12, médiane=97, q3=652),
    donc 140 sépare bien "même phrase" de "paragraphes différents".
    """

    def _article(self, titre, corps=""):
        return {
            "title": titre, "summary": "", "body": corps,
            "source": "Test", "url": "https://ex.org/news/a",
            "language": "en", "date": None,
        }

    def test_the_window_is_a_named_constant(self):
        import categorisation
        import matching

        self.assertEqual(
            categorisation.FENETRE_RELATION, matching.FENETRE_RELATION_DEFAUT
        )
        self.assertEqual(matching.FENETRE_RELATION_DEFAUT, 140)

    def test_close_terms_make_a_relation(self):
        cat = categoriser(
            self._article("Journalist detained in Almaty, Kazakhstan")
        )
        self.assertTrue(cat["relation_acteur_traitement"])

    def test_distant_terms_do_not(self):
        # Acteur et traitement présents, mais séparés par bien plus que
        # la fenêtre : c'est exactement le cas "paragraphes différents"
        # que le troisième quartile (652 caractères) décrit.
        cat = categoriser(
            self._article(
                "Kazakhstan opens new hospital",
                corps=(
                    "A journalist attended the opening. "
                    + "Filler about the building and its architecture. " * 12
                    + "In an unrelated case, a man was sentenced last year."
                ),
            )
        )
        self.assertIn("journaliste", cat["acteur"])
        self.assertIn("condamnation", cat["traitement"])
        self.assertFalse(cat["relation_acteur_traitement"])

    def test_the_window_is_actually_honoured(self):
        # Le réglage doit piloter la détection, pas seulement exister.
        from unittest.mock import patch

        import categorisation

        article = self._article(
            "Kazakhstan news",
            corps=(
                "A journalist spoke. " + "x" * 300 + " He was sentenced."
            ),
        )

        with patch.object(categorisation, "FENETRE_RELATION", 10):
            serre = categorisation.categoriser(article)
        with patch.object(categorisation, "FENETRE_RELATION", 5000):
            large = categorisation.categoriser(article)

        self.assertFalse(serre["relation_acteur_traitement"])
        self.assertTrue(large["relation_acteur_traitement"])


class VocabulaireAnglesMortsTests(unittest.TestCase):
    """
    Vocabulaire ajouté le 2026-09-14 après un audit des angles morts :
    sur 971 articles publiés par des organisations dont les droits
    humains sont le métier (HRW, Amnesty, RSF, CPJ, FIDH, OMCT,
    CIVICUS), 803 ressortaient en E/F. 572 étaient hors zone, mais 231
    étaient dans le périmètre — "Azerbaijan: Opposition Leader
    Arrested" ressortait acteur=aucun.
    """

    def _article(self, titre, langue="en"):
        return {
            "title": titre, "summary": "", "body": "",
            "source": "Human Rights Watch", "url": "https://ex.org/news/a",
            "language": langue, "date": None,
        }

    def test_political_figures_are_actors(self):
        for titre, attendu in (
            ("Azerbaijan: Opposition Leader Arrested", "opposant"),
            ("Azerbaijan Escalates Crackdown on Exiled Critics", "opposant"),
            ("Dozens of protesters detained in Kazakhstan", "opposant"),
        ):
            with self.subTest(titre=titre):
                self.assertIn(attendu, categoriser(self._article(titre))["acteur"])

    def test_bloggers_count_as_journalists(self):
        # La figure la plus réprimée en Ouzbékistan, absente de
        # JOURNALIST_TERMS.
        cat = categoriser(
            self._article("Uzbekistan: Free Blogger from Forced Psychiatric Detention")
        )
        self.assertIn("journaliste", cat["acteur"])

    def test_being_detained_is_also_an_identity(self):
        for titre in (
            "Belarus: Release of over 200 other political prisoners",
            "Detainee says China has secret jail in Dubai",
            "Azerbaijan: Armenian POWs Abused in Custody",
        ):
            with self.subTest(titre=titre):
                self.assertIn("detenu", categoriser(self._article(titre))["acteur"])

    def test_professional_roles_are_actors(self):
        for titre, attendu in (
            ("Kazakhstan Authorities Arrest Professor Suspected of Espionage",
             "universitaire"),
            ("French artist imprisoned in Azerbaijan due to graffiti", "artiste"),
        ):
            with self.subTest(titre=titre):
                self.assertIn(attendu, categoriser(self._article(titre))["acteur"])

    def test_demographics_are_not_actors(self):
        # Même ligne que "imam" gardé et "muslim" écarté : un rôle
        # qu'on peut arrêter pour ce qu'il fait, contre une catégorie
        # de population. Ces titres déclenchaient les candidats
        # "etudiant" et "enfant", rejetés pour cette raison.
        for titre in (
            "New KNU building for 3,000 students opened in Talas",
            "Psychological support for parents raising children",
        ):
            with self.subTest(titre=titre):
                acteurs = categoriser(self._article(titre))["acteur"]
                self.assertNotIn("etudiant", acteurs)
                self.assertNotIn("enfant", acteurs)

    def test_surveillance_is_a_treatment(self):
        # Mode de répression majeur et contemporain, totalement absent
        # du schéma : 51 articles du corpus.
        for titre in (
            "Facial Recognition Deal in Kyrgyzstan Poses Risks to Rights",
            "Surveillance and Spyware",
            "Слежка за активистами в Казахстане",
        ):
            with self.subTest(titre=titre):
                self.assertIn(
                    "surveillance", categoriser(self._article(titre))["traitement"]
                )

    def test_punitive_psychiatry_is_a_treatment(self):
        cat = categoriser(
            self._article("Uzbekistan: End the Punitive Psychiatric Detention")
        )
        self.assertIn("internement_psychiatrique", cat["traitement"])

    def test_travel_bans_and_forced_exile_are_treatments(self):
        for titre, attendu in (
            ("Tajikistan: Lift Travel Ban on Critically Ill Child",
             "interdiction_voyager"),
            ("Forced Exile of Indigenous Rights Activists", "exil_force"),
        ):
            with self.subTest(titre=titre):
                self.assertIn(
                    attendu, categoriser(self._article(titre))["traitement"]
                )

    def test_ill_treatment_is_detected(self):
        # Formule standard des rapports HRW/Amnesty, qui manquait.
        cat = categoriser(self._article("Azerbaijan: Armenian POWs Abused in Custody"))
        self.assertIn("violence_physique", cat["traitement"])


class ViolencePhysiqueTests(unittest.TestCase):
    """
    Audit du 2026-09-14 : violence_physique ne ressortait que 14 fois
    sur 4000 articles. La classe n'avait AUCUN motif de racine russe,
    alors que les autres traitements en ont depuis le 2026-09-12 —
    "избиения", "избили", "избита" n'ont aucune chance de matcher une
    liste de locutions anglaises qualifiées ("extrajudicial killing",
    "death in custody").

    Chaque racine a été vérifiée sur les 9235 articles archivés, et
    "beaten" porte une exclusion mesurée plutôt qu'une supposition.
    """

    def _traitements(self, titre, corps=""):
        resultat = categoriser(
            {
                "title": titre,
                "summary": corps,
                "body": corps,
                "source": "Test",
                "url": "https://example.org/a",
            }
        )
        return [t for t in resultat["traitement"] if t != "aucun"]

    def test_racines_russes_du_passage_a_tabac(self):
        # 19 occurrences dans le corpus pour ces trois racines, 19
        # justes. Aucune n'était détectée avant.
        for titre in (
            "Казахстан: Произвольные аресты и избиения протестующих",
            "Их избили, а потом одного еще и посадили",
            "Она была избита полицией, что привело к перелому ключицы",
        ):
            with self.subTest(titre=titre):
                self.assertIn("violence_physique", self._traitements(titre))

    def test_beaten_en_anglais(self):
        self.assertIn(
            "violence_physique",
            self._traitements("Kazakhstan: Protesters Arbitrarily Arrested, Beaten"),
        )

    def test_idiome_touristique_exclu(self):
        # Le garde-fou. Sur 8 occurrences de "beaten" dans le corpus,
        # la seule fausse venait de cet idiome, sur un article RFE/RL
        # vantant la région. Sans le (?! track| path), ce seul cas
        # suffisait à disqualifier le terme entier.
        self.assertNotIn(
            "violence_physique",
            self._traitements(
                "Central Asia draws Western tourists",
                "Travellers looking for a holiday off the beaten track will find much here.",
            ),
        )

    def test_violences_policieres(self):
        self.assertIn(
            "violence_physique",
            self._traitements("Armenia: Limited Justice for Police Violence"),
        )

    def test_poboi_ne_matche_pas_pobochny(self):
        # Les terminaisons de "побои" sont énumérées plutôt que
        # laissées à \\w* : "побочный" (collatéral) partage le préfixe
        # et n'a rien à voir avec des coups.
        self.assertNotIn(
            "violence_physique",
            self._traitements("Побочный эффект новой экономической политики"),
        )


class DisparitionSansFauxPositifTests(unittest.TestCase):
    """
    DISPARITION_TERMS contenait "disappeared" nu — exactement le terme
    rejeté côté scoring le même jour, et pour la même raison. Sur les
    9235 articles archivés, il ne déclenchait qu'UN titre, et c'était
    la mer d'Aral.
    """

    def _traitements(self, titre, corps=""):
        resultat = categoriser(
            {
                "title": titre,
                "summary": corps,
                "body": corps,
                "source": "Test",
                "url": "https://example.org/a",
            }
        )
        return [t for t in resultat["traitement"] if t != "aucun"]

    def test_une_mer_qui_seche_n_est_pas_une_disparition_forcee(self):
        self.assertNotIn(
            "disparition",
            self._traitements(
                "The Aral Sea has all but disappeared",
                "But in small towns and villages, signs of life remain.",
            ),
        )

    def test_la_forme_qualifiee_reste_detectee(self):
        for titre in (
            "Turkmenistan: Enforced Disappearance of Activist",
            "Tadjikistan : disparition forcée d'un opposant",
        ):
            with self.subTest(titre=titre):
                self.assertIn("disparition", self._traitements(titre))
