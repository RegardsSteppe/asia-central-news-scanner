"""
verite_terrain.py — mesurer la qualité du tri, et pas seulement sa
non-régression.

Le test de caractérisation (tests/test_scoring_characterization.py)
prouve que scoring.py ne change pas. Il ne dit rien de sa JUSTESSE. Or
c'est la seule question qu'un client posera : quelle proportion des
articles pertinents attrapez-vous, et quelle proportion de ce que vous
remontez l'est vraiment ?

Y répondre vraiment suppose un corpus étiqueté à la main. Ce module
sert les deux situations, et ne fait jamais passer l'une pour l'autre.

SANS ÉTIQUETAGE HUMAIN (le cas par défaut aujourd'hui)
-------------------------------------------------------

  comparer(...)            croise le scoring et le second avis du LLM
  accord_avec_juge(...)    taux d'ACCORD — jamais appelé précision ni
                           rappel, parce que ça n'en est pas
  analyser_desaccords(...) ce qu'il y a à corriger : sources aveugles,
                           et mots sur-représentés dans les titres que
                           le juge retient et que le scanner rejette

C'est déjà actionnable : chaque article retenu par le juge seul est un
candidat "mot-clé manquant", et les remonter par source et par mot
transforme l'audit article-par-article en un inventaire de tout le
corpus d'un coup.

Mais il faut être net sur la limite : un accord élevé ne prouve rien.
Si le scanner et le juge ratent la même chose — un pan de vocabulaire
absent des deux côtés — l'accord reste excellent pendant que la qualité
est mauvaise. L'accord mesure la ressemblance entre deux systèmes, pas
leur justesse.

AVEC ÉTIQUETAGE HUMAIN (quand il y en aura)
--------------------------------------------

  a_arbitrer(...)          la liste courte à trancher : tous les
                           désaccords, plus un échantillon de contrôle
                           de cas d'accord (sans lui, les erreurs
                           communes aux deux systèmes resteraient
                           invisibles)
  charger_verite/mesurer   précision, rappel et F1 — les vrais

Le verdict du LLM ne compte jamais comme vérité : c'est un avis, biaisé
à sa manière (généreux sur tout ce qui ressemble à des droits humains,
faible en géographie). Caler scoring.py dessus reviendrait à optimiser
vers ses erreurs.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
VERITE_FILE = BASE_DIR / "verite_terrain.json"

# Combien de cas d'accord tirer au sort, en plus de tous les désaccords.
ECHANTILLON_ACCORDS = 200

# Un désaccord sur un article classé A est plus grave qu'un désaccord
# sur un E : le premier est en haut du site, le second est noyé. Sert à
# trier ce qu'on fait arbitrer en premier.
_GRAVITE_NIVEAU = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}


def _cle(article: dict[str, Any]) -> str:
    return article.get("archive_key") or article.get("key") or article.get("url") or ""


def comparer(
    articles: list[dict[str, Any]],
    verdicts: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Croise le verdict déterministe (`relevant`, produit par scoring.py)
    et celui du juge, article par article.

    Retourne les quatre cases du tableau de contingence et le détail de
    chaque cas, indexé par clé. Les articles sans verdict exploitable
    (panne du modèle, réponse illisible) sont comptés à part : les
    traiter comme "non pertinent" fausserait tout.
    """
    par_cle = {_cle(a): a for a in articles if _cle(a)}
    resultat = {
        "accord_retenu": [],
        "accord_rejete": [],
        "faux_positif_possible": [],
        "faux_negatif_possible": [],
        "sans_verdict": [],
    }

    for verdict in verdicts:
        cle = verdict.get("cle") or ""
        article = par_cle.get(cle)

        if article is None:
            continue

        if "pertinent" not in verdict:
            resultat["sans_verdict"].append(
                {"cle": cle, "erreur": verdict.get("erreur", "inconnue")}
            )
            continue

        deterministe = bool(article.get("relevant"))
        juge = bool(verdict["pertinent"])

        cas = {
            "cle": cle,
            "titre": article.get("title", ""),
            "source": article.get("source", ""),
            "niveau": article.get("level", ""),
            "score": article.get("score", 0),
            "deterministe": deterministe,
            "juge": juge,
            "raison_juge": verdict.get("raison", ""),
            "confiance_juge": verdict.get("confiance", ""),
            "raisons_scoring": article.get("reasons", []),
        }

        if deterministe and juge:
            resultat["accord_retenu"].append(cas)
        elif not deterministe and not juge:
            resultat["accord_rejete"].append(cas)
        elif deterministe and not juge:
            resultat["faux_positif_possible"].append(cas)
        else:
            resultat["faux_negatif_possible"].append(cas)

    return resultat


