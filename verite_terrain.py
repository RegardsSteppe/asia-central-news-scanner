"""
verite_terrain.py — mesurer la qualité du tri, et pas seulement sa
non-régression.

Le test de caractérisation (tests/test_scoring_characterization.py)
prouve que scoring.py ne change pas. Il ne dit rien de sa JUSTESSE. Or
c'est la seule question qu'un client posera : quelle proportion des
articles pertinents attrapez-vous, et quelle proportion de ce que vous
remontez l'est vraiment ?

Y répondre suppose un corpus étiqueté. Étiqueter 6800 articles à la
main est hors de portée ; ce module rend l'exercice faisable :

  1. comparer(...)      croise le scoring déterministe et le second avis
                        du LLM (juge_llm.py)
  2. a_arbitrer(...)    en sort la liste de ce qu'un humain doit trancher
  3. charger/mesurer    calcule précision et rappel sur les arbitrages

CE QUI COMPTE COMME VÉRITÉ
---------------------------

Uniquement un arbitrage humain. Le verdict du LLM ne compte jamais
comme vérité : c'est un avis, biaisé à sa manière (généreux sur tout ce
qui ressemble à des droits humains, faible en géographie). Il sert à
choisir QUOI faire arbitrer, pas à décider.

POURQUOI ARBITRER AUSSI DES CAS D'ACCORD
-----------------------------------------

N'étiqueter que les désaccords donnerait des chiffres flatteurs et
faux : les cas où les deux systèmes se trompent ENSEMBLE — le trou le
plus dangereux, un pan de vocabulaire qui manque des deux côtés —
resteraient invisibles. a_arbitrer() ajoute donc un échantillon
aléatoire de cas d'accord, seul moyen d'estimer sans biais ce qui se
passe sur le reste du corpus.
"""

from __future__ import annotations

import json
import random
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
    chiffres = resume(comparaison)

    print(f"COMPARAISON | {chiffres['articles_juges']} articles jugés")
    print(f"  accord                 : {chiffres['taux_accord'] * 100:.1f} %")
    print(f"    retenus des deux     : {chiffres['accord_retenu']}")
    print(f"    rejetés des deux     : {chiffres['accord_rejete']}")
    print(f"  faux positifs possibles: {chiffres['faux_positif_possible']}")
    print(f"  faux négatifs possibles: {chiffres['faux_negatif_possible']}")
    if chiffres["sans_verdict"]:
        print(f"  sans verdict           : {chiffres['sans_verdict']}")

    cas = a_arbitrer(comparaison, echantillon_accords=args.echantillon)
    ecrits = ecrire_a_arbitrer(cas, args.sortie)
    print(f"\nARBITRAGE | {ecrits} cas à trancher -> {args.sortie}")

    verite = charger_verite()
    if verite:
        mesure = mesurer(articles, verite)
        print(
            f"\nMESURE | sur {mesure['etiquetes']} articles étiquetés : "
            f"précision {mesure['precision'] * 100:.1f} % | "
            f"rappel {mesure['rappel'] * 100:.1f} % | "
            f"F1 {mesure['f1'] * 100:.1f} %"
        )
    else:
        print(
            f"\nMESURE | aucune étiquette dans {VERITE_FILE.name} — "
            "arbitrez le fichier ci-dessus puis renommez-le, "
            "ou fusionnez-le dedans."
        )


if __name__ == "__main__":
    main()
