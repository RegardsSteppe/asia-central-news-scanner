# Historique des décisions — asia-central-news-scanner

Ce fichier n'est pas une documentation d'usage. C'est le registre des
décisions structurantes, des alternatives écartées et des erreurs déjà
commises. Il ne se lit que quand une décision d'architecture est remise
en question — pour savoir si l'argument qui l'a fondée tient toujours.

Pour les instructions opérationnelles, voir `CLAUDE.md`.

---

## 1. L'objectif, et son déplacement

### Point de départ

Un scanner de presse multi-sources sur l'Asie centrale, le Caucase et le
Xinjiang : agrégation de ~150 flux (presse locale, ONG droits humains,
médias d'État russes et chinois, think tanks), notation de chaque
article, catégorisation descriptive, publication d'un site statique.

L'objectif initial était **opérationnel** : que le pipeline tourne de bout
en bout sans perdre de données. Les premiers travaux le montrent — rendre
le téléchargeur de corps reprenable, corriger l'extraction qui attrapait
le mauvais bloc HTML, empêcher le throttle Google News d'affamer le pool
principal.

### Le déplacement

L'objectif s'est déplacé vers la **justesse de la détection** quand
l'archive append-only est devenue exploitable comme corpus de mesure.

La bascule est nette et datable : à partir du moment où
`archive.jsonl` a contenu assez d'articles (13 366 aujourd'hui) pour
qu'une requête dessus soit statistiquement parlante, la question a cessé
d'être « est-ce que ça tourne » pour devenir « est-ce que ça voit ».

La méthode de travail s'est inversée en conséquence :

1. Mesurer un angle mort sur le corpus réel — pas l'imaginer.
   Exemples réels : « 4368 des 9556 entrées archivées n'ont aucune
   géographie », « 221 des 251 articles HRW en zone de veille restent en
   niveau E », « violence_physique ne ressort que 14 fois sur 4000 ».
2. Isoler la cause mécanique, pas le symptôme.
3. Auditer chaque candidat de correction sur les **titres réellement
   déclenchés** dans le corpus, et rejeter ceux dont la précision est
   trop basse.
4. Écrire les tests, **y compris les candidats rejetés** comme garde-fous.
5. Lire le diff du harnais de caractérisation avant de régénérer son
   snapshot.
6. Mesurer avant/après en chiffres, et rapporter.

### Le signal de rendement décroissant

Il faut le noter explicitement, parce qu'il conditionne la suite : les
gains vont en décroissant vite.

| Correctif | Articles concernés |
|---|---|
| Géographie manquante alors que le pays est nommé | ~4368 |
| Pages de navigation classées comme articles | ~88 + fond |
| Vocabulaire français HRW (répression nue + cibles) | 221 → 93 restants |
| Vocabulaire russe HRW | 93 |
| Géographie allemande / kazakhe / tadjike / ouzbèke native | dizaines |
| Cibles manquantes (lawyer, POW, prisonnier politique FR) | 13 |

Le puits n'est pas tari, mais il faut creuser plus profond pour moins
d'eau. La suite utile n'est probablement plus dans le vocabulaire (voir
§5, dette assumée).

---

## 2. Décisions d'architecture

### 2.1 `matching.py` — une couche de détection partagée

**Décision.** Extraire dans un module unique toutes les primitives de
correspondance : `normalize`, `find_terms`, `contains_pattern`,
`relation_present`, `phrase_present`, `looks_like_section_page`,
`slugify`, `resolve_language`.

**Pourquoi.** `scoring.py` et `categorisation.py` avaient chacun leur
propre logique. Elles avaient déjà divergé : un article pouvait sortir
parfaitement décrit côté catégorisation (`acteur=opposant`,
`traitement=pression_administrative`) et rester invisible côté scoring,
faute que les deux reconnaissent les mêmes choses.

**Alternative écartée.** Laisser les deux implémentations vivre
séparément et les synchroniser manuellement. Rejetée : c'est exactement
ce qui se passait, et la dérive était déjà là. Une convention de
synchronisation que rien ne vérifie n'est pas une architecture.

**Ce qui reste imparfait.** La couche de détection est partagée, le
**vocabulaire** ne l'est qu'à moitié (voir 2.2 et §5).