def resume(comparaison: dict[str, Any]) -> dict[str, Any]:
    """Chiffres d'ensemble : taux d'accord et volume de chaque case."""
    tailles = {cle: len(valeur) for cle, valeur in comparaison.items()}
    juges = sum(
        tailles[cle]
        for cle in (
            "accord_retenu",
            "accord_rejete",
            "faux_positif_possible",
            "faux_negatif_possible",
        )
    )
    accords = tailles["accord_retenu"] + tailles["accord_rejete"]

    return {
        **tailles,
        "articles_juges": juges,
        "taux_accord": round(accords / juges, 4) if juges else 0.0,
    }


def a_arbitrer(
    comparaison: dict[str, Any],
    echantillon_accords: int = ECHANTILLON_ACCORDS,
    graine: int = 20260913,
) -> list[dict[str, Any]]:
    """
    Ce qu'un humain doit trancher : tous les désaccords, plus un
    échantillon aléatoire de cas d'accord (voir l'entête du module).

    Les désaccords viennent en premier, les plus graves d'abord — un
    article classé A que le juge rejette est en haut du site.
    """
    desaccords = (
        comparaison["faux_positif_possible"] + comparaison["faux_negatif_possible"]
    )
    desaccords.sort(
        key=lambda cas: (
            _GRAVITE_NIVEAU.get(cas.get("niveau", "E"), 0),
            cas.get("score", 0),
        ),
        reverse=True,
    )

    accords = comparaison["accord_retenu"] + comparaison["accord_rejete"]
    tirage = random.Random(graine)
    echantillon = tirage.sample(
        accords, min(echantillon_accords, len(accords))
    ) if accords else []

    for cas in desaccords:
        cas["motif_arbitrage"] = "désaccord"
    for cas in echantillon:
        cas["motif_arbitrage"] = "échantillon de contrôle"

    return desaccords + echantillon


# ============================================================
# EXPLOITER LES DÉSACCORDS SANS ÉTIQUETAGE HUMAIN
# ============================================================
#
# Tant que personne n'arbitre, il n'y a pas de vérité, donc pas de
# précision ni de rappel — seulement un taux d'accord avec le juge (voir
# accord_avec_juge, qui refuse délibérément ce vocabulaire).
#
# Les désaccords restent néanmoins exploitables tels quels : chaque
# article que le juge retient et que le scanner rejette est un candidat
# "mot-clé manquant". Les regrouper par source et par langue montre OÙ
# le scanner est aveugle, et comparer le vocabulaire des titres en
# désaccord à celui du reste du corpus fait remonter les mots qui
# déclenchent le juge et pas le scanner. C'est la même démarche que les
# audits article par article des semaines passées, mais menée sur tout
# le corpus d'un coup.

# Un mot doit apparaître au moins ce nombre de fois dans les désaccords
# pour être proposé : en dessous, c'est du bruit statistique.
MIN_OCCURRENCES_MOT = 3

_MOT = re.compile(r"[^\W\d_][\w'-]{2,}", re.UNICODE)


def accord_avec_juge(comparaison: dict[str, Any]) -> dict[str, Any]:
    """
    Décompte de l'accord entre le scanner et le juge.

    Volontairement PAS appelé précision/rappel : sans arbitrage humain,
    rien ici ne mesure la justesse. Deux systèmes qui se trompent
    ensemble affichent un accord excellent.
    """
    chiffres = resume(comparaison)

    return {
        "articles_juges": chiffres["articles_juges"],
        "taux_accord": chiffres["taux_accord"],
        "retenus_par_les_deux": chiffres["accord_retenu"],
        "rejetes_par_les_deux": chiffres["accord_rejete"],
        "retenus_par_le_juge_seul": chiffres["faux_negatif_possible"],
        "retenus_par_le_scanner_seul": chiffres["faux_positif_possible"],
        "sans_verdict": chiffres["sans_verdict"],
        "avertissement": (
            "Accord avec un juge LLM, pas une mesure de justesse : "
            "aucun étiquetage humain n'a été fait."
        ),
    }


