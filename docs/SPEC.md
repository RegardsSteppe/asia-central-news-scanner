# Spécification — asia-central-news-scanner

Ce que le système fait, extrait du code au 2026-10-03. Ni le pourquoi
(`docs/HISTORY.md`), ni les consignes de travail (`CLAUDE.md`) : les
contrats observables.

Toute valeur chiffrée ci-dessous est une constante du code, citée avec
son module. Les mesures sur corpus sont datées et marquées comme telles —
elles décrivent l'état des données, pas une garantie.

---

## 1. Objet

Surveiller la presse sur l'Asie centrale, le Caucase et le Xinjiang,
noter chaque article par des règles déterministes et explicables, et
publier un site statique classé.

Le scoring n'utilise aucun LLM pour décider de la pertinence. Un juge LLM
existe (`juge_llm.py`, déployé sur RunPod) mais rend un **avis
indépendant**, jamais intégré au score.

**Zone de veille** (`scoring.regional_context`) : Asie centrale **OU**
Caucase **OU** Ouïghours. Un article hors zone ne peut pas dépasser le
niveau D.

---

## 2. Entrées

### 2.1 Sources — `sources.py`

122 sources, chacune un dict à 8 clés obligatoires et 2 optionnelles :

| Clé | Obligatoire | Rôle |
|---|---|---|
| `name`, `short_name`, `label` | oui | identité et affichage |
| `type` | oui | `rss` (24) ou `html` (98) |
| `url` | oui | point d'entrée |
| `language` | oui | langue déclarée — **non fiable**, voir §5.6 |
| `profile` | oui | 13 valeurs, dont `human_rights` (24), `state_media` (23) |
| `max_articles` | oui | plafond par scan |
| `feeds` | non (24) | flux multiples |
| `fallbacks` | non (13) | URL de repli si la principale échoue |

Langues déclarées : `en` 88, `ru` 22, `fr` 4, `multi` 2, `de` 2, `kk` 1,
`tg` 1, `uz` 1.

### 2.2 Conséquence structurelle du type `html`

Le chemin HTML (`article_ingestion`, `extract_links_from_html`) construit
un article depuis un lien de page de listing : il n'a que **titre + URL**,
et pose `summary=""`. Ce n'est pas un défaut mais la nature de la source.

Le chemin RSS lit `summary` ou `description`, **sauf** pour Google News,
où la `<description>` est délibérément vidée : elle ne contient que le
titre ré-empaqueté en HTML.

*Mesuré le 2026-09-20 sur 13 366 entrées archivées : 0,5 % portent un
résumé, 35,5 % un corps. Les deux tiers du corpus sont donc notés sur le
titre seul.*

---

## 3. Pipeline — `news_scanner.run_scan()`

Étapes dans l'ordre, telles que nommées par `timed_call` :

1. **mémoire** — `show_memory()`, `compute_seen_keys()`
2. **`fetch+parse`** — `collect_articles()`, parallélisé
3. **`deduplicate`** — URL canonique ou titre normalisé
4. **garde-fou** — `check_corpus_not_collapsed()`, **avant toute écriture**
5. **`score-first-pass`** — titre + résumé uniquement
6. **`vocabulary`** — mots fréquents des titres
7. **corps d'archive** — rendus aux articles, nettoyés à la lecture
8. **`enrichment`** — téléchargement des corps manquants, sous budget
9. **`archive`** — `merge_with_archive()`
10. **`sort-final`**
11. **`build-stats`**
12. **`build-audit`**
13. **`synthesis`** — LLM, **niveau A seulement**, optionnel
14. **`export-html`** → `index.html`
15. **`export-csv`** → `articles.csv`
16. sauvegarde de la mémoire

Deux passes de notation : la première sur titre + résumé classe tout le
corpus à bas coût ; la seconde ne concerne que les articles retenus pour
l'enrichissement, renotés avec leur corps.

---

## 4. Contrats de données

### 4.1 Entrée d'archive — `archive.ARCHIVE_FIELDS`

Exactement 10 champs : `key`, `url`, `title`, `summary`, `source`,
`source_label`, `language`, `date`, `premiere_vue`, `body`.

Aucun champ `score`, `level`, `relevant` ou `pertinent` : l'archive
stocke des **faits immuables**, jamais un jugement. Un corpus archivé
est renotable intégralement après un changement de scoring.

- `body` conservé seulement si `level ∈ BODY_KEEP_LEVELS`
  (`SCANNER_BODY_KEEP_LEVELS`, défaut `A,B,C,D,E`), tronqué à
  `BODY_MAX_CHARS = 8000`.
