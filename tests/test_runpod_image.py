"""
L'image RunPod ne contient qu'une poignée de fichiers, listés à la main
dans le Dockerfile. Un refactor qui ajoute une dépendance à scoring.py
casse donc l'endpoint en silence : rien dans la CI ne construit l'image
ni n'importe le handler avec ce sous-ensemble de fichiers.

Arrivé pour de vrai le 2026-09-13 : l'extraction de matching.py a laissé
l'image incapable de démarrer (ModuleNotFoundError au premier import),
et personne ne l'aurait su avant le prochain déploiement.

Ce test compare la liste du Dockerfile à la fermeture transitive réelle
des imports du handler.
"""

import ast
import re
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

POINT_ENTREE = "rp_handler"

# Chaque image et ce qu'elle doit pouvoir faire tourner en plus du
# handler. L'image minimale n'embarque aucun LLM (mode judge
# indisponible, et c'est voulu) ; Dockerfile.juge l'ajoute.
IMAGES = {
    "Dockerfile": (),
    "Dockerfile.juge": ("juge_llm",),
}


def modules_locaux() -> set[str]:
    return {chemin.stem for chemin in RACINE.glob("*.py")}


def imports_directs(module: str) -> set[str]:
    """
    Modules locaux importés par `module` AU NIVEAU MODULE.

    Les imports placés dans une fonction sont volontairement exclus :
    ce sont des dépendances optionnelles (rp_handler importe juge_llm
    dans le corps du mode judge, précisément pour que l'image minimale
    tourne sans LLM). Seuls les imports du niveau module font échouer
    le démarrage du conteneur, et c'est ce que ce test protège — les
    extras sont déclarés image par image dans IMAGES.
    """
    source = (RACINE / f"{module}.py").read_text(encoding="utf-8")
    arbre = ast.parse(source)
    locaux = modules_locaux()
    trouves = set()

    a_visiter = list(arbre.body)
    while a_visiter:
        noeud = a_visiter.pop()

        if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue

        if isinstance(noeud, ast.Import):
            for alias in noeud.names:
                racine = alias.name.split(".")[0]
                if racine in locaux:
                    trouves.add(racine)
        elif isinstance(noeud, ast.ImportFrom) and noeud.module:
            racine = noeud.module.split(".")[0]
            if racine in locaux:
                trouves.add(racine)
        else:
            # try/if/with au niveau module (ex. l'import optionnel de
            # stop_words) : leur contenu compte encore comme module.
            for champ in ("body", "orelse", "finalbody", "handlers"):
                a_visiter.extend(getattr(noeud, champ, []) or [])

    return trouves


def fermeture_imports(depart: str) -> set[str]:
    vus = {depart}
    a_voir = [depart]

    while a_voir:
        module = a_voir.pop()
        for dependance in imports_directs(module):
            if dependance not in vus:
                vus.add(dependance)
                a_voir.append(dependance)

    return vus


def fichiers_copies(dockerfile: str) -> set[str]:
    """Modules Python listés dans les instructions COPY d'un Dockerfile."""
    contenu = (RACINE / dockerfile).read_text(encoding="utf-8")
    copies = set()

    for ligne in contenu.splitlines():
        ligne = ligne.strip()
        if not ligne.upper().startswith("COPY "):
            continue
        for morceau in re.findall(r"[\w./-]+\.py", ligne):
            copies.add(Path(morceau).stem)

    return copies


class DockerfileCoversImportsTests(unittest.TestCase):
    def test_every_imported_module_is_copied_into_each_image(self):
        for dockerfile, extras in IMAGES.items():
            with self.subTest(image=dockerfile):
                requis = set(fermeture_imports(POINT_ENTREE))
                for extra in extras:
                    requis |= fermeture_imports(extra)

                manquants = sorted(requis - fichiers_copies(dockerfile))

                self.assertEqual(
                    manquants,
                    [],
                    f"{dockerfile} ne copie pas {manquants} — "
                    "l'endpoint RunPod planterait au démarrage. "
                    "Ajoutez-les à la ligne COPY.",
                )

    def test_the_handler_itself_is_copied(self):
        for dockerfile in IMAGES:
            with self.subTest(image=dockerfile):
                self.assertIn(POINT_ENTREE, fichiers_copies(dockerfile))

    def test_no_image_carries_the_full_scanner(self):
        # L'intérêt de ces images : pas de scraping, pas de génération de
        # site. Si news_scanner y entrait, c'est que le handler a dérivé.
        for dockerfile in IMAGES:
            with self.subTest(image=dockerfile):
                copies = fichiers_copies(dockerfile)
                for lourd in ("news_scanner", "article_ingestion", "synthesis"):
                    self.assertNotIn(
                        lourd, copies, f"{lourd} n'a rien à faire dans {dockerfile}"
                    )

    def test_minimal_image_stays_free_of_the_llm(self):
        # Sinon chaque scoring déterministe paierait le poids du modèle.
        self.assertNotIn("juge_llm", fichiers_copies("Dockerfile"))


if __name__ == "__main__":
    unittest.main()
