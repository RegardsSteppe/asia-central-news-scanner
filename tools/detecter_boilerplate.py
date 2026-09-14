"""
Génère boilerplate.py — le pied de page que chaque source recopie à
l'identique sous tous ses articles.

Le problème qu'il résout : le scoring lisait des titres d'AUTRES
articles. Le cas le plus net est Turkmen.News, dont les 796 caractères
de pied de page citent un prisonnier politique sous CHAQUE article, y
compris ceux sur le prix de la viande — deux d'entre eux ressortaient
en niveau A avec un score de 100. strip_related_blocks() traite ce cas
par marqueur ("Читайте также", "Recommended Stories"), mais un
marqueur par site ne passe pas à l'échelle : Asia-Plus termine par un
fil "Recent News" sans aucun marqueur, 24.kg par un bloc "Popular".

Le principe est mécanique et ne demande aucun vocabulaire : un texte
identique d'un article à l'autre d'une même source ne peut pas être le
contenu de CET article.

    python tools/detecter_boilerplate.py

Deux garde-fous, tirés d'une mesure et non d'une intuition :

  - Le QUORUM est une proportion, pas un nombre. Sans lui, Kommersant
    ressortait avec 4475 caractères partagés par 4 articles sur 180 —
    ce n'était pas un pied de page mais le même discours du Kremlin
    republié quatre fois. Exiger 20 % des articles de la source élimine
    ce cas sans toucher aux vrais pieds de page, qu'une majorité
    d'articles portent.

  - Le suffixe est ramené à une frontière de mot. La recherche
    dichotomique trouve la plus longue correspondance exacte, qui
    commence volontiers au milieu d'un mot ("ilipino Filipino
    French") : on ne retire que le mot entier.

Le fichier généré est relu à la main avant commit — c'est un artefact
de données, pas une boîte noire.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from text_utils import strip_related_blocks  # noqa: E402

SORTIE = RACINE / "boilerplate.py"
ARCHIVE = RACINE / "archive.jsonl"

# Un corps plus court que ça n'apprend rien sur le pied de page de sa
# source : il est probablement tronqué ou n'est pas un article.
CORPS_MINIMUM = 400

# En dessous, le "pied de page" détecté est une coïncidence (deux
# articles qui finissent par la même phrase banale).
SUFFIXE_MINIMUM = 120

# Au-dessus, on ne détecte plus un pied de page mais un article
# republié à l'identique.
SUFFIXE_MAXIMUM = 4000

MIN_ARTICLES = 4
MIN_PROPORTION = 0.20


def _plus_long_suffixe_stable(corps: list[str]) -> str:
    """
    Plus long suffixe commun porté par au moins le quorum de corps.

    Dichotomie sur la longueur : si k corps partagent leurs n derniers
    caractères, ils partagent aussi leurs n-1 derniers, donc la
    propriété est monotone et se cherche en log(n) au lieu de n.
    """
    quorum = max(MIN_ARTICLES, int(MIN_PROPORTION * len(corps)))
    if len(corps) < quorum:
        return ""

    bas = SUFFIXE_MINIMUM
    haut = min(SUFFIXE_MAXIMUM, min(len(c) for c in corps))
    meilleur = ""

    while bas <= haut:
        milieu = (bas + haut) // 2
        suffixe, occurrences = collections.Counter(
            corps_unique[-milieu:] for corps_unique in corps
        ).most_common(1)[0]

        if occurrences >= quorum:
            meilleur = suffixe
            bas = milieu + 1
        else:
            haut = milieu - 1

    return _borner_sur_un_mot(meilleur)


def _borner_sur_un_mot(suffixe: str) -> str:
    """
    Ramène le suffixe au début du premier mot entier qu'il contient.

    La dichotomie coupe au caractère près, donc au milieu d'un mot une
    fois sur deux. Retirer "ilipino Filipino French..." laisserait un
    "F" orphelin collé à la fin du texte utile.
    """
    if not suffixe:
        return ""

    espace = suffixe.find(" ")
    if espace == -1:
        return ""

    return suffixe[espace + 1:].strip()


def collecter(chemin: Path) -> dict[str, list[str]]:
    par_source: dict[str, list[str]] = collections.defaultdict(list)

    with chemin.open(encoding="utf-8") as handle:
        for ligne in handle:
            ligne = ligne.strip()
            if not ligne:
                continue
            article = json.loads(ligne)
            corps = strip_related_blocks(article.get("body") or "")
            if len(corps) > CORPS_MINIMUM:
                par_source[article.get("source") or ""].append(corps)

    return par_source


def main() -> None:
    if not ARCHIVE.exists():
        raise SystemExit(f"archive introuvable : {ARCHIVE}")

    par_source = collecter(ARCHIVE)

    table: dict[str, str] = {}
    rapport: list[tuple[int, int, int, str]] = []

    for source, corps in sorted(par_source.items()):
        if not source or len(corps) < MIN_ARTICLES:
            continue
        suffixe = _plus_long_suffixe_stable(corps)
        if len(suffixe) < SUFFIXE_MINIMUM:
            continue
        porteurs = sum(1 for c in corps if c.endswith(suffixe))
        table[source] = suffixe
        rapport.append((len(suffixe), porteurs, len(corps), source))

    lignes = [
        '"""',
        "boilerplate.py — GÉNÉRÉ, ne pas éditer à la main.",
        "",
        "Produit par tools/detecter_boilerplate.py à partir de",
        "archive.jsonl : pour chaque source, le pied de page que ses",
        "articles recopient à l'identique.",
        "",
        "Un texte identique d'un article à l'autre d'une même source ne",
        "peut pas être le contenu de cet article-là. C'est ce qui",
        "permet de le retirer sans connaître un seul mot de vocabulaire.",
        '"""',
        "",
        "# nom de la source -> suffixe à retirer de ses corps",
        "BOILERPLATE_PAR_SOURCE: dict[str, str] = {",
    ]
    for _, _, _, source in sorted(rapport, reverse=True):
        lignes.append(f"    {source!r}: {table[source]!r},")
    lignes.append("}")
    lignes.append("")

    SORTIE.write_text("\n".join(lignes), encoding="utf-8")

    total = sum(n * p for n, p, _, _ in rapport)
    print(f"{len(table)} sources -> {SORTIE}")
    print(f"{total} caractères de pied de page retirés du corpus")
    print()
    for n, p, tot, source in sorted(rapport, reverse=True):
        print(f"  {n:5d} car | {p:4d}/{tot:<4d} | {source[:40]}")


if __name__ == "__main__":
    main()