- `date` sérialisée en ISO ; reparsée par l'appelant.

### 4.2 Sortie de `categoriser()` — `categorisation.py`

11 champs descriptifs, plus les preuves :

| Champ | Valeurs |
|---|---|
| `geo` | liste de pays / régions, ou `["aucun"]` |
| `geo_role` | `sujet_principal` \| `mention_secondaire` \| `absent` |
| `acteur` | liste parmi 15 catégories, ou `["aucun"]` |
| `acteur_role` | même échelle que `geo_role` |
| `traitement` | liste parmi 14 catégories, ou `["aucun"]` |
| `traitement_role` | même échelle |
| `relation_acteur_traitement` | booléen — co-occurrence dans une fenêtre de `FENETRE_RELATION = 140` caractères |
| `type` | `evenement_date` \| `rapport_analyse` \| `plaidoyer_communique` \| `page_thematique` \| `indetermine` \| `navigation` |
| `age_jours` | entier ou `null` |
| `source_specialisee` | booléen |
| `preuves` | pour chaque étiquette, les termes trouvés et leur emplacement (`titre_ou_chapo` / `corps`) |

`categoriser()` est une **fonction de lecture pure** : elle ne modifie
pas l'article reçu, contrairement à `classify_article()` qui réécrit
`article["language"]` sur place.

**Le rôle a deux paliers là où il en faudrait trois.** `mention_secondaire`
confond un terme répété dans le corps et un mot incident unique.
`preuves` contient de quoi les distinguer, le champ `*_role` ne l'expose
pas. *Mesuré le 2026-09-18 : 57,8 % des étiquettes `acteur` et 53,9 % des
`traitement` reposent sur une occurrence unique d'un terme unique.*

### 4.3 Sous-scores — `news_scanner.score_fields`

Six, exposés dans le CSV : `geography_score`, `target_score`,
`repression_score`, `rights_score`, `journalism_score`,
`geopolitical_score`.

`signals` porte en plus ~60 booléens de diagnostic (`primary_hr_anchor`,
`regional_context`, `has_activist`, `confirmed_repression`…), repris dans
le harnais de caractérisation sous forme d'empreinte.

---

## 5. Scoring — `scoring.py`

### 5.1 Niveaux, dans l'ordre d'évaluation de `decide_level()`

| Niveau | Condition |
|---|---|
| **F** | `section_page` — **testé en premier**, avant la géographie |
| **D** | `regional_context` faux **et** `global_hr_signal` vrai |
| **E** | `regional_context` faux et pas de signal HR |
| **E** | `non_news` ou `noise` |
| **A** | `score ≥ 75` **et** au moins une confirmation (§5.2) |
| **B** | `score ≥ 55` |
| **C** | `score ≥ 35` |
| **E** | tout le reste |

Constantes : `LEVEL_A_MIN_SCORE = 75`, `LEVEL_B_MIN_SCORE = 55`,
`LEVEL_C_MIN_SCORE = 35`.

**F avant la géographie** : une page pays nomme évidemment son pays, les
tests de géographie la valideraient à tort.

**D n'est atteignable que hors zone.** Un article *dans* la zone dont le
score reste sous 35 tombe directement en E — il n'existe aucun palier
intermédiaire pour un article régional insuffisamment noté.

### 5.2 Confirmations exigées pour A — `_LEVEL_A_CONFIRMATIONS`

`confirmed_activist_pressure`, `confirmed_journalist_pressure`,
`severe_detected`, `confirmed_repression`, `primary_forced_labor`,
`primary_lgbt_pressure`, `primary_press`, `critical_hr_case`.

Un score ≥ 75 sans aucune de ces huit ne donne pas A.

### 5.3 Pertinence — `decide_relevance()`

`RELEVANCE_MIN_SCORE = 40`. Indépendante du niveau.

Vrai si `confirmed_activist_pressure` **ou**
`confirmed_journalist_pressure` — ces deux signaux passent outre le seuil
de score, par choix explicite. Sinon : `regional_context` **et**
`score ≥ 40` **et** ni `non_news` ni `noise` **et** au moins un des dix
signaux de `_RELEVANCE_SIGNALS`.

### 5.4 Thème et priorité

`decide_theme()` renvoie le premier signal présent dans l'ordre de
`_THEME_RULES`, sinon `"Faible priorité"`.
`decide_priority()` : 90 → `ABSOLUE`, 75 → `TRÈS HAUTE`, 60 → `HAUTE`,
40 → `MOYENNE`, 20 → `FAIBLE`.