def _mots(textes: list[str]) -> dict[str, int]:
    comptes: dict[str, int] = {}

    for texte in textes:
        for mot in _MOT.findall((texte or "").lower()):
            comptes[mot] = comptes.get(mot, 0) + 1

    return comptes


def mots_sur_representes(
    titres_desaccord: list[str],
    titres_reference: list[str],
    minimum: int = MIN_OCCURRENCES_MOT,
) -> list[dict[str, Any]]:
    """
    Mots bien plus fréquents dans les titres en désaccord que dans le
    reste du corpus — candidats à ajouter au vocabulaire.

    On compare des fréquences relatives plutôt que des comptes bruts :
    les mots-outils ("dans", "the", "в") apparaissent partout, donc leur
    rapport vaut ~1 et ils tombent d'eux-mêmes. Pas besoin d'une liste
    de mots vides, qui serait à maintenir en quatre langues.
    """
    dans_desaccord = _mots(titres_desaccord)
    dans_reference = _mots(titres_reference)

    total_desaccord = sum(dans_desaccord.values()) or 1
    total_reference = sum(dans_reference.values()) or 1

    candidats = []
    for mot, compte in dans_desaccord.items():
        if compte < minimum:
            continue

        frequence = compte / total_desaccord
        frequence_ref = dans_reference.get(mot, 0) / total_reference
        # +1 occurrence virtuelle : un mot absent de la référence aurait
        # sinon un rapport infini, et sortirait en tête sur un hasard.
        rapport = frequence / (frequence_ref or (1 / total_reference))

        if rapport > 1.5:
            candidats.append(
                {"mot": mot, "occurrences": compte, "sur_representation": round(rapport, 1)}
            )

    candidats.sort(key=lambda c: (-c["sur_representation"], -c["occurrences"]))
    return candidats


def analyser_desaccords(
    comparaison: dict[str, Any],
    limite: int = 15,
) -> dict[str, Any]:
    """
    Ce qu'il y a à corriger, déduit des seuls désaccords.

    "rates" : le juge retient, le scanner rejette — des articles que la
    veille manque probablement. C'est le côté qui coûte cher.
    "bruit" : l'inverse, des articles que le scanner remonte pour rien.
    """
    rates = comparaison["faux_negatif_possible"]
    bruit = comparaison["faux_positif_possible"]
    accords = comparaison["accord_retenu"] + comparaison["accord_rejete"]

    def par(champ: str, cas: list[dict[str, Any]]) -> list[dict[str, Any]]:
        comptes: dict[str, int] = {}
        for un_cas in cas:
            valeur = un_cas.get(champ) or "(inconnu)"
            comptes[valeur] = comptes.get(valeur, 0) + 1
        return [
            {champ: valeur, "cas": compte}
            for valeur, compte in sorted(
                comptes.items(), key=lambda item: -item[1]
            )[:limite]
        ]

    return {
        "rates": {
            "total": len(rates),
            "par_source": par("source", rates),
            "par_niveau": par("niveau", rates),
            "mots_candidats": mots_sur_representes(
                [c.get("titre", "") for c in rates],
                [c.get("titre", "") for c in accords],
            )[:limite],
        },
        "bruit": {
            "total": len(bruit),
            "par_source": par("source", bruit),
            "par_niveau": par("niveau", bruit),
        },
    }


# ============================================================
# VÉRITÉ TERRAIN
# ============================================================

