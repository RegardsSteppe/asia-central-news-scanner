"""
matching.py — la couche de détection partagée : comment on cherche du
vocabulaire dans le texte d'un article.

Trois couches se partagent ce projet et chacune a un rôle net :

    keywords.py        QUOI chercher   (le vocabulaire, 4 langues)
        |
    matching.py        COMMENT chercher (normalisation, cache de regex,
        |               morphologie russe, détection de langue)
        |
        +--> scoring.py          décision éditoriale historique (score/niveau)
        +--> categorisation.py   description factuelle (geo/acteur/traitement)

Ces primitives vivaient dans scoring.py, et categorisation.py devait
importer trois de ses noms privés (la recherche par racines russes et
ses deux tables de motifs) pour ne pas réécrire de son côté une
détection plus faible. Les deux modules consommateurs partagent
désormais la même API publique : une
amélioration de la détection (une racine russe de plus, une langue
gérée) profite aux deux au lieu de devoir être recopiée.

Ce module ne décide RIEN : il ne connaît ni score, ni niveau, ni
pertinence. Il répond seulement à "ce texte contient-il ce vocabulaire".
"""

import re
from functools import lru_cache
from urllib.parse import urlparse

from keywords import REPRESSION_MORPHOLOGY_PATTERNS_V9


def normalize(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().lower()


_CYRILLIC_CHARS_RE = re.compile(r"[а-яё]", re.I)
_PERSIAN_CHARS_RE = re.compile(r"[؀-ۿ]")
_LATIN_CHARS_RE = re.compile(r"[a-z]", re.I)


def detect_language(text):
    """
    Cheap script-ratio language detection, used only as a fallback for
    articles whose source doesn't declare a single language in
    sources.py (missing, or "multi" — e.g. RFE/RL, which mixes several
    language services in one feed list). Not a general-purpose language
    identifier: it only distinguishes Russian/Farsi script from a Latin
    default, which is exactly what the language-scoped regex checks
    below need to decide whether to run.
    """
    if not text:
        return ""
    cyrillic = len(_CYRILLIC_CHARS_RE.findall(text))
    persian = len(_PERSIAN_CHARS_RE.findall(text))
    latin = len(_LATIN_CHARS_RE.findall(text))
    total = cyrillic + persian + latin
    if total < 20:
        return ""
    if cyrillic / total > 0.3:
        return "ru"
    if persian / total > 0.3:
        return "fa"
    return "en"


@lru_cache(maxsize=None)
def compiled(pattern, flags=0):
    """
    classify_article() runs dozens of keyword-list lookups against every
    article, each historically recompiling its regex from scratch — with
    ~50 term lists of dozens of phrases each, that's ~1800+ regex
    compilations per article. Terms/patterns are static (from keywords.py
    or literals below), so the compiled pattern is cached and reused
    across every article instead.
    """
    return re.compile(pattern, flags)


def phrase_present(text, phrase):
    if not text or not phrase:
        return False
    pattern = r"(?<!\w)" + re.escape(normalize(phrase)) + r"(?!\w)"
    return bool(compiled(pattern).search(text))


@lru_cache(maxsize=None)
def _terms_alternation(terms):
    """
    Combine a term list into one alternation regex plus a lookup from
    normalized term text back to the original term string, so find_terms
    can scan the text once instead of running a separate compile+search
    per term (classify_article calls find_terms ~50 times per article,
    against lists of dozens of terms each). Cached on the term tuple:
    the static lists from keywords.py/scoring.py are reused across every
    article, same as _compiled/_alternation_pattern.
    """
    entries = []
    lookup = {}
    for term in terms:
        norm = normalize(term)
        if not norm or norm in lookup:
            continue
        lookup[norm] = term
        entries.append(norm)
    if not entries:
        return None, {}
    entries.sort(key=len, reverse=True)
    # Les limites de mot encadrent le groupe entier au lieu d'être
    # répétées dans chaque alternative. Avec "(?<!\w)t1(?!\w)|(?<!\w)t2
    # (?!\w)|..." le moteur ne peut construire aucun préfiltre et ré-teste
    # le lookbehind pour chacun des ~190 termes, à chacune des ~12000
    # positions du texte. En sortant les assertions, il ne les évalue
    # qu'une fois par position et peut sauter directement aux premiers
    # caractères plausibles : mesuré sur un corps d'article réel, 30 ms
    # -> 0,95 ms par appel (x32), pour un résultat identique (les
    # alternatives restent testées dans le même ordre, la plus longue
    # d'abord, et le moteur revient dans le groupe si (?!\w) échoue).
    pattern_text = (
        r"(?<!\w)(?:"
        + "|".join(re.escape(norm) for norm in entries)
        + r")(?!\w)"
    )
    return compiled(pattern_text), lookup


def find_terms(text, terms):
    if not text or not terms:
        return []
    pattern, lookup = _terms_alternation(tuple(terms))
    if pattern is None:
        return []
    found = {lookup[match.group(0)] for match in pattern.finditer(text) if match.group(0) in lookup}
    return [term for term in terms if term in found]


def contains_pattern(text, patterns):
    return any(compiled(pattern, re.I | re.S).search(text) for pattern in patterns)


@lru_cache(maxsize=None)
def _borner(terme_normalise):
    """
    Encadre une alternative par des frontières de mot.

    Le début est toujours borné. La fin ne l'est QUE si le terme
    s'achève sur une lettre latine : les listes portent des radicaux
    russes et persans volontairement tronqués ("задержан", "преследова")
    qui doivent continuer à matcher leurs flexions ("задержана",
    "задержаны"). Leur coller un (?!\w) les rendrait muets sur toute
    forme fléchie, c'est-à-dire sur presque tout le texte réel.
    """
    motif = re.escape(terme_normalise)
    debut = r"(?<!\w)"
    fin = r"(?!\w)" if terme_normalise[-1:].isascii() and terme_normalise[-1:].isalpha() else ""
    return debut + motif + fin


def _alternation_pattern(terms):
    """
    Combine a term list into one alternation regex instead of matching
    each term separately. Terms are sorted longest-first so overlapping
    alternatives (e.g. "activist" vs "activists") prefer the longer match.
    Cached on the term tuple: the same static lists (ACTIVIST_TERMS,
    TARGET_TERMS_V9, ...) are reused across every article.

    Chaque alternative est bornée (voir _borner). Sans ça — c'était le
    cas jusqu'au 2026-09-14 — "forced" matchait dans "reinforced",
    "ngo" dans "Congo", "convicted" dans n'importe quel mot le
    contenant. Comme cette fonction alimente relation_present(), donc
    le signal target_repression_relation, une occurrence interne
    suffisait à déclarer une relation cible/action sur un article sans
    rapport, et ce signal déclenche à son tour le plafond à 55.
    """
    escaped = sorted(
        (_borner(normalize(term)) for term in terms if term),
        key=len,
        reverse=True,
    )
    if not escaped:
        return None
    return compiled("|".join(escaped), re.I | re.S)


# Écart maximal, en caractères, entre la fin d'un terme et le début de
# l'autre pour qu'on parle de "relation".
#
# Cette valeur est restée trois mois sans justification, introduite par
# un commit intitulé "improve". Mesurée le 2026-09-14 sur les 9235
# articles archivés, elle se défend — mais il fallait le vérifier.
#
# Nombre d'articles où un acteur et un traitement sont en relation,
# selon la fenêtre :
#
#      0 car    57   0.6%      300 car   389   4.2%
#     40 car   258   2.8%      600 car   457   4.9%
#     80 car   299   3.2%     1200 car   526   5.7%
#    140 car   344   3.7%    illimitée   622   6.7%
#
# La courbe a un coude : de 0 à 140 on gagne 287 articles, de 140 à 300
# seulement 45, puis elle repart lentement et linéairement. Cette
# dernière pente n'est plus de la proximité, c'est de la co-occurrence
# fortuite dans des corps de 12000 caractères.
#
# La distribution des écarts explique pourquoi : elle est bimodale.
# Premier quartile 12 caractères ("le journaliste arrêté"), médiane 97,
# mais troisième quartile 652 — des paragraphes différents, souvent des
# sujets différents. 140 tombe entre les deux modes.
#
# Ce que la fenêtre ne sait pas faire : distinguer "le journaliste a été
# arrêté" de "le journaliste a raconté l'arrestation du trafiquant".
# Les deux ont leurs termes à quelques caractères. C'est de la
# proximité, pas de la syntaxe.
FENETRE_RELATION_DEFAUT = 140


def relation_present(text, targets, actions, window=FENETRE_RELATION_DEFAUT):
    """
    True if any target term and any action term co-occur within `window`
    characters of each other, in either order.

    Previously this compiled a dedicated regex per (target, action) pair
    (thousands of pairs for the larger term lists) and searched the full
    article text with each one. Instead, build one combined alternation
    regex per side, collect match spans, and compare positions — this
    turns O(targets x actions) regex compiles/searches into O(targets +
    actions).
    """
    if not text:
        return False
    target_pattern = _alternation_pattern(tuple(targets))
    if target_pattern is None:
        return False
    target_spans = [m.span() for m in target_pattern.finditer(text)]
    if not target_spans:
        return False
    action_pattern = _alternation_pattern(tuple(actions))
    if action_pattern is None:
        return False
    action_spans = [m.span() for m in action_pattern.finditer(text)]
    if not action_spans:
        return False
    for target_start, target_end in target_spans:
        for action_start, action_end in action_spans:
            # Empans qui se chevauchent : c'est la relation la plus
            # forte qui soit, et elle était rejetée. Certaines listes
            # partagent des locutions entières — "journalist detained"
            # est à la fois un terme d'acteur et un terme de traitement
            # — donc les deux côtés matchent exactement le même texte.
            # Les deux tests ci-dessous exigent l'un APRÈS l'autre, ce
            # qu'un empan ne peut pas être vis-à-vis de lui-même : un
            # titre aussi explicite que "Journalist detained in Almaty"
            # ressortait relation=False, pendant que deux mots
            # quelconques à 100 caractères l'un de l'autre passaient.
            if target_start < action_end and action_start < target_end:
                return True
            if target_end <= action_start <= target_end + window:
                return True
            if action_end <= target_start <= action_end + window:
                return True
    return False


def has_russian_repression_morphology(text):
    """
    Répression décrite en russe, quelle que soit la flexion
    ("задержан"/"задержания"/"задержанного"...). Le russe décline tout :
    sans ces racines, seule la forme nominative exacte serait reconnue.
    """
    return contains_pattern(text, REPRESSION_MORPHOLOGY_PATTERNS_V9)


# Le russe est une langue à déclinaisons : un pays/une ville n'apparaît
# sous sa forme nominative exacte ("Узбекистан") que lorsqu'il est
# sujet — la tournure la plus courante dans une dépêche ("в
# Узбекистане", "власти Казахстана", "с Таджикистаном") le décline au
# génitif/prépositionnel/instrumental, jamais couvert par le matching
# de phrase exacte (find_terms/phrase_present). Repéré en audit réel
# le 2026-09-11 : "Наманганская правозащитница" (adjectif de Namangan)
# et "хлопковых полях Узбекистана" (génitif) ne franchissaient jamais
# la porte géographique malgré un vrai cas de défenseure des droits
# condamnée. Chaque paire (nom canonique, motif) complète — sans les
# remplacer — les listes CENTRAL_ASIA_TERMS/CAUCASUS_TERMS existantes.
RUSSIAN_CENTRAL_ASIA_STEM_PATTERNS = (
    ("казахстан", r"\bказахстан\w*\b"),
    ("казах", r"\bказах\w*\b"),
    ("узбекистан", r"\bузбекистан\w*\b"),
    ("узбек", r"\bузбек\w*\b"),
    ("кыргызстан", r"\bкыргызстан\w*\b"),
    # "кыргызский"/"кыргызские"/"кыргызской"... : l'adjectif russe
    # moderne (orthographe post-1991, celle qu'utilise le Kirghizistan
    # lui-même) ne partage pas le radical de "кыргызстан" (qui ne
    # couvre que "кыргызстана", "кыргызстане"...) — sans ce motif, un
    # article ne nommant JAMAIS le pays autrement que par cet adjectif
    # (ex. "кыргызские власти", "les autorités kirghizes") ne franchit
    # jamais la porte géographique. Repéré en audit réel le 2026-09-12
    # sur un article Kloop concernant un activiste kirghize (Kloop
    # Кенжебаев) resté à 0/E faute de reconnaître "кыргызские". Les 4
    # autres pays d'Asie centrale (казах/узбек/таджик/туркмен) avaient
    # déjà leur forme adjectivale nue ci-dessous ; seul le kirghize
    # manquait la sienne (only "киргиз", l'orthographe soviétique
    # antérieure, était couverte).
    ("кыргыз", r"\bкыргыз\w*\b"),
    ("киргизия", r"\bкиргизи\w*\b"),
    ("киргиз", r"\bкиргиз\w*\b"),
    ("таджикистан", r"\bтаджикистан\w*\b"),
    ("таджик", r"\bтаджик\w*\b"),
    ("туркменистан", r"\bтуркменистан\w*\b"),
    ("туркмен", r"\bтуркмен\w*\b"),
    ("наманган", r"\bнаманган\w*\b"),
    ("ташкент", r"\bташкент\w*\b"),
    ("алматы", r"\bалмат\w*\b"),
    ("астана", r"\bастан\w*\b"),
    ("бишкек", r"\bбишкек\w*\b"),
    ("ашхабад", r"\bашхабад\w*\b"),
    ("худжанд", r"\bхуджанд\w*\b"),
)

RUSSIAN_CAUCASUS_STEM_PATTERNS = (
    ("армения", r"\bармени\w*\b"),
    ("азербайджан", r"\bазербайджан\w*\b"),
    ("грузия", r"\bгрузи\w*\b"),
    ("чечня", r"\bчечн\w*\b"),
    ("чечня", r"\bчечен\w*\b"),
    ("дагестан", r"\bдагестан\w*\b"),
    ("осетия", r"\bосети\w*\b"),
    ("ингушетия", r"\bингуш\w*\b"),
    ("ереван", r"\bереван\w*\b"),
)


def find_terms_with_stems(text, terms, stem_patterns):
    """
    find_terms() complété par des racines flexionnelles : un terme est
    reconnu soit par correspondance exacte, soit par sa racine suivie
    de n'importe quelle terminaison.
    """
    matches = list(find_terms(text, terms))

    for name, pattern in stem_patterns:
        if name in matches:
            continue

        if compiled(pattern, re.I).search(text):
            matches.append(name)

    return matches


# ============================================================
# API PARTAGÉE — scoring.py ET categorisation.py passent par ici
# ============================================================
#
# Les trois fonctions ci-dessous encapsulent la règle que les deux
# modules appliquaient chacun de leur côté : la morphologie russe ne
# doit tourner que sur du texte russe (elle coûte cher et n'a aucun
# sens ailleurs), et la langue à considérer n'est pas toujours celle
# que la source déclare.


def resolve_language(declared_language, text):
    """
    Langue à utiliser pour les vérifications ciblées (racines russes,
    motifs farsi).

    La plupart des sources déclarent leur langue dans sources.py ; pour
    celles qui n'en déclarent pas une seule (ex. RFE/RL, "multi", qui
    mélange plusieurs services linguistiques dans un même flux), on
    retombe sur une détection par script du texte réel.
    """
    declared = (declared_language or "").strip().lower()
    if declared in ("", "multi"):
        return detect_language(text) or declared
    return declared


def find_central_asia_terms(text, terms, language):
    """Termes d'Asie centrale présents, morphologie russe incluse si besoin."""
    return find_terms_with_stems(
        text,
        terms,
        RUSSIAN_CENTRAL_ASIA_STEM_PATTERNS if language == "ru" else (),
    )


def find_caucasus_terms(text, terms, language):
    """Termes du Caucase présents, morphologie russe incluse si besoin."""
    return find_terms_with_stems(
        text,
        terms,
        RUSSIAN_CAUCASUS_STEM_PATTERNS if language == "ru" else (),
    )


# ============================================================
# FORME D'UN LIEN — page de rubrique vs article
# ============================================================
#
# Une page de rubrique porte pour titre exactement ce que son URL
# nomme : "Burkina Faso" sous cpj.org/africa/burkina-faso/, "Central
# Asia" sous eurasianet.org/region/central-asia. Un vrai article a un
# slug tronqué ou daté ("north-koreas-nicaragua-court" pour "North
# Korea's Nicaragua Courtship"), donc l'égalité EXACTE entre le
# dernier segment et le titre slugifié les sépare proprement, sans
# liste de verbes et sans rien de spécifique à une langue.
#
# Ici plutôt que dans article_ingestion.py (où vivent les autres
# heuristiques de lien) parce que scoring.py en a besoin et ne peut
# importer que matching/keywords : l'image RunPod minimale ne copie
# pas article_ingestion, qui tire bs4 et feedparser.
#
# Audit du 2026-09-14 : 442 entrées sur 8174, une douzaine de sources,
# zéro faux positif.

_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")

# Au-delà, un titre n'est plus un nom de rubrique mais une phrase.
SECTION_TITLE_MAX_WORDS = 5


def slugify(title):
    return _SLUG_NON_ALNUM.sub("-", (title or "").lower()).strip("-")


# Décorations que les sites accrochent à leur <title> et qui empêchent
# le slug de correspondre au segment d'URL : " - OHCHR Treaty Body
# Database", "Read More ›", "Tous les rapports »".
_TITRE_DECORATION = re.compile(r"\s*[-–—|]\s*[^-–—|]{1,40}$")
_TITRE_FLECHE = re.compile(r"[\s\u203a\u00bb>›»]+$")

# Segments d'URL qui désignent un index plutôt qu'une publication.
# Liste explicite et relue, tirée du recensement des URL du corpus :
# c'est ce qui remplace une comparaison approximative entre le slug du
# titre et le segment, approche essayée puis abandonnée faute de
# pouvoir séparer "US edition" sur /preference/edition/us d'un vrai
# titre court sur une URL courte — les deux ont exactement la même
# forme, et seul le contexte du chemin les distingue.
_SEGMENTS_INDEX = frozenset({
    "about", "about-us", "archive", "archives", "author", "authors",
    "cat", "categories", "category", "contact", "countries", "country",
    "donate", "index", "newsletter", "people", "podcast", "podcasts",
    "ppl", "preference", "preferences", "profile", "program",
    "programme", "programmes", "programs", "project", "projects",
    "publications", "region", "regions", "rubric", "section",
    "sections", "series", "staff", "subscribe", "tag", "tags", "team",
    "theme", "themes", "topic", "topics", "ueber-uns", "what-we-do",
    "where-we-work",
})

# Une URL qui date son contenu désigne une publication, jamais un
# index : aucune page de rubrique ne s'appelle /2026/09/12/. Le garde-
# fou vaut d'être explicite, parce que la règle du slug est fragile
# sur les titres courts — "Kazakhstan: Protesters Arbitrarily
# Arrested, Beaten" fait exactement 5 mots, et son URL d'origine chez
# HRW reprend le slug du titre. Sans cette exclusion, un vrai article
# de la forme la plus typique du corpus tomberait en niveau F.
#
# Vérifié sur les 9556 articles archivés : aucune des pages de
# rubrique réellement détectées ne porte de date dans son chemin, donc
# l'exclusion ne coûte aucune détection légitime.
_CHEMIN_DATE = re.compile(r"/(?:19|20)\d{2}/\d{1,2}(?:/|$)")


def looks_like_section_page(url, title):
    """
    Page de rubrique (pays, région, thème) plutôt qu'article.

    La règle de base est que le dernier segment de l'URL soit le slug
    du titre : eurasianet.org/region/the-baltics intitulé "The
    Baltics". Elle est protégée par SECTION_TITLE_MAX_WORDS, qui écarte
    les vrais articles — leurs titres sont longs, et leurs URL portent
    en général une date.

    Élargie le 2026-09-14 sur mesure : 88 pages échappaient à l'égalité
    stricte, toutes pour l'une de deux raisons.

    Le titre porte une décoration que le slug d'URL n'a pas ("Read
    More ›", "- OHCHR Treaty Body Database") : on réessaie donc avec
    le titre décapé.

    Le chemin passe par un segment d'index (_SEGMENTS_INDEX) :
    /preference/edition/us, /country/macedonia, /project/bad-practice.
    Une comparaison approximative entre slug et segment a d'abord été
    essayée puis abandonnée — "US edition" sur /preference/edition/us
    et un vrai titre court sur une URL courte ont la même forme, et
    aucun réglage ne les séparait sans perdre de vrais cas.

    Parmi les 88, on trouve les éditions du Guardian, "Donate Now"
    d'Amnesty, "Nous rejoindre" et "Tous les rapports" de RSF, les
    pages pays de CIVICUS et de l'OMCT, le bandeau cookies d'Amnesty.
    """
    titre = _TITRE_FLECHE.sub("", (title or "").strip())

    if not titre:
        return False

    try:
        chemin = urlparse(url or "").path.rstrip("/")
    except ValueError:
        return False

    if _CHEMIN_DATE.search(chemin):
        return False

    segments = [segment for segment in chemin.split("/") if segment]

    if not segments:
        return False

    dernier = segments[-1]

    variantes = [titre]
    decape = _TITRE_DECORATION.sub("", titre).strip()
    if decape and decape != titre:
        variantes.append(decape)

    court = any(
        len(variante.split()) <= SECTION_TITLE_MAX_WORDS
        for variante in variantes
    )

    if not court:
        return False

    for variante in variantes:
        if len(variante.split()) > SECTION_TITLE_MAX_WORDS:
            continue
        if slugify(variante) == dernier:
            return True

    return any(segment.lower() in _SEGMENTS_INDEX for segment in segments)