### 5.5 Invariants de calcul

- **Aucun plafond ne vaut la valeur d'un seuil.** Le test de niveau est
  `>=`, donc un plafond posé sur le seuil promeut au lieu de retenir.
  Les plafonds s'écrivent `LEVEL_x_MIN_SCORE - 1`.
- Hors zone, le score est plafonné à 20.
- Le score final est borné à `[0, 100]`.
- Le score **ne dépend pas de la fraîcheur** — vérifié par
  `ScoreIsAgeIndependentTests`.

### 5.6 Détection de langue

`resolve_language()` arbitre entre la langue déclarée par la source et
celle détectée dans le texte. La langue déclarée est connue pour être
fausse sur plusieurs sources ; les motifs propres à un script
(cyrillique, persan) ne sont lancés que si la langue **résolue** le
justifie.

---

## 6. Couche éditoriale — `regles_editoriales.py`

### 6.1 Contrat

`est_pertinent(categorisation) -> (bool, str)`. La raison est toujours
renseignée, y compris quand le verdict est positif.

Neuf constantes de choix, **toutes à `None`** : `PERIMETRE_GEO`,
`GEO_ROLE_MINIMUM`, `ACTEUR_ROLE_MINIMUM`, `TRAITEMENT_ROLE_MINIMUM`,
`ACTEURS_RETENUS`, `TRAITEMENTS_RETENUS`, `TYPES_EXCLUS`,
`AGE_MAXIMUM_JOURS`, `EXIGER_RELATION_ACTEUR_TRAITEMENT`.

Sémantique : **une constante à `None` ne filtre pas**. Le module est donc
fonctionnel et permissif sans qu'aucune valeur n'ait été devinée.

Les filtres se combinent en **ET** — chacun peut opposer son veto, et les
effets se cumulent.

`VERSION_REGLES` date le jeu de règles, pour pouvoir réévaluer un corpus
déjà catégorisé sans le rescanner.

### 6.2 État actuel : sans effet

`_apply_categorisation()` écrit `categorisation_pertinent` et
`categorisation_reason` sur l'article et dans le CSV, et **n'affecte
jamais** `score`, `level`, `theme` ni `relevant`. Le classement du site
vient entièrement de `classify_article()`.

Tant que les neuf constantes sont à `None`, `categorisation_pertinent`
vaut toujours `True`. Les remplir change l'audit, pas le site.

---

## 7. Persistance

### 7.1 Archive — `data/archive.jsonl`

Append-only. Une ligne = un article. Invariants :

- `merge_scanned()` **ne réécrit jamais** une entrée existante.
- Une ligne illisible est ignorée, jamais fatale : l'archive doit rester
  lisible malgré une écriture interrompue.
- La fusion de deux fichiers (`merge_files`) résout en **UNION**, jamais
  par un gagnant — sinon un run concurrent perdrait ses lignes.
- Les correctifs rétroactifs sont des fonctions **idempotentes**
  (`backfill_bodies`, `nettoyer_corps`, `nettoyer_titres`,
  `backfill_dates`), appelées depuis le bloc de maintenance du scan.
- Les chemins ne sont définis qu'une fois (`DATA_DIR`) ; les points
  d'écriture créent le dossier au besoin.

`data/archive_state.json` est dérivé et réécrit à chaque run.
`data/memory.json` porte la fraîcheur par source et les clés vues ;
committé par la CI à dessein.

### 7.2 Garde-fou anti-effondrement

`check_corpus_not_collapsed()` lève `CorpusCollapseError` si le scan
collecte moins de `CORPUS_COLLAPSE_RATIO` (défaut **0,5**) du run
précédent. **Rien n'est publié** ; le site garde sa version complète.

- Jamais déclenché au premier run (pas de référence) ni quand le corpus
  grandit. La référence est `memory["last_corpus_size"]`.
- `SCANNER_ALLOW_CORPUS_DROP=1` dégrade l'erreur en avertissement, pour
  une chute légitime et assumée (panne durable d'un fournisseur, coupe
  volontaire de sources).

Comparant un fetch instantané au run n-1, il échoue légitimement sur un
déclenchement manuel hors créneau. Ce n'est pas une régression.

---

## 8. Sorties

- `index.html` — tableau de bord, régénéré intégralement (jamais fusionné).
- `articles.csv` — une ligne par article : identité, score, niveau, thème,
  priorité, pertinence, les six sous-scores, et les champs
  `categorisation_*` (dont `categorisation_pertinent` et sa raison).