def charger_verite(path: Path | None = None) -> dict[str, bool]:
    """
    Étiquettes humaines : clé d'article -> pertinent (booléen).

    Seules les entrées explicitement tranchées comptent. Une entrée
    laissée à null (pas encore arbitrée) est ignorée plutôt que
    comptée comme "non pertinent".
    """
    path = path or VERITE_FILE

    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as handle:
            brut = json.load(handle)
    except Exception as exc:
        print(f"WARNING | VERITE | fichier illisible: {type(exc).__name__}: {exc}")
        return {}

    etiquettes = brut.get("etiquettes", brut) if isinstance(brut, dict) else {}

    return {
        cle: valeur["pertinent"] if isinstance(valeur, dict) else valeur
        for cle, valeur in etiquettes.items()
        if (
            isinstance(valeur, bool)
            or (isinstance(valeur, dict) and isinstance(valeur.get("pertinent"), bool))
        )
    }


def mesurer(
    articles: list[dict[str, Any]],
    verite: dict[str, bool],
) -> dict[str, Any]:
    """
    Précision, rappel et F1 de scoring.py sur les articles étiquetés.

    précision : parmi ce que le scanner retient, quelle part est
                réellement pertinente (l'inverse du bruit)
    rappel    : parmi ce qui est réellement pertinent, quelle part le
                scanner attrape (l'inverse des articles ratés)
    """
    vrais_positifs = faux_positifs = faux_negatifs = vrais_negatifs = 0

    for article in articles:
        cle = _cle(article)
        if cle not in verite:
            continue

        attendu = verite[cle]
        obtenu = bool(article.get("relevant"))

        if obtenu and attendu:
            vrais_positifs += 1
        elif obtenu and not attendu:
            faux_positifs += 1
        elif not obtenu and attendu:
            faux_negatifs += 1
        else:
            vrais_negatifs += 1

    precision = (
        vrais_positifs / (vrais_positifs + faux_positifs)
        if (vrais_positifs + faux_positifs)
        else 0.0
    )
    rappel = (
        vrais_positifs / (vrais_positifs + faux_negatifs)
        if (vrais_positifs + faux_negatifs)
        else 0.0
    )
    f1 = (
        2 * precision * rappel / (precision + rappel)
        if (precision + rappel)
        else 0.0
    )

    return {
        "etiquetes": vrais_positifs + faux_positifs + faux_negatifs + vrais_negatifs,
        "vrais_positifs": vrais_positifs,
        "faux_positifs": faux_positifs,
        "faux_negatifs": faux_negatifs,
        "vrais_negatifs": vrais_negatifs,
        "precision": round(precision, 4),
        "rappel": round(rappel, 4),
        "f1": round(f1, 4),
    }


def ecrire_a_arbitrer(
    cas: list[dict[str, Any]],
    path: Path,
) -> int:
    """
    Écrit le fichier d'arbitrage : chaque cas avec `pertinent` à null,
    à remplacer par true ou false à la main.
    """
    contenu = {
        "mode_emploi": (
            "Remplacez chaque \"pertinent\": null par true ou false. "
            "Les entrées laissées à null sont ignorées par mesurer()."
        ),
        "etiquettes": {
            cas_unique["cle"]: {
                "pertinent": None,
                "titre": cas_unique.get("titre", ""),
                "source": cas_unique.get("source", ""),
                "niveau": cas_unique.get("niveau", ""),
                "motif_arbitrage": cas_unique.get("motif_arbitrage", ""),
                "avis_scoring": cas_unique.get("deterministe"),
                "avis_juge": cas_unique.get("juge"),
                "raison_juge": cas_unique.get("raison_juge", ""),
            }
            for cas_unique in cas
        },
    }

    with path.open("w", encoding="utf-8") as handle:
        json.dump(contenu, handle, ensure_ascii=False, indent=1, sort_keys=True)

    return len(contenu["etiquettes"])


# ============================================================
# CLI
# ============================================================