### 2.2 `keywords.py` — une liste, deux consommateurs

**Décision.** `ACTIVIST_TERMS`, `JOURNALIST_TERMS`,
`HUMAN_RIGHTS_DEFENDER_TERMS`, les listes géographiques, etc. vivent dans
`keywords.py` et sont importées par `scoring.py` **et**
`categorisation.py`.

**Pourquoi.** Même raisonnement qu'en 2.1, appliqué aux données. Cas
réel : le blogueur est la figure la plus réprimée en Ouzbékistan ;
`TARGET_TERMS_V9` (scoring) le connaissait, `JOURNALIST_TERMS`
(catégorisation) non — donc la catégorisation le ratait
systématiquement.

**Corollaire non tenu.** Plusieurs listes de cibles vivent encore
**dans `categorisation.py`** : `DETENU_TERMS`, `AVOCAT_TERMS`,
`CROYANT_TERMS`, `MINORITE_SEXUELLE_TERMS`, `UNIVERSITAIRE_TERMS`,
`ARTISTE_TERMS`, `MIGRANT_TERMS`, `ECOLOGISTE_TERMS`,
`SYNDICALISTE_TERMS`, `FEMME_TERMS`, `MINORITE_ETHNIQUE_TERMS`,
`CITOYEN_TERMS`. Le scoring ne les voit pas. C'est précisément le bug
qu'a exposé la dernière itération : « Azerbaijan: Armenian POWs Abused in
Custody » ressortait `acteur=detenu` côté catégorisation et
`target_score=0` côté scoring.

### 2.3 Les faits séparés des choix : `categorisation.py` / `regles_editoriales.py`

**Décision.** `categorisation.py` décrit un article (géographie, acteur,
traitement, type) sans jamais dire si on s'y intéresse.
`regles_editoriales.py` ne détecte rien : il applique des choix
(périmètre géographique, acteurs retenus, âge maximum…) sur le dict que
`categoriser()` renvoie.

**Pourquoi.** Changer d'avis sur le périmètre éditorial ne doit jamais
obliger à retoucher le moteur de détection.

**Alternative écartée.** Encoder le périmètre directement dans
`classify_article`. Rejetée : le périmètre est une opinion, la détection
est un fait. Les mélanger rend impossible de changer l'un sans risquer
l'autre, et impossible de re-évaluer un corpus déjà catégorisé sous de
nouvelles règles sans le re-scanner.

**Sous-décision importante : aucune valeur devinée.** Les 9 constantes
qui encodent un vrai choix éditorial sont laissées à `None`, avec les
options listées en commentaire. Tant qu'une constante est `None`,
`est_pertinent()` **ne filtre pas** sur ce critère — elle ne bloque rien
plutôt que d'appliquer un choix que personne n'a fait.

C'est une décision volontaire et elle a un coût, documenté en §5 : tant
qu'elles sont vides, c'est le scoring qui fait office de politique
éditoriale par défaut.

### 2.4 Le harnais de caractérisation

**Décision.** `tests/test_scoring_characterization.py` rejoue 478
articles réels (`tests/fixtures/scoring_corpus.json`) contre un snapshot
figé (`scoring_snapshot.json`) et compare score, niveau, raisons,
pertinence, thème, priorité et une empreinte des ~60 signaux.

**Pourquoi.** Un test unitaire vérifie un cas connu. Il ne dit rien des
477 autres articles qu'un ajout de vocabulaire fait bouger. Le snapshot
transforme chaque changement de scoring en **diff lisible**.

**Alternative écartée.** Se contenter de tests unitaires ciblés.
Rejetée : le mode de défaillance dominant sur ce code n'est pas « le cas
que je viens d'écrire est faux », c'est « mon ajout a déplacé 40 articles
que je n'ai pas regardés ».

**Règle qui en découle.** Le snapshot se régénère
(`tests/fixtures/rebuild_scoring_snapshot.py`) **après** lecture du diff,
jamais avant, et jamais pour faire taire un test rouge.

### 2.5 L'archive append-only

**Décision.** `archive.jsonl`, append-only, une entrée par URL, enrichie
au fil des runs (corps, dates, nettoyages) sans jamais réécrire l'entrée
existante par un simple re-scan. Le site publie le **corpus complet**, pas
le scan du jour.

