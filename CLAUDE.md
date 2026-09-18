# CLAUDE.md

## Architecture

Couches, du bas vers le haut. Une couche n'importe jamais une couche au-dessus d'elle.

- `matching.py` — primitives de correspondance. N'importe aucun module métier.
- `keywords.py` — vocabulaire partagé. Une liste, deux consommateurs.
- `scoring.py` et `categorisation.py` — importent `matching` + `keywords`, **jamais l'un l'autre**.
- `regles_editoriales.py` — applique des choix sur le dict de `categoriser()`. Ne détecte rien.
- `news_scanner.py` — orchestration. `archive.py` — persistance append-only.

Invariants :

- `categorisation.py` **décrit** (géographie, acteur, traitement), ne dit jamais si on s'y intéresse. `regles_editoriales.py` **décide**, ne détecte jamais.
- Les 9 constantes à `None` de `regles_editoriales.py` (`PERIMETRE_GEO`, `ACTEURS_RETENUS`, `AGE_MAXIMUM_JOURS`…) sont **réservées à l'utilisateur**. Ne jamais en deviner une. `None` = ce critère ne filtre pas.
- Un terme de vocabulaire qui doit servir au scoring **et** à la catégorisation va dans `keywords.py`. Y ajouter un terme sans vérifier les deux consommateurs est la cause de la moitié des trous corrigés ici.
- `decide_level` : F (page de rubrique) est décidé **en premier**, avant la géographie — une page pays nomme évidemment son pays. `D` n'est atteignable que si `regional_context` est **faux**.
- Un correctif d'extraction doit être doublé d'une fonction de rattrapage idempotente (cf. `nettoyer_corps`) câblée dans le bloc de maintenance de `news_scanner.py` : `merge_scanned` ne réécrit jamais une entrée archivée.
- Ne jamais toucher au déploiement RunPod ni à l'affichage du site sans demande explicite.

## Conventions

- **Auditer avant d'ajouter du vocabulaire.** Chercher le candidat dans `archive.jsonl` (titres **et** corps), compter les déclenchements justes, et rejeter sous ~80 % de précision. Chiffres dans le commentaire, au-dessus du terme.
- **Rejeter les mots qui désignent une population, garder ceux qui désignent un rôle.** `imam` oui, `muslim` non. `opposants` oui, `opposant` non (participe présent de *opposer*). `юрист` non (chroniques juridiques). `farmer` non (moissons chinoises).
- **Avant de retirer un terme**, mesurer ce que le retrait coûte en détections légitimes — pas seulement ce qu'il fait gagner.
- **Chaque candidat rejeté devient un test** dans `tests/test_scoring.py`, avec les chiffres de l'audit. C'est le seul garde-fou contre sa réintroduction.
- Énumérer les formes fléchies russes **une par une** dans les listes lues par `find_terms` (`несогласные`, `несогласных`, `несогласным`, `несогласными`). Une racine tronquée y est inerte (voir Pièges).
- Commentaires en français, au-dessus du bloc concerné, expliquant **pourquoi** et avec les chiffres mesurés. Pas de commentaire qui paraphrase le code.
- Messages de commit et PR en français, avec les chiffres de l'audit et l'impact avant/après.
- Branche de travail : `claude/salut-clf4oi`. Ne jamais pousser ailleurs.

## Commandes

```bash
python3 -m unittest discover              # ce que lance la CI — doit passer
python3 -m pytest -q                      # à lancer aussi, avant tout push
python3 tests/fixtures/rebuild_scoring_snapshot.py   # APRÈS avoir lu le diff
```

Mesure sur corpus réel — appliquer le même prétraitement que la production, sinon la mesure est fausse :

```python
from matching import looks_like_section_page
from text_utils import strip_boilerplate, strip_related_blocks
# ignorer les pages de rubrique, puis :
corps = strip_boilerplate(strip_related_blocks(body), source)
```

## Pièges

- **`find_terms` ≠ `contains_pattern`.** `find_terms` borne la fin du terme **inconditionnellement** : un radical tronqué (`депортаци`) y est totalement inerte, sans erreur. `contains_pattern` (via `_borner`) ne borne la fin que pour les terminaisons latines, donc les radicaux russes/persans y fonctionnent. Vérifier quel consommateur lit la liste avant d'y mettre une racine.
- **`\b` dans une chaîne Python non-raw** devient un octet backspace. Le motif compile et ne matche jamais. Générer via `repr()` sur une raw string, et vérifier de bout en bout sur des données réelles.
- **Ne jamais poser un plafond sur la valeur d'un seuil.** `min(score, 55)` avec `LEVEL_B_MIN_SCORE = 55` promeut au lieu de retenir (le test est `>=`). Utiliser `LEVEL_B_MIN_SCORE - 1`. Ce bug avait mis 85 des 102 articles de niveau B à exactement 55/100.
- **`target_score` ne lit que `has_activist` / `has_journalist`.** `TARGET_TERMS_V9`, `AVOCAT_TERMS`, `DETENU_TERMS` ne l'alimentent pas. Une cible ajoutée au mauvais endroit n'a aucun effet mesurable.
- **`keywords.py::TARGET_TERMS_V9` est du code mort** — `scoring.py` a sa propre copie locale du même nom. Éditer la mauvaise ne produit rien.
- **hrw.org renvoie 403** ici comme en CI : les articles HRW sont notés **sur leur titre seul**. Inutile de chercher à récupérer leur corps.
- **Lire le diff du harnais de caractérisation avant de régénérer le snapshot**, et rapporter qui monte et qui descend. Ne jamais le régénérer pour faire taire un test rouge.
- La CI doit installer `requirements.txt` exactement : un épinglage exigeant Python 3.11 est passé au vert et a cassé la production en 3.10.
- `CorpusCollapseError` sur un run manuel n'est pas une régression : le garde-fou compare au run précédent, et un déclenchement hors créneau collecte légitimement moins. Rien n'est publié, le site garde sa version.

## Collaboration avec moi

- Ingénieur expérimenté. Pas d'explication de concepts, pas de paraphrase du code, pas de récapitulatif de ce que je viens de lire.
- **Autonomie large sur l'exécution** : mesurer, auditer, coder, tester, commiter, ouvrir la PR, attendre la CI, merger. Je ne veux pas valider chaque étape.
- **M'arrêter et demander** si : une décision éditoriale se présente (périmètre, seuils, ce qui mérite d'être vu), une mesure montre une **dégradation réelle** (pas du bruit qui se redistribue entre niveaux bas), ou un changement touche la **formule de score** plutôt que le vocabulaire.
- Mes demandes sont courtes, en français, souvent sans ponctuation ni contexte. Elles contiennent un chiffre ou un symptôme observé sur le site ; le travail de diagnostic est à ta charge. Si je demande « une méthode », je veux la méthode **et** son application immédiate, pas un plan.
- Me rapporter en **chiffres avant/après** mesurés sur le corpus réel. Un correctif sans mesure n'est pas un correctif.
- Ne jamais remplir les constantes de `regles_editoriales.py` : ce sont mes décisions, pas les tiennes.

Contexte historique et justification des décisions d'architecture :
voir docs/HISTORY.md (à lire uniquement si une décision structurante est
remise en question).