def _charger_json(chemin: Path) -> Any:
    with chemin.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _articles_depuis_archive() -> list[dict[str, Any]]:
    """Rescore l'archive complète avec les règles du jour."""
    import archive as archive_module
    from scoring import classify_article
    from text_utils import parse_date

    entrees = archive_module.load_archive()
    etat = archive_module.load_state()

    articles = []
    for article in archive_module.iter_articles(entrees, etat):
        article["date"] = parse_date(article.get("date"))
        classify_article(article)
        articles.append(article)

    return articles


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Croise le scoring déterministe et le second avis du juge, "
            "puis prépare la liste à arbitrer à la main."
        )
    )
    parser.add_argument(
        "--verdicts",
        required=True,
        type=Path,
        help=(
            "JSON des verdicts du juge — la réponse du mode 'judge' de "
            "rp_handler, ou un objet {\"verdicts\": [...]}."
        ),
    )
    parser.add_argument(
        "--articles",
        type=Path,
        help=(
            "JSON d'articles déjà scorés. Par défaut, l'archive du dépôt "
            "est rechargée et rescorée."
        ),
    )
    parser.add_argument(
        "--sortie",
        type=Path,
        default=BASE_DIR / "a_arbitrer.json",
        help="Fichier d'arbitrage à produire.",
    )
    parser.add_argument(
        "--arbitrage",
        action="store_true",
        help=(
            "Écrit aussi le fichier d'arbitrage manuel. Sans lui, seuls "
            "l'accord et l'analyse des désaccords sont produits — ce qui "
            "ne demande aucune relecture humaine."
        ),
    )
    parser.add_argument(
        "--echantillon",
        type=int,
        default=ECHANTILLON_ACCORDS,
        help=(
            "Nombre de cas d'accord tirés au sort en plus des désaccords "
            "(0 pour n'arbitrer que les désaccords — déconseillé, voir "
            "l'entête du module)."
        ),
    )
    args = parser.parse_args()

    brut = _charger_json(args.verdicts)
    verdicts = brut.get("verdicts", brut) if isinstance(brut, dict) else brut

    if args.articles:
        articles = _charger_json(args.articles)
        if isinstance(articles, dict):
            articles = articles.get("articles", [])
    else:
        articles = _articles_depuis_archive()

    comparaison = comparer(articles, verdicts)
    accord = accord_avec_juge(comparaison)

    print(f"ACCORD AVEC LE JUGE | {accord['articles_juges']} articles jugés")
    print(f"  d'accord                   : {accord['taux_accord'] * 100:.1f} %")
    print(f"    retenus par les deux     : {accord['retenus_par_les_deux']}")
    print(f"    rejetés par les deux     : {accord['rejetes_par_les_deux']}")
    print(f"  retenus par le juge seul   : {accord['retenus_par_le_juge_seul']}")
    print(f"  retenus par le scanner seul: {accord['retenus_par_le_scanner_seul']}")
    if accord["sans_verdict"]:
        print(f"  sans verdict               : {accord['sans_verdict']}")
    print(f"  /!\\ {accord['avertissement']}")

    analyse = analyser_desaccords(comparaison)

    rates = analyse["rates"]
    print(f"\nÀ CORRIGER | {rates['total']} articles retenus par le juge seul")
    if rates["par_source"]:
        print("  sources les plus concernées :")
        for ligne in rates["par_source"][:8]:
            print(f"    {ligne['cas']:5}  {ligne['source'][:50]}")
    if rates["mots_candidats"]:
        print("  mots sur-représentés dans ces titres (vocabulaire candidat) :")
        for mot in rates["mots_candidats"][:12]:
            print(
                f"    x{mot['sur_representation']:<6} {mot['occurrences']:4} fois  "
                f"{mot['mot']}"
            )

    bruit = analyse["bruit"]
    if bruit["total"]:
        print(f"\nBRUIT | {bruit['total']} articles retenus par le scanner seul")
        for ligne in bruit["par_source"][:8]:
            print(f"    {ligne['cas']:5}  {ligne['source'][:50]}")

    if args.arbitrage:
        cas = a_arbitrer(comparaison, echantillon_accords=args.echantillon)
        ecrits = ecrire_a_arbitrer(cas, args.sortie)
        print(f"\nARBITRAGE | {ecrits} cas à trancher -> {args.sortie}")

    verite = charger_verite()
    if verite:
        mesure = mesurer(articles, verite)
        print(
            f"\nMESURE | sur {mesure['etiquetes']} articles étiquetés à la main : "
            f"précision {mesure['precision'] * 100:.1f} % | "
            f"rappel {mesure['rappel'] * 100:.1f} % | "
            f"F1 {mesure['f1'] * 100:.1f} %"
        )


if __name__ == "__main__":
    main()