**Pourquoi.** Les flux RSS ne portent que les items récents. Sans
archive, le corpus disponible pour la mesure se serait réduit à une
fenêtre glissante de quelques jours, et tout le travail de justesse
décrit en §1 aurait été impossible.

**Conséquence.** Tout correctif d'extraction doit s'accompagner d'une
fonction de rattrapage idempotente (`nettoyer_corps`, `nettoyer_titres`)
câblée dans le bloc de maintenance de `news_scanner.py` : sinon le
correctif ne s'applique qu'aux futures entrées et l'archive garde ses
données abîmées pour toujours.

### 2.6 La CI avant le merge

**Décision.** `tests.yml`, déclenché sur `pull_request` et sur `push`
vers `main`, installe exactement `requirements.txt` et lance
`python -m unittest discover`.

**Pourquoi.** Les tests ne tournaient que dans `news-scanner.yml`,
c'est-à-dire **après** le merge sur `main`. Une pull request ne pouvait
pas être rouge, et une régression n'était visible qu'une fois en
production.

**Détail qui a coûté un run.** L'étape d'installation posait des versions
libres au lieu de `requirements.txt`. Un épinglage exigeant Python 3.11
est donc passé au vert en CI et a cassé le run #142, où la production
tourne en 3.10.

### 2.7 Le niveau F, décidé avant la géographie

**Décision.** Les pages de rubrique et le mobilier de site (« Burkina
Faso » chez CPJ, « Cookie Statement » chez Amnesty, « Donate Now »,
éditions du Guardian) sortent en niveau F, et **ce test passe en premier,
avant même le contexte régional**.

**Pourquoi l'ordre compte.** Une page pays mentionne évidemment son pays :
les tests de géographie la valideraient à tort.

**Alternative écartée.** Les classer en E. Rejetée : E signifie « article
sans intérêt », ce qui est faux d'une page qui n'est pas un article. Et
comme certaines sont longues et bien remplies, elles remontaient parfois
au-dessus de vrais sujets.

### 2.8 Le garde-fou anti-effondrement

**Décision.** `check_corpus_not_collapsed()` lève `CorpusCollapseError`
et **ne publie rien** si le scan collecte moins de la moitié du run
précédent. Le site garde sa version complète.

**Pourquoi.** Un flux en panne, un 403 généralisé ou une erreur de parsing
pouvait publier un site vide par-dessus un site complet.

**Sa métrique est discutable** — voir §5.

### 2.9 Les niveaux A-F, et le trou entre D et E

Structure actuelle, dans l'ordre d'évaluation de `decide_level()` :

- **F** — page de rubrique / mobilier de site. Décidé en premier.
- **D** — hors zone de veille (`regional_context = False`) mais portant un
  vrai signal droits humains (`global_hr_signal`) : HRW sur un défenseur
  au Rwanda.
- **A** — score ≥ 75 **et** un signal de confirmation.
- **B** — score ≥ 55.
- **C** — score ≥ 35.
- **E** — tout le reste.

**Conséquence structurelle, découverte tard.** `D` n'est atteignable que
si `regional_context` est **faux**. Un article *dans* la zone de veille
dont le score reste sous 35 n'a aucun palier intermédiaire : il tombe
directement en E, à côté du sport et de la météo. C'est ce qui explique
que 585 articles HRW — géographie confirmée, ancrage répressif confirmé —
se retrouvent dans le même seau que le bruit.

Ce n'est pas un bug corrigé : c'est un constat, et une décision reportée
(§5).

---

## 3. Impasses et régressions — causes racines

### 3.1 Les plafonds posés sur les seuils

**Symptôme.** Un changement d'indicatif téléphonique, la mort d'un acteur
et un trafiquant de MDMA en niveau B.

**Cause racine.** Le code écrivait `score = min(score, 55)` là où
`LEVEL_B_MIN_SCORE = 55`, et le test de niveau est `>=`. Un plafond posé
**sur** un seuil ne retient rien : il **promeut** l'article exactement au
niveau qu'on voulait lui refuser.

**Mesure avant correction.** 85 des 102 articles de niveau B étaient à
exactement 55/100 ; 41 des 106 en C à exactement 35/100.

