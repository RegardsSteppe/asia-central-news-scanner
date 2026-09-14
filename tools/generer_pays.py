"""
Génère pays_monde.py — la table "terme -> pays" pour tous les pays du
monde, en anglais, français et russe.

Écrite à la main, cette table ferait des centaines de lignes que
personne ne relirait et que rien ne tiendrait à jour. Elle est donc
dérivée de pycountry (norme ISO 3166-1 et ses traductions officielles)
par ce script, lancé à la demande. pycountry n'est PAS une dépendance
du scanner : seul le fichier généré l'est.

    python tools/generer_pays.py

Ce que ce script ne sait pas faire, et que categorisation.py garde donc
à la main : la morphologie russe (Украина/Украины/Украине...) et les
formes familières ("Kirghizie", "Ouzbékistan" translittéré). Les listes
curées de la zone de veille restent prioritaires sur cette table.
"""

from __future__ import annotations

import gettext
import re
import sys
import unicodedata
from pathlib import Path

import pycountry

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "pays_monde.py"

# Noms trop ambigus hors contexte pour être cherchés tels quels.
# Vérifiés sur le corpus réel : ils désignent bien plus souvent autre
# chose qu'un pays.
AMBIGUS = {
    "jordan",      # prénom, et joueur de football
    "chad",        # prénom anglophone
    "guinea",      # cochon d'Inde, et surtout inclus dans Papouasie-
                   # Nouvelle-Guinée / Guinée équatoriale / Guinée-Bissau
    "turkey",      # l'oiseau — la Turquie est déjà curée à la main
    "georgia",     # État américain — la Géorgie est déjà curée
    "mali",        # "Mali" est aussi un mot courant en russe translittéré
}

# Traductions écartées nommément : le nom du pays dans cette
# langue-là est un mot courant. Mesuré sur le corpus réel plutôt que
# supposé — "того" déclenchait 446 articles, contre 172 pour le
# terme légitime suivant ("пакистан").
TRADUCTIONS_AMBIGUES = {
    "того",   # Togo en russe = génitif de "тот" ("de celui-là")
}

# Pays déjà traités à la main dans categorisation.py, avec leur
# morphologie : on ne les regénère pas pour ne pas écraser ce travail.
DEJA_CURES = {
    "KZ", "UZ", "KG", "TJ", "TM", "AZ", "AM", "GE",
    "IR", "AF", "RU", "UA", "CN", "BY", "TR", "MD",
}


def _slug(nom: str) -> str:
    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", nom)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "_", sans_accent.lower()).strip("_")


def _normaliser(terme: str) -> str:
    return " ".join(terme.lower().split())


def construire() -> tuple[dict[str, str], dict[str, str]]:
    fr = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["fr"])
    ru = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["ru"])

    termes: dict[str, str] = {}
    libelles: dict[str, str] = {}

    for pays in pycountry.countries:
        if pays.alpha_2 in DEJA_CURES:
            continue

        nom_fr = fr.gettext(pays.name)
        cle = _slug(nom_fr)

        if not cle:
            continue

        libelles[cle] = nom_fr

        formes = {pays.name, nom_fr, ru.gettext(pays.name)}
        formes.add(getattr(pays, "common_name", "") or "")
        formes.add(getattr(pays, "official_name", "") or "")

        for forme in formes:
            forme = _normaliser(forme)
            # Les noms d'un seul caractère ou trop courts matchent trop.
            if len(forme) < 4 or forme in AMBIGUS:
                continue
            if forme in TRADUCTIONS_AMBIGUES:
                continue
            # Premier arrivé gagne : évite qu'un nom officiel partagé
            # ("Republic of...") ne réécrive un pays déjà associé.
            termes.setdefault(forme, cle)

    return termes, libelles


def ecrire(termes: dict[str, str], libelles: dict[str, str]) -> None:
    lignes = [
        '"""',
        "pays_monde.py — GÉNÉRÉ, ne pas éditer à la main.",
        "",
        "Produit par tools/generer_pays.py à partir de pycountry",
        "(ISO 3166-1 et ses traductions officielles fr/ru).",
        "",
        "La morphologie russe et les formes familières des pays de la zone",
        "de veille restent curées à la main dans categorisation.py, qui a",
        "la priorité sur cette table.",
        '"""',
        "",
        "# terme normalisé -> identifiant de pays",
        "PAYS_MONDE_TERMES: dict[str, str] = {",
    ]
    for terme in sorted(termes):
        lignes.append(f"    {terme!r}: {termes[terme]!r},")
    lignes.append("}")
    lignes.append("")
    lignes.append("# identifiant -> libellé affichable")
    lignes.append("PAYS_MONDE_LIBELLES: dict[str, str] = {")
    for cle in sorted(libelles):
        lignes.append(f"    {cle!r}: {libelles[cle]!r},")
    lignes.append("}")
    lignes.append("")

    SORTIE.write_text("\n".join(lignes), encoding="utf-8")


if __name__ == "__main__":
    try:
        import pycountry  # noqa: F401
    except ImportError:
        sys.exit("pycountry requis : pip install pycountry")

    termes, libelles = construire()
    ecrire(termes, libelles)
    print(f"{len(libelles)} pays, {len(termes)} termes -> {SORTIE.name}")