- `html_template.ARCHIVAL_AGE_DAYS = 60` : au-delà, un article est marqué
  « republié » à l'affichage.
- Le rôle est annoté à l'affichage : `mention_secondaire` rend
  « (mention) », ce qui distingue un article *sur* un journaliste d'un
  article qui en cite un au passage.

---

## 9. Surfaces d'exécution

| Commande | Effet |
|---|---|
| `python news_scanner.py [--scan]` | scan complet ; `--scan` force la récupération |
| `python archive.py --merge-into BASE INCOMING` | fusion en union de deux archives |
| `python fetch_all_bodies.py --archive [--workers N] [--limit N]` | remplit les corps manquants de l'archive |
| `python find_candidate_sources.py --csv articles.csv` | découverte de sources |
| `python -m unittest discover` | suite de tests — ce que lance la CI |
| `python tests/fixtures/rebuild_scoring_snapshot.py` | régénère le snapshot de caractérisation |

Workflows : `news-scanner.yml` (planifié + manuel), `fetch-bodies.yml`
(manuel), `find-sources.yml`, `tests.yml` (sur PR et sur `main`).

RunPod — `rp_handler.py`, trois modes : `score` (tout en une passe),
`batch` (par lots, même résultat), `judge` (avis LLM indépendant).
Images construites par `Dockerfile` et `Dockerfile.juge`, qui copient une
liste explicite de modules ; `tests/test_runpod_image.py` vérifie que tout
module importé y figure.

---

## 10. Configuration

Toutes préfixées `SCANNER_` :

`FETCH_WORKERS`, `ENRICH_WORKERS`, `ENRICH_LIMIT`,
`ENRICH_PER_SOURCE_LIMIT`, `SOURCE_MIN_INTERVAL`,
`HTTP_CONNECT_TIMEOUT`, `HTTP_READ_TIMEOUT`, `HTTP_MAX_ATTEMPTS`,
`HTTP_RETRY_BACKOFF_BASE`, `BODY_KEEP_LEVELS`, `BODY_CACHE_TTL`,
`BODY_CACHE_MAX_ENTRIES`, `MAX_CACHED_ARTICLES_PER_SOURCE`,
`MAX_PERSISTED_SEEN_KEYS`, `CORPUS_COLLAPSE_RATIO`,
`ALLOW_CORPUS_DROP`.

---

## 11. Limites spécifiées

Ce ne sont pas des défauts à corriger mais des propriétés du système.

- **hrw.org renvoie 403** aux runners CI comme aux environnements
  d'agent. Les articles HRW sont archivés via une redirection Google News
  et notés **sur leur titre seul**. Aucun corps n'est récupérable.
- **Les URL Google News n'ont pas de corps** : constante
  `BODY_UNAVAILABLE_GOOGLE_NEWS`, articles marqués sans tentative.
- **Deux tiers du corpus n'ont ni corps ni résumé** (§2.2).
- **Le type `indetermine` est un aveu, pas un jugement** : « ni date ni
  corps récupérable ». L'exclure jetterait les deux tiers du corpus pour
  ce qu'on n'a pas réussi à récupérer.
- `find_terms()` borne la fin du terme inconditionnellement : un radical
  tronqué y est **inerte**. `contains_pattern()` (via `_borner`) ne borne
  la fin que pour les terminaisons latines. Les deux ne sont pas
  interchangeables.

## 12. Hors spécification

Points où le code ne définit pas de contrat, et où rien ne doit être
inféré :

- **Le périmètre éditorial** — les neuf constantes à `None` (§6.1). Tant
  qu'elles sont vides, le périmètre effectif est celui qu'encode
  `scoring.py`, qui est un défaut technique et non un choix validé.
- **La justesse du score.** Les tests garantissent la *stabilité* (snapshot
  de caractérisation) et des cas *nommés*, jamais que le classement est
  le bon. Aucun corpus labellisé par un humain ne sert de référence.
- `target_score` ne lit que `has_activist` / `has_journalist` :
  `TARGET_TERMS_V9` (scoring), `AVOCAT_TERMS` et `DETENU_TERMS`
  (catégorisation) ne l'alimentent pas. Une cible ajoutée ailleurs n'a
  aucun effet mesurable.
- `keywords.py::TARGET_TERMS_V9` est du code mort — `scoring.py` définit
  sa propre liste homonyme.

---

Pourquoi ces décisions ont été prises, et quelles alternatives ont été
écartées : voir `docs/HISTORY.md`.