**Correctif.** `LEVEL_B_MIN_SCORE - 1`. Un cran en dessous, pour que le
plafond fasse ce que son nom dit.

**Leçon transférable.** Toute constante de plafond doit être comparée aux
constantes de seuil, pas choisie « au jugé ».

### 3.2 Les racines tronquées, inertes sans le dire

**Symptôme.** Des radicaux russes ajoutés en toute bonne foi
(`"депортаци"`, `"несогласн"`) ne matchaient rien, sans aucune erreur.

**Cause racine.** Asymétrie non documentée entre deux constructeurs de
regex du même module :

- `_terms_alternation()` (derrière **`find_terms`**) borne la fin
  **inconditionnellement** : `(?<!\w)(?:t1|t2|…)(?!\w)`. Un radical
  tronqué y est totalement inerte.
- `_borner()` (derrière **`contains_pattern`** / `_alternation_pattern`)
  ne borne la fin **que si le terme s'achève sur une lettre latine**,
  précisément pour que les radicaux russes et persans tronqués continuent
  de matcher leurs flexions.

Deux fonctions du même fichier, deux sémantiques opposées, un appelant
qui ne peut pas le deviner.

**Correctif retenu.** Énumérer les formes fléchies une par une dans les
listes consommées par `find_terms` (`"несогласные"`, `"несогласных"`,
`"несогласным"`, `"несогласными"`), et le dire en commentaire à chaque
fois.

**Alternative existante et sous-utilisée.** `find_terms_with_stems()`
accepte des couples (terme, motif de racine). Presque personne ne s'en
sert. Voir §5.

### 3.3 Le `\b` avalé par une chaîne non-raw

**Symptôme.** Un motif généré, compilé sans erreur, qui ne matche jamais.

**Cause racine.** Écrire une regex contenant `\b` dans une chaîne Python
**non-raw** (triple-quotes comprises) la transforme silencieusement en
octet backspace `\x08`.

**Règle.** Un bloc de regex généré par programme se produit via `repr()`
sur une *raw string*, ou s'écrit directement avec un outil qui ne
réinterprète pas les échappements — et se vérifie de bout en bout sur
des données réelles avant d'être cru.

### 3.4 Le scoring lisait les titres des voisins

**Symptôme.** Des articles notés sur un sujet qu'ils ne traitaient pas.

**Cause racine.** L'extraction de corps embarquait les blocs « articles
liés » / « à lire aussi ». Le scoring voyait donc les titres voisins
comme du contenu de l'article.

**Correctif.** `strip_related_blocks()` + `strip_boilerplate()`, avec
détection du boilerplate **par répétition entre articles d'une même
source** plutôt qu'un marqueur codé en dur par site — un marqueur par
site ne passe pas à l'échelle de 150 sources.

**Conséquence de méthode.** Tout script de mesure sur l'archive doit
appliquer `strip_boilerplate(strip_related_blocks(corps), source)` avant
`classify_article`, sinon il ne mesure pas la production.

### 3.5 Les candidats de vocabulaire rejetés — une seule cause racine

Cinq rejets, cinq audits, un seul motif : **un mot qui désigne une
population ou un usage anodin, pas un rôle pour lequel on se fait
réprimer.**

| Candidat | Mesure | Verdict |
|---|---|---|
| `muslim` | catégorie de population | rejeté (`imam` gardé : rôle) |
| `opposant` (singulier FR) | 1 faux sur 2 — participe présent de *opposer* : « une querelle de voisinage opposant un éleveur au maire » | rejeté (le pluriel est sûr, un participe présent étant invariable) |
| `эксплуатация` | « mise en service » 9 fois sur 11 (« сдали в эксплуатацию ») | rejeté |
| `юрист` / `адвокат` nus | 2 titres HR sur 12-16 — chroniques juridiques grand public (divorce, stationnement, achat immobilier) | rejeté |
| `farmer` / `фермер` nus | 3-4 justes sur 8 — moissons chinoises, agriculture au Kosovo | rejeté |
| `disappeared` / `missing after` nus | 3 faux sur 5 — mer d'Aral, ferry à Bali | rejeté (forme qualifiée « disparition forcée » gardée) |
| `нападение` | sens militaire/criminel dominant | rejeté |
| `militant` (EN) | 7 articles sur 7 = insurgé armé (Houthis, CENTCOM) | **retiré** après coup |
| `press freedom`, `мусдود`, `того` | génériques | rejetés |

