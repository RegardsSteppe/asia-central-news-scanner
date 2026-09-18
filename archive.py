"""
archive.py — l'historique durable des articles.

Jusqu'ici le scanner ne gardait aucune mémoire des articles : chaque run
republiait "ce que les sources affichent en ce moment", et un article
qui sortait de la page d'accueil de sa source disparaissait du site.
Ce module conserve tout ce qui a été vu une fois.

DEUX FICHIERS, parce qu'ils n'ont pas la même nature
-----------------------------------------------------

archive.jsonl        immuable, append-only. Une ligne = un article, les
                     faits qui ne changent jamais (url, titre, résumé,
                     source, langue, date de publication, date de
                     première vue). Un run n'y AJOUTE que les nouveaux.

archive_state.json   mutable, réécrit à chaque run, mais tenu petit :
                     la date du dernier scan, et — uniquement pour les
                     articles qui n'y figuraient PLUS — la date à
                     laquelle une source les affichait pour la dernière
                     fois.

Les séparer n'est pas cosmétique. Si chaque ligne portait sa date de
dernier scan, chaque run réécrirait les ~6800 lignes du fichier et git
en stockerait une copie entière à chaque fois — précisément le problème
que cette structure existe pour éviter. En append-only, git ne stocke
que les lignes ajoutées.

Et l'état ne liste que les exceptions pour la même raison. Un
dictionnaire clé -> date couvrant tout le corpus pèse 1,1 Mo réécrits à
chaque run (mesuré sur les 6764 articles du 2026-09-13). Or presque
tous les articles sont revus à chaque run : la règle est donc "vu au
dernier scan", et seuls les articles tombés des pages de leurs sources
sont inscrits nommément. Leur date est alors figée pour toujours, donc
git n'en stocke la ligne qu'une fois : le coût par run devient
proportionnel aux articles qui viennent de disparaître, pas au corpus.

CE QUI N'EST PAS STOCKÉ ICI
---------------------------

Le score, le niveau, le thème : recalculés à chaque run par scoring.py
à partir des règles du jour. C'est l'intérêt de l'archive — enrichir un
mot-clé profite rétroactivement à tout l'historique, sans rien
re-télécharger.

CE QUI EST STOCKÉ, ET POURQUOI ÇA A CHANGÉ
------------------------------------------

Le corps des articles l'est désormais pour tous les niveaux (voir
BODY_KEEP_LEVELS). Il ne l'était que pour A-D, par souci de taille, et
c'était un mauvais calcul : le corps est l'endroit où vit l'information
descriptive (73% des articles qui portent un "traitement" le perdent
sans lui), et le niveau E est justement là où les catégories sont
vides. On jetait donc un texte qu'on venait de télécharger, à l'endroit
précis où il aurait servi.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from article_ingestion import strip_diplomat_byline, strip_osce_metadata
from text_utils import strip_boilerplate, strip_related_blocks

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ARCHIVE_FILE = DATA_DIR / "archive.jsonl"
ARCHIVE_STATE_FILE = DATA_DIR / "archive_state.json"

# Niveaux dont on conserve le corps complet dans l'archive.
#
# Était {"A","B","C","D"} — le corps d'un article de niveau E était
# jeté alors qu'on venait de le télécharger. Mesuré le 2026-09-14 sur
# les 167 articles du corpus qui ont un corps : sans lui, 73% de ceux
# qui portent un "traitement" et 61% de ceux qui portent un "acteur"
# ressortent vides. Autrement dit le corps est l'endroit où vit
# l'information descriptive, et le niveau E est précisément la zone où
# les catégories sont vides. Garder A-D seulement garantissait que le
# problème ne se résorbe jamais.
#
# Le coût est réel et borné par BODY_MAX_CHARS : environ 6 Ko par
# article, soit ~30 Mo pour la part récupérable du corpus (un tiers des
# URL sont des redirections Google News dont le corps n'existe pas).
# SCANNER_BODY_KEEP_LEVELS permet de revenir au comportement d'avant
# sans toucher au code si l'archive devient trop lourde.
_BODY_KEEP_LEVELS_ENV = os.getenv("SCANNER_BODY_KEEP_LEVELS", "A,B,C,D,E")

BODY_KEEP_LEVELS = frozenset(
    niveau.strip().upper()
    for niveau in _BODY_KEEP_LEVELS_ENV.split(",")
    if niveau.strip()
)

# Longueur max du corps conservé, alignée sur BODY_CACHE_MAX_CHARS
# (news_scanner.py) pour ne pas stocker deux troncatures différentes.
BODY_MAX_CHARS = 8000

# Champs immuables d'une entrée d'archive. Tout le reste (score, niveau,
# thème, catégorisation) est recalculé à chaque run.
ARCHIVE_FIELDS = (
    "key",
    "url",
    "title",
    "summary",
    "source",
    "source_label",
    "language",
    "date",
    "premiere_vue",
    "body",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize_date(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def entry_from_article(
    article: dict[str, Any],
    key: str,
    premiere_vue: str | None = None,
) -> dict[str, Any]:
    """Entrée d'archive (faits immuables) à partir d'un article scoré."""
    body = ""
    if article.get("level") in BODY_KEEP_LEVELS:
        body = (article.get("body") or "")[:BODY_MAX_CHARS]

    return {
        "key": key,
        "url": article.get("url", ""),
        "title": article.get("title", ""),
        "summary": article.get("summary", ""),
        "source": article.get("source", ""),
        "source_label": article.get("source_label", ""),
        "language": article.get("language", ""),
        "date": _serialize_date(article.get("date")),
        "premiere_vue": premiere_vue or _now_iso(),
        "body": body,
    }


def article_from_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """
    Article rescorable à partir d'une entrée d'archive.

    La date est laissée telle quelle (chaîne ISO) : news_scanner la
    reparse via parse_date au moment de l'utiliser, comme pour un
    article fraîchement récupéré.
    """
    return {
        "url": entry.get("url", ""),
        "title": entry.get("title", ""),
        "summary": entry.get("summary", ""),
        "source": entry.get("source", ""),
        "source_label": entry.get("source_label", ""),
        "language": entry.get("language", ""),
        "date": entry.get("date"),
        "body": entry.get("body", ""),
    }


# ============================================================
# LECTURE / ÉCRITURE
# ============================================================

def load_archive(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """
    Archive indexée par clé.

    Une ligne illisible est ignorée plutôt que de faire échouer le run :
    l'archive est append-only, donc une ligne corrompue (écriture
    interrompue) ne doit jamais empêcher de lire les milliers d'autres.
    """
    path = path or ARCHIVE_FILE

    if not path.exists():
        return {}

    entries: dict[str, dict[str, Any]] = {}
    ignorees = 0

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                ignorees += 1
                continue
            key = entry.get("key")
            if isinstance(key, str) and key:
                entries[key] = entry

    if ignorees:
        print(f"WARNING | ARCHIVE | {ignorees} ligne(s) illisible(s) ignorée(s)")

    return entries


def append_entries(
    entries: Iterable[dict[str, Any]],
    path: Path | None = None,
) -> int:
    """Ajoute des entrées à la fin du fichier. Retourne le nombre écrit."""
    path = path or ARCHIVE_FILE
    entries = list(entries)

    if not entries:
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    return len(entries)


def rewrite_archive(
    entries: Iterable[dict[str, Any]],
    path: Path | None = None,
) -> int:
    """
    Réécrit l'archive en entier.

    Le fonctionnement normal privilégie append_entries, qui garde le
    coût git proportionnel aux nouveautés. La réécriture complète sert
    aux opérations de maintenance (purge, migration de schéma) et au
    remplissage des corps (voir backfill_bodies), qui modifie par
    nature des lignes existantes. L'appelant ne doit la déclencher que
    si quelque chose a effectivement changé : un run qui n'ajoute aucun
    corps doit rester en append-only.
    """
    path = path or ARCHIVE_FILE
    entries = list(entries)

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    return len(entries)


def empty_state() -> dict[str, Any]:
    return {"dernier_scan": "", "vus_avant": {}}


def merge_files(base_path: Path, incoming_path: Path) -> tuple[int, int]:
    """
    Fusionne `incoming_path` dans `base_path`. Retourne
    (entrées ajoutées, faits récupérés — corps et dates).

    Sert à résoudre une course entre deux runs : si un autre run a poussé
    ses lignes pendant le nôtre, réécrire notre version par-dessus
    perdrait les siennes. Un fichier append-only se résout en prenant
    l'union, jamais en choisissant un gagnant.

    L'union porte sur DEUX choses depuis le 2026-09-14, et pas
    seulement sur les clés manquantes. Un corps qui arrive pour une clé
    déjà connue des deux côtés est lui aussi du contenu neuf : ne
    reprendre que les entrées absentes le jetait silencieusement. Le
    cas se produit dès qu'un run perd la course au push, se remet sur
    la version distante et refusionne la sienne — ses corps fraîchement
    téléchargés portent justement sur des clés déjà archivées. Sans ça,
    un run de remplissage de corps (fetch_all_bodies.py --archive) perd
    des heures de téléchargement pour un simple conflit de push.

    L'union porte sur les corps ET sur les dates, pour la même raison :
    une date extraite pendant une passe d'une heure se perdrait au
    premier conflit de push. Comme backfill_bodies et backfill_dates,
    un corps n'est jamais remplacé par un plus court et une date connue
    n'est jamais écrasée : la fusion ne peut qu'enrichir.
    """
    base = load_archive(base_path)
    incoming = load_archive(incoming_path)

    manquantes = []
    corps_recuperes = 0

    for key, entry in incoming.items():
        if key not in base:
            manquantes.append(entry)
            continue

        nouveau = entry.get("body") or ""
        if nouveau and len(nouveau) > len(base[key].get("body") or ""):
            base[key]["body"] = nouveau
            corps_recuperes += 1

        date = entry.get("date")
        if date and not base[key].get("date"):
            base[key]["date"] = date
            corps_recuperes += 1

    if corps_recuperes:
        # Une ligne existante change : il faut réécrire, l'ajout en fin
        # de fichier ne peut pas modifier une ligne déjà écrite. Les
        # entrées manquantes sont intégrées au même passage.
        for entry in manquantes:
            base[entry["key"]] = entry
        rewrite_archive(base.values(), base_path)
        return len(manquantes), corps_recuperes

    return append_entries(manquantes, base_path), 0


def load_state(path: Path | None = None) -> dict[str, Any]:
    path = path or ARCHIVE_STATE_FILE

    if not path.exists():
        return empty_state()

    try:
        with path.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
        if isinstance(state, dict):
            state.setdefault("dernier_scan", "")
            anciens = state.get("vus_avant")
            state["vus_avant"] = anciens if isinstance(anciens, dict) else {}
            return state
    except Exception as exc:
        print(
            f"WARNING | ARCHIVE | état illisible, réinitialisé: "
            f"{type(exc).__name__}: {exc}"
        )

    return empty_state()


def derniere_vue(state: dict[str, Any], key: str) -> str:
    """
    Date à laquelle une source affichait cet article pour la dernière
    fois.

    Absent de `vus_avant` veut dire "vu au dernier scan" : c'est le cas
    de la quasi-totalité du corpus, et c'est ce qui garde l'état petit.
    """
    return state.get("vus_avant", {}).get(key) or state.get("dernier_scan", "")


def save_state(state: dict[str, Any], path: Path | None = None) -> None:
    path = path or ARCHIVE_STATE_FILE

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, sort_keys=True, indent=1)
    except Exception as exc:
        print(
            f"WARNING | ARCHIVE | sauvegarde de l'état échouée: "
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# FUSION
# ============================================================

def merge_scanned(
    archive: dict[str, dict[str, Any]],
    state: dict[str, Any],
    scanned: list[tuple[str, dict[str, Any]]],
    scan_date: str | None = None,
) -> list[dict[str, Any]]:
    """
    Intègre les articles d'un run dans l'archive.

    `scanned` est une liste de (clé, article scoré). Retourne les
    nouvelles entrées à ajouter au fichier — l'appelant décide quand
    écrire. `state` est mis à jour sur place : date du dernier scan, et
    date de dernière vue des articles effectivement revus dans une
    source.

    Un article déjà archivé n'est jamais réécrit : seule sa date de
    dernière vue bouge, et elle vit dans l'état, pas dans l'archive.
    """
    scan_date = scan_date or _now_iso()
    scan_precedent = state.get("dernier_scan", "")
    vus_avant = state.setdefault("vus_avant", {})

    nouvelles = []
    vus_maintenant = set()

    for key, article in scanned:
        if not key:
            continue

        vus_maintenant.add(key)
        # Réapparu dans une source : il redevient "vu au dernier scan",
        # donc il sort de la liste des exceptions.
        vus_avant.pop(key, None)

        if key in archive:
            continue

        entry = entry_from_article(article, key, premiere_vue=scan_date)
        archive[key] = entry
        nouvelles.append(entry)

    # Les articles absents de ce run qui n'étaient pas encore inscrits
    # étaient, par définition, visibles au scan précédent : on fige leur
    # date là, une fois pour toutes.
    if scan_precedent:
        for key in archive:
            if key not in vus_maintenant and key not in vus_avant:
                vus_avant[key] = scan_precedent

    state["dernier_scan"] = scan_date

    return nouvelles


def backfill_bodies(
    archive: dict[str, dict[str, Any]],
    scanned: list[tuple[str, dict[str, Any]]],
) -> int:
    """
    Recopie dans l'archive le corps des articles qu'on vient de
    télécharger. Modifie `archive` sur place, renvoie le nombre
    d'entrées mises à jour.

    Nécessaire parce que merge_scanned() n'écrit QUE les nouveautés :
    un article déjà archivé qui reçoit enfin son corps ne verrait
    jamais sa ligne changer. Constaté sur le run du 2026-09-14, qui a
    téléchargé 914 corps et n'en a conservé que 18 — les seuls qui
    appartenaient à des articles encore inconnus de l'archive. Sans
    cette étape, l'enrichissement retélécharge indéfiniment un texte
    qu'il jette aussitôt.

    Ne touche qu'aux entrées dont le corps est ABSENT ou plus court :
    un corps déjà stocké ne doit pas être remplacé par une extraction
    partielle (page servie derrière un mur, redirection...), sinon le
    contenu se dégraderait d'un run à l'autre.
    """
    mis_a_jour = 0

    for key, article in scanned:
        if not key or key not in archive:
            continue

        if article.get("level") not in BODY_KEEP_LEVELS:
            continue

        nouveau = (article.get("body") or "")[:BODY_MAX_CHARS]
        if not nouveau:
            continue

        if len(nouveau) <= len(archive[key].get("body") or ""):
            continue

        archive[key]["body"] = nouveau
        mis_a_jour += 1

    return mis_a_jour


def nettoyer_corps(archive: dict[str, dict[str, Any]]) -> int:
    """
    Applique strip_related_blocks() aux corps DÉJÀ archivés. Modifie
    `archive` sur place, renvoie le nombre d'entrées nettoyées.

    backfill_bodies() ne peut pas s'en charger : il refuse par
    construction tout corps plus court que celui qu'il remplace — une
    règle qui protège contre les extractions partielles, et qu'un
    nettoyage, par définition raccourcissant, prendrait de plein
    fouet.

    Le rattrapage est nécessaire parce que l'archive contient déjà
    plusieurs milliers de corps téléchargés avant le nettoyage, et que
    rien ne les retéléchargera : un corps présent n'est jamais
    réenrichi. La fonction étant idempotente, les runs suivants
    renvoient 0 et l'archive reste en append-only.
    """
    nettoyes = 0

    for entry in archive.values():
        corps = entry.get("body") or ""
        if not corps:
            continue

        propre = strip_boilerplate(strip_related_blocks(corps), entry.get("source"))
        if propre != corps:
            entry["body"] = propre
            nettoyes += 1

    return nettoyes


def nettoyer_titres(archive: dict[str, dict[str, Any]]) -> int:
    """
    Applique strip_diplomat_byline() aux titres DÉJÀ archivés.
    Modifie `archive` sur place, renvoie le nombre d'entrées nettoyées.

    Contrairement aux corps (voir nettoyer_corps), les titres ne sont
    JAMAIS retéléchargés : merge_scanned() n'écrit un article déjà
    archivé sous aucun prétexte, titre compris. Sans ce rattrapage,
    les titres déjà pollués — 12 de The Diplomat (signature et chapô
    collés), 22 d'OSCE (étiquette, doublon et pied Date/Location) —
    le resteraient pour toujours, même une fois le bug corrigé à la
    source. Idempotente, comme nettoyer_corps.
    """
    nettoyes = 0

    for entry in archive.values():
        titre = entry.get("title") or ""
        if not titre:
            continue

        propre = strip_diplomat_byline(titre, entry.get("source"))
        propre = strip_osce_metadata(propre, entry.get("source"))
        if propre != titre:
            entry["title"] = propre
            nettoyes += 1

    return nettoyes


def backfill_dates(
    archive: dict[str, dict[str, Any]],
    scanned: list[tuple[str, dict[str, Any]]],
) -> int:
    """
    Inscrit dans l'archive la date de publication découverte pour des
    entrées qui n'en avaient pas. Modifie `archive` sur place, renvoie
    le nombre d'entrées mises à jour.

    Même angle mort que pour les corps : merge_scanned() n'écrit que
    les nouveautés, donc une date extraite après coup — au moment où
    l'article reçoit enfin son texte — ne rejoignait jamais sa ligne.
    Audit du 2026-09-14 : 5829 entrées sur 8824 sans date, dont 3545
    dont la page avait pourtant été téléchargée.

    Ne remplit qu'une date ABSENTE. Une date déjà connue vient du flux
    RSS, qui est plus fiable que ce qu'on devine dans une page HTML.
    """
    mis_a_jour = 0

    for key, article in scanned:
        if not key or key not in archive:
            continue

        if archive[key].get("date"):
            continue

        date = _serialize_date(article.get("date"))
        if not date:
            continue

        archive[key]["date"] = date
        mis_a_jour += 1

    return mis_a_jour


def iter_articles(
    archive: dict[str, dict[str, Any]],
    state: dict[str, Any],
) -> Iterator[dict[str, Any]]:
    """
    Articles rescorables de toute l'archive, enrichis de leurs dates.

    Chaque article porte `derniere_vue` (dernière fois qu'une source
    l'affichait) et `dernier_scan` (ce run) — c'est ce qui permet de
    distinguer un article toujours en ligne d'un article archivé.
    """
    dernier_scan = state.get("dernier_scan", "")

    for key, entry in archive.items():
        article = article_from_entry(entry)
        article["archive_key"] = key
        article["premiere_vue"] = entry.get("premiere_vue", "")
        article["derniere_vue"] = derniere_vue(state, key)
        article["dernier_scan"] = dernier_scan
        yield article


# ============================================================
# CLI — utilisé par le workflow pour résoudre une course au push
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Maintenance de l'archive")
    parser.add_argument(
        "--merge-into",
        nargs=2,
        metavar=("BASE", "INCOMING"),
        required=True,
        help=(
            "Fusionne INCOMING dans BASE : entrées manquantes, et faits "
            "(corps, dates) que BASE n'a pas encore."
        ),
    )
    args = parser.parse_args()

    base, incoming = (Path(p) for p in args.merge_into)
    ajoutees, faits = merge_files(base, incoming)
    print(
        f"ARCHIVE | {ajoutees} entrée(s) et {faits} fait(s) "
        f"fusionné(s) dans {base.name}"
    )