**Deux leçons distinctes.**

1. *La leçon « rôle contre population »* : on garde ce pour quoi on se
   fait arrêter, on écarte ce qu'on est.
2. *La leçon « disappeared »* : avant de **retirer** un terme, vérifier
   ce que le retrait coûte en détections légitimes. `militant` a été
   retiré seulement après avoir constaté que les 7 déclenchements étaient
   tous faux.

**Chaque rejet est devenu un test.** C'est ce qui empêche un futur agent
de « corriger » un trou en réintroduisant un candidat déjà mesuré et
écarté.

### 3.6 Le 403 de hrw.org

**Constat.** hrw.org renvoie HTTP 403 aux runners GitHub Actions **et** à
cet environnement. Les articles HRW sont archivés via une redirection
Google News, dont le corps n'existe pas non plus.

**Conséquence permanente, pas un bug à corriger.** Les articles HRW sont
notés **sur leur seul titre**. Tout vocabulaire destiné à améliorer HRW
doit fonctionner sur un titre nu — d'où l'effort disproportionné sur les
formulations exactes des titres de rapports (« Répression létale au
Karakalpakstan », « Ill-Treatment of Detainees Documented »).

### 3.7 `CorpusCollapseError` sur un déclenchement manuel

**Symptôme.** Le run manuel de `news-scanner.yml` lancé après le merge de
PR #108 a échoué : `6532 articles contre 13366 au run précédent (seuil :
6683)`.

**Cause racine.** Aucune — ni du code, ni du changement. Le garde-fou a
fonctionné comme prévu : ce cycle de collecte instantané a récupéré
moitié moins d'items que le précédent (fluctuation normale des flux RSS
selon l'heure). Rien n'a été publié, le site a gardé sa version complète.

**Mais la métrique est discutable** — voir §5.

---

## 4. Ce qui a été essayé et abandonné

**Restreindre la table d'audit du site au niveau D.** Commité puis
reverté le jour même (`d6f251e` → `16df342`).

**`fetch_all_bodies.py` comme prérequis de la vérité terrain.** Abandonné :
la comparaison devait être utile **sans** labellisation humaine
préalable, sinon rien ne pouvait avancer.

**Télécharger les URL Google News.** Abandonné : leur corps n'existe pas
structurellement. Constante `BODY_UNAVAILABLE_GOOGLE_NEWS`, et les
articles sont marqués sans tentative de téléchargement.

---

## 5. Dette assumée et décisions reportées

### 5.1 `target_score` ne voit qu'un tiers des cibles — dette assumée

**État.** `target_score` est calculé uniquement à partir de
`has_activist` / `has_journalist` (plus un test littéral sur
`civil society` / `ngo`). Or :

- `TARGET_TERMS_V9` (dans `scoring.py`) contient `lawyer`, `адвокат`,
  `professor`, `writer`, `poet`, `artist`, `political prisoner`,
  `detainee`… et **n'alimente pas `target_score`** — il ne sert qu'à
  `target_repression_relation`, consommé ailleurs.
- `DETENU_TERMS`, `AVOCAT_TERMS`, `MINORITE_SEXUELLE_TERMS` et consorts
  vivent dans `categorisation.py` et sont **invisibles** au scoring.

**Contournement retenu (PR #108), et pourquoi il est laid.** `pow`,
`pows`, `prisoner of war`, `военнопленный` et `lawyer` ont été ajoutés à
**`ACTIVIST_TERMS`**, parce que c'est le seul canal qui alimente
réellement `target_score`. Sémantiquement, un prisonnier de guerre n'est
pas un activiste. C'est un mensonge de nommage, assumé pour éviter un
changement de formule au rayon d'impact large.

**Le correctif propre, non fait.** Ajouter une branche
`elif regional_context and target_repression_relation: target_score = 15`
— `target_repression_relation` exige déjà la **co-occurrence** d'une cible
et d'une action répressive explicite, donc c'est bien plus sûr qu'une
mention nue. Non fait parce que c'est un changement de formule de score,
pas un ajout de vocabulaire : il faut une mesure avant/après complète et
une validation éditoriale.

### 5.2 `keywords.py::TARGET_TERMS_V9` est du code mort

`scoring.py` définit sa **propre** `TARGET_TERMS_V9` en local (ligne ~275)
et n'importe jamais celle de `keywords.py` (ligne ~2517). Deux listes, le
même nom, aucun lien. Éditer la mauvaise ne produit aucun effet et aucune
erreur. Non nettoyé pour ne pas mélanger un nettoyage à un correctif
mesuré.

### 5.3 Les 9 constantes éditoriales à `None`

`PERIMETRE_GEO`, `GEO_ROLE_MINIMUM`, `ACTEUR_ROLE_MINIMUM`,
`TRAITEMENT_ROLE_MINIMUM`, `ACTEURS_RETENUS`, `TRAITEMENTS_RETENUS`,
`TYPES_EXCLUS`, `AGE_MAXIMUM_JOURS`, `EXIGER_RELATION_ACTEUR_TRAITEMENT`.

**Réservées à l'utilisateur, à ne jamais remplir d'initiative.**

**Coût réel, à énoncer clairement.** Tant qu'elles sont vides, le
périmètre éditorial effectif est celui qu'encode `scoring.py`
(`regional_context = Asie centrale OU Caucase OU Ouïghours`, seuils 75 /
55 / 35). Autrement dit : **on optimise une fonction de score dont
l'objectif n'a jamais été validé.** C'est l'angle mort le plus coûteux du
projet.

### 5.4 Le seuil du garde-fou compare deux choses différentes

`check_corpus_not_collapsed` compare le nombre d'articles **collectés
dans ce cycle** au nombre du run précédent. Un déclenchement manuel hors
créneau habituel collecte légitimement moins, et échoue. Le garde-fou est
bon ; sa métrique de comparaison mériterait d'être une moyenne glissante
plutôt que le run n-1.

### 5.5 Trous mesurés, non investigués

- **Fararu (persan) : 757 des 821 articles à score exactement 0.**
  Score exactement nul = signature d'un échec **structurel** (langue mal
  résolue, géographie absente du vocabulaire persan), pas de contenu
  inintéressant. Même signature que les trous allemand / kazakh / tadjik
  / ouzbek déjà corrigés.
- **`primary_lgbt_pressure` ne reconnaît que `lgbt` et `queer`** — pas
  `gay`, `геев`, `гомосексуальные мужчины`. Il ne fait que relever un
  plafond, donc l'effet serait limité, mais le trou est réel.
- **Le palier manquant entre D et E** pour les articles *en zone* dont le
  score reste sous 35 (§2.9). C'est la vraie cause de la taille du seau E.

### 5.6 Aucune vérité terrain labellisée

`verite_terrain.py` existe, un juge LLM existe (`juge_llm.py`,
déploiement RunPod), mais **aucun corpus labellisé par l'utilisateur**
n'a jamais servi de référence. Toutes les mesures de ce projet disent
« le score monte », jamais « le score a raison ». Les deux ne sont pas la
même chose, et rien ne le vérifie aujourd'hui.

---

## 6. Repères chronologiques

| Étape | Contenu |
|---|---|
| Fiabilité du pipeline | reprise sur timeout, extraction de corps, throttle Google News |
| Séparation faits / choix | `categorisation.py` + `regles_editoriales.py`, câblés dans le scan |
| Couche partagée | `matching.py`, puis `keywords.py` comme vocabulaire commun |
| Durcissement | garde-fou d'effondrement, vérification de schéma d'URL, CI sur PR, dépendances épinglées |
| Archive | `archive.jsonl` append-only, publication du corpus complet, rattrapage des corps |
| Mesure | harnais de caractérisation sur 478 articles réels |
| Justesse — géographie | pays nommés, Haut-Karabakh, Abkhazie, allemand, kazakh/tadjik/ouzbek natifs |
| Justesse — pages de rubrique | niveau F, reconnaissance au-delà de l'égalité de slug |
| Justesse — vocabulaire HRW | français puis russe, avec le piège des racines tronquées |
| Justesse — extraction | boilerplate par répétition, signature/chapô collés au titre |
| Justesse — cibles | lawyer, POW, prisonnier politique FR (PR #108) |
