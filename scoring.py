import re
from functools import lru_cache

from keywords import (
    CENTRAL_ASIA_TERMS,
    CAUCASUS_TERMS,
    UYGHUR_TERMS,
    HUMAN_RIGHTS_TERMS,
    REPRESSION_TERMS,
    SPECIFIC_RIGHTS_TERMS,
    DOMESTIC_POLITICAL_TERMS,
    MAJOR_GEOPOLITICAL_TERMS,
    ROUTINE_GEO_TERMS,
    REGIONAL_ACTORS,
    HISTORICAL_TERMS,
    NON_NEWS_TERMS,
    NOISE_TERMS,
    LEGAL_REPRESSION_TERMS,
    JOURNALIST_TERMS,
    ACTIVIST_TERMS,
    CENTRAL_ASIA_HR_TERMS,
    SEVERE_REPRESSION_TERMS,
    ACTIVIST_REPRESSION_PATTERNS,
    JOURNALIST_REPRESSION_PATTERNS,
    ACTIVIST_REPRESSION_RU_PATTERNS,
    JOURNALIST_REPRESSION_RU_PATTERNS,
    ACTIVIST_REPRESSION_FA_PATTERNS,
    JOURNALIST_REPRESSION_FA_PATTERNS,
    REPRESSION_WEIGHTS,
    SPECIFIC_RIGHTS_WEIGHTS,
    LEGAL_CONTEXT_TERMS,
    LOW_SIGNAL_CONTEXT_TERMS,
    HUMAN_RIGHTS_DEFENDER_TERMS,
    FORCED_LABOR_TERMS,
)


# ============================================================
# V9 — SIGNAUX ADDITIONNELS
# ============================================================

REPRESSION_TERMS_V9 = [
    "torture", "tortured", "tortures", "torture allegations",
    "political prisoner", "political prisoners", "political repression",
    "political crackdown", "persecution", "persecuted", "persecutes",
    "arbitrary detention", "arbitrarily detained",
    "imprisoned", "imprisons", "imprisonment", "jailed", "jails",
    "prison sentence", "sentenced to prison", "sentences to prison",
    "sentenced", "sentences", "arrested", "arrests", "detained", "detains",
    "convicted", "convicts", "prosecuted", "prosecutes",
    # Titres journalistiques au présent d'action ("X Jails/Sentences/
    # Detains Y") : les formes passées ci-dessus ratent systématiquement
    # ce registre très courant (ex. "Kazakhstan Jails Activists for
    # Peaceful Xinjiang Protest", repéré en audit réel le 2026-09-11 —
    # article HRW correctement récupéré mais noté 30/BRUIT faute de
    # "jails" dans cette liste).
    "criminal prosecution", "censorship", "media blocked", "website blocked",
    "internet shutdown", "online censorship", "press restrictions",
    "media restrictions", "forced marriage", "child marriage",
    "forced labor", "forced labour", "forced picking", "forced cotton harvesting",
    "mobilized for cotton", "mandatory cotton picking", "forced recruitment",
    "labor mobilization", "labour mobilization",
    "преследован", "преследование", "задержан", "задержание", "арестован",
    "арест", "осужден", "осуждён", "приговорен", "приговорён",
    "заключен", "заключён", "репресс", "пытк", "цензур", "запрет",
    "политический заключенный", "политическое преследование",
    "политически мотивирован", "произвольное задержание",
    "принудительный труд", "трудовая мобилизация", "принудительная уборка хлопка",
    "بازداشت", "دستگیر", "زندانی سیاسی", "زندانیان سیاسی", "سرکوب سیاسی",
    "سرکوب", "آزار و اذیت", "بازداشت خودسرانه", "زندانی", "حبس",
    "محکوم", "محکومیت", "پرونده سیاسی", "محاکمه سیاسی", "شکنجه",
    "سانسور", "رسانه مسدود", "سایت مسدود", "قطعی اینترنت",
    "ازدواج اجباری", "ازدواج کودکان", "کار اجباری",

    # French — sans ce vocabulaire, les sources HRW/Amnesty/RSF en
    # français (repéré en audit réel le 2026-09-11 sur un article HRW
    # français concernant Anar Mammadli) ne franchissent jamais
    # l'ancrage HR principal, quel que soit le contenu réel.
    "torture", "torturé", "torturée", "prisonnier politique",
    "prisonniers politiques", "répression politique",
    "détention arbitraire", "emprisonné", "emprisonnement",
    "peine de prison", "condamné à la prison", "condamné", "condamne",
    "arrêté", "arrête", "détenu", "détient", "poursuivi", "poursuit",
    "censure", "site bloqué", "coupure d'internet", "mariage forcé",
    "travail forcé",
]

CENTRAL_ASIA_HR_EVENT_TERMS_V9 = [
    "bloody january", "january events", "qantar", "qantar events",
    "nukus protests", "nukus protest", "nukus events",
    "karakalpakstan protests", "karakalpakstan protest",
    "july 2022 karakalpakstan", "gorno-badakhshan", "gbao",
    "gbao protests", "khorog protests", "khorog protest",
    "pamiri protests", "uzbekistan crackdown",
    "january 2022 kazakhstan", "kazakhstan january 2022",
    "январские события", "январь 2022", "кровавый январь",
    "кантар", "нукусские события", "протесты в нукусе",
    "каракалпакстан протесты", "события в каракалпакстане",
    "горно-бадахшанская область", "гбао", "протесты в хоруге",
]

POLITICAL_RIGHTS_TERMS_V9 = [
    "rule of law", "judicial independence", "independent judiciary",
    "due process", "fair trial", "checks and balances",
    "concentration of power", "concentrate power", "power concentration",
    "lifetime immunity", "immunity from prosecution",
    "politically motivated charges", "politically motivated prosecution",
    "selective prosecution", "abuse of process", "constitutional court",
    "political prosecution", "political charges",
    "верховенство закона", "независимость судебной системы",
    "независимый суд", "справедливый суд", "право на справедливое судебное разбирательство",
    "сосредоточение власти", "концентрация власти",
    "пожизненный иммунитет", "иммунитет от уголовного преследования",
    "политически мотивированные обвинения", "политическое преследование",
    "избирательное правосудие",
]

PRESS_REPRESSION_TERMS_V9 = [
    "journalist detained", "journalist arrested", "journalist imprisoned",
    "journalist sentenced", "reporter detained", "reporter arrested",
    "media outlet closed", "media outlet shut down", "outlet closed",
    "outlet shut down", "media blocked", "website blocked",
    "internet shutdown", "online censorship", "press restrictions",
    "media restrictions", "press crackdown", "journalist harassment",
    "журналист задержан", "журналист арестован", "журналист осужден",
    "журналист приговорен", "журналист заключен", "СМИ заблокировано",
    "сайт заблокирован", "интернет отключили", "интернет отключение",
    "цензура в интернете", "ограничения для СМИ", "давление на журналистов",
]

GENDER_VIOLENCE_TERMS_V9 = [
    "domestic violence", "intimate partner violence", "marital violence",
    "violence against women", "gender-based violence", "gender violence",
    "coercive control", "forced marriage", "child marriage",
    "abuse of women", "abuse of daughters-in-law", "daughters-in-law",
    "daughter-in-law", "silent suffering", "bride kidnapping",
    "women subjected to violence", "насилие в семье", "домашнее насилие",
    "насилие в отношении женщин", "гендерное насилие", "принудительный брак",
    "детский брак", "насилие над женщинами", "невестка", "невестки",
    "насилие над невестками", "принуждение",
]

TRANSNATIONAL_REPRESSION_TERMS_V9 = [
    "transnational repression", "targeted abroad", "threatened abroad",
    "surveillance abroad", "dissidents abroad", "extradition request",
    "extradited", "extradition", "deported", "rendition",
    "kidnapped abroad", "abducted abroad", "forced return",
    "transnational persecution", "транснациональные репрессии",
    "преследование за рубежом", "преследование за границей",
    "экстрадиция", "экстрадирован", "депортирован", "похищен за рубежом",
    "принудительное возвращение", "преследование диссидентов за рубежом",
]

POLITICAL_PRISONER_TERMS_V9 = [
    "political prisoner", "political prisoners", "prisoner of conscience",
    "prisoners of conscience", "political prosecution", "political charges",
    "politically motivated charges", "politically motivated prosecution",
    "political imprisonment", "политический заключенный",
    "политические заключенные", "узник совести", "политическое заключение",
    "политическое преследование", "политически мотивированное обвинение",
]

DEMOCRACY_CIVIC_SPACE_TERMS_V9 = [
    "democracy score", "democratic decline", "democracy decline",
    "civic space", "shrinking civic space", "civil society restrictions",
    "political pluralism", "political participation", "democratic backsliding",
    "демократия", "снижение демократии", "гражданское пространство",
    "ограничение гражданского общества", "политический плюрализм",
]

TARGET_TERMS_V9 = [
    "activist", "activists", "human rights defender", "human rights defenders",
    "dissident", "dissidents", "journalist", "journalists", "reporter",
    "reporters", "lawyer", "lawyers", "blogger", "bloggers",
    "civil society", "ngo", "ngos", "правозащитник", "правозащитники",
    "активист", "активисты", "диссидент", "диссиденты", "журналист",
    "журналисты", "блогер", "блогеры", "адвокат", "адвокаты",
    # Formes féminines (voir la note dans ACTIVIST_TERMS/keywords.py) :
    # правозащитница change de radical par rapport au masculin.
    "активистка", "активистки", "правозащитница", "правозащитницы",
    "журналистка", "журналистки", "диссидентка", "диссидентки",
    "корреспондент", "корреспондентка", "корреспондента",
    "militant", "militants", "activiste", "activistes",
    "défenseur des droits humains", "défenseurs des droits humains",
    "défenseur des droits de l'homme", "défenseurs des droits de l'homme",
    "journaliste", "journalistes", "avocat", "avocate", "avocats",
    "blogueur", "blogueuse", "blogueurs", "société civile", "ong",
]

EXPLICIT_HR_ACTION_TERMS_V9 = [
    "arrested", "detained", "imprisoned", "jailed", "prosecuted",
    "convicted", "sentenced", "tortured", "persecuted", "harassed",
    "threatened", "censored", "blocked", "banned", "deported",
    "extradited", "abducted", "forced",
    # Présent journalistique ("Court Sentences Activist", "Police
    # Detain Blogger"...) : même limite que REPRESSION_TERMS_V9,
    # voir le commentaire là-bas.
    "arrests", "detains", "imprisons", "jails", "prosecutes",
    "convicts", "sentences", "tortures", "persecutes", "harasses",
    "threatens", "censors", "blocks", "bans", "deports",
    "extradites", "abducts", "forces",
    "задержан", "арестован",
    "осужден", "приговорен", "заключен", "пытал", "преследовал",
    "преследуется", "угрожал", "запрещен", "заблокирован", "депортирован",
    "экстрадирован", "похищен", "принужден",
    "arrêté", "arrête", "détenu", "détient", "emprisonné", "emprisonne",
    "condamné", "condamne", "torturé", "torture", "persécuté", "persécute",
    "harcelé", "harcèle", "menacé", "menace", "censuré", "censure",
    "bloqué", "bloque", "interdit", "expulsé", "expulse",
]

STRONG_PRIMARY_RIGHTS_V9 = [
    "human rights violation", "human rights violations", "rights violation",
    "freedom of expression", "freedom of speech", "freedom of assembly",
    "press freedom", "media freedom", "gender-based violence",
    "violence against women", "domestic violence", "coercive control",
    "forced marriage", "child marriage", "ethnic discrimination",
    "religious discrimination", "academic freedom", "academic censorship",
    "forced labor", "forced labour", "forced picking",
    "forced cotton harvesting", "child labor", "child labour",
    "lgbt rights", "lgbti rights", "нарушение прав человека",
    "свобода слова", "свобода прессы", "насилие в отношении женщин",
    "насилие в семье", "гендерное насилие", "принудительный труд",
    "принудительный брак", "детский труд", "этническая дискриминация",
    "религиозная дискриминация",
]

STRONG_POLITICAL_CONTEXT_V9 = [
    "lifetime immunity", "immunity from prosecution", "judicial independence",
    "rule of law", "due process", "fair trial", "checks and balances",
    "concentration of power", "politically motivated prosecution",
    "selective prosecution", "пожизненный иммунитет",
    "иммунитет от уголовного преследования", "независимость судебной системы",
    "верховенство закона", "справедливый суд", "сосредоточение власти",
    "концентрация власти", "политическое преследование",
]

REPRESSION_MORPHOLOGY_PATTERNS_V9 = [
    r"\bзадерж\w*",
    r"\bарест\w*",
    r"\bосужден\w*",
    r"\bосуждён\w*",
    r"\bприговор\w*",
    r"\bзаключ\w*",
    r"\bпреследован\w*",
    r"\bрепресс\w*",
    r"\bпыт\w*",
    r"\bцензур\w*",
    r"\bзапрещ\w*",
]

BODY_CONFIRMATION_TERMS_V9 = [
    "according to", "rights group", "human rights group",
    "amnesty international", "human rights watch", "civil society",
    "witnesses", "court documents", "prosecutors", "authorities",
    "arbitrary", "politically motivated", "torture", "detained",
    "arrested", "imprisoned", "sentenced", "задержан", "арестован",
    "пытки", "репресс", "правозащитники", "власти",
]

ACADEMIC_HR_TERMS_V9 = [
    "academic freedom", "academic censorship", "academic repression",
    "professor arrested", "professor detained", "scholar arrested",
    "scholar detained", "академическая свобода", "преследование ученых",
    "арест профессора", "задержание профессора",
]

GENERIC_REFORM_TERMS_V7 = [
    "democratic reform", "democratic reforms", "political reform",
    "political reforms", "development programs", "social stability",
    "constitutional reform", "political development", "political traditions",
]

NON_HR_TOPIC_TERMS_V7 = [
    "diaspora", "hidden economy", "travelogue", "night train", "dombra",
    "metallica", "k-pop", "hip-hop", "classical repertoire", "album",
    "music", "culture", "cultural", "tourism", "economic", "economy",
    "data center", "investors", "bonds", "gold reserves", "strategic partnership",
    "state visit", "sco summit", "nomad games",
]

REPRESSION_TERMS_V7 = REPRESSION_TERMS_V9
JOURNALIST_TERMS_V7 = JOURNALIST_TERMS
ACTIVIST_TERMS_V7 = ACTIVIST_TERMS


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
def _compiled(pattern, flags=0):
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
    return bool(_compiled(pattern).search(text))


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
    pattern_text = "|".join(r"(?<!\w)" + re.escape(norm) + r"(?!\w)" for norm in entries)
    return _compiled(pattern_text), lookup


def find_terms(text, terms):
    if not text or not terms:
        return []
    pattern, lookup = _terms_alternation(tuple(terms))
    if pattern is None:
        return []
    found = {lookup[match.group(0)] for match in pattern.finditer(text) if match.group(0) in lookup}
    return [term for term in terms if term in found]


def capped_add(current, value, maximum):
    return min(current + value, maximum)


def contains_pattern(text, patterns):
    return any(_compiled(pattern, re.I | re.S).search(text) for pattern in patterns)


def weighted_score(terms, weights, maximum):
    score = 0
    for term in terms:
        score += weights.get(normalize(term), 2)
    return min(score, maximum)


@lru_cache(maxsize=None)
def _alternation_pattern(terms):
    """
    Combine a term list into one alternation regex instead of matching
    each term separately. Terms are sorted longest-first so overlapping
    alternatives (e.g. "activist" vs "activists") prefer the longer match.
    Cached on the term tuple: the same static lists (ACTIVIST_TERMS,
    TARGET_TERMS_V9, ...) are reused across every article.
    """
    escaped = sorted(
        (re.escape(normalize(term)) for term in terms if term),
        key=len,
        reverse=True,
    )
    if not escaped:
        return None
    return _compiled("|".join(escaped), re.I | re.S)


def relation_present(text, targets, actions, window=140):
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
            if target_end <= action_start <= target_end + window:
                return True
            if action_end <= target_start <= action_end + window:
                return True
    return False


def has_russian_repression_morphology(text):
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
_RUSSIAN_CENTRAL_ASIA_STEM_PATTERNS = (
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

_RUSSIAN_CAUCASUS_STEM_PATTERNS = (
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


def _find_terms_with_russian_stems(text, terms, stem_patterns):
    matches = list(find_terms(text, terms))

    for name, pattern in stem_patterns:
        if name in matches:
            continue

        if _compiled(pattern, re.I).search(text):
            matches.append(name)

    return matches


def classify_article(article):
    title = normalize(article.get("title", ""))
    summary = normalize(article.get("summary", ""))
    body = normalize(article.get("body", ""))

    source_text = normalize(article.get("source", ""))
    link_text = normalize(article.get("link", article.get("url", "")))
    source_context = source_text + " " + link_text

    headline = (title + " " + summary[:3000]).strip()
    primary_hr_text = (title + " " + summary[:1600]).strip()
    full_text = (headline + " " + body[:12000]).strip()

    reasons = []

    # Chaque article est tagué avec sa langue pour ne lancer les
    # vérifications regex spécifiques à une langue (déclinaisons russes,
    # motifs farsi...) que sur les articles concernés — un article
    # anglais/français n'a jamais besoin d'être passé au crible des
    # déclinaisons russes ou des motifs persans. La plupart des sources
    # déclarent leur langue dans sources.py ; pour les quelques-unes
    # qui n'en déclarent pas une seule (ex: RFE/RL, "multi", qui mélange
    # plusieurs services linguistiques dans un même flux), on retombe
    # sur une détection par script (Cyrillique/Persan/Latin) du texte
    # réel de l'article. Le résultat est réécrit sur l'article lui-même
    # : chaque article ressort de classify_article() tagué avec la
    # langue effectivement utilisée pour le scorer, pas seulement la
    # langue déclarée par la source. Suggéré par l'utilisateur le
    # 2026-09-11 après avoir remarqué le ralentissement des runs suite
    # à l'ajout des vérifications russes, puis élargi à toutes les
    # vérifications langue-spécifiques (pas seulement le russe).
    declared_language = (article.get("language") or "").strip().lower()
    if declared_language in ("", "multi"):
        resolved_language = detect_language(full_text) or declared_language
    else:
        resolved_language = declared_language
    article["language"] = resolved_language

    is_russian_source = resolved_language == "ru"
    is_farsi_source = resolved_language == "fa"
    ru_central_asia_stems = (
        _RUSSIAN_CENTRAL_ASIA_STEM_PATTERNS if is_russian_source else ()
    )
    ru_caucasus_stems = (
        _RUSSIAN_CAUCASUS_STEM_PATTERNS if is_russian_source else ()
    )

    central_asia = _find_terms_with_russian_stems(
        headline, CENTRAL_ASIA_TERMS, ru_central_asia_stems
    )
    caucasus = _find_terms_with_russian_stems(
        headline, CAUCASUS_TERMS, ru_caucasus_stems
    )
    uyghur = find_terms(headline, UYGHUR_TERMS)

    # Uniquement des médias EXCLUSIVEMENT dédiés à la région : "Radio
    # Free Europe / Radio Liberty" et "Current Time" en ont été retirés
    # (audit réel du 2026-09-11) — RFE/RL couvre des dizaines de pays
    # (son service iranien Radio Farda notamment), donc cette porte de
    # secours faisait passer n'importe quel article RFE/RL sans rapport
    # avec l'Asie centrale/le Caucase (ex : jumelles iraniennes
    # torturées, prix du pétrole) comme pleinement régional, jusqu'au
    # niveau A. La géographie de ces articles reste jugée normalement
    # sur leur contenu (titre/corps), comme pour toute autre source.
    central_asia_source_terms = [
        "turkmen.news", "turkmen news", "the times of central asia",
        "times of central asia", "eurasianet", "eurasianet.org",
        "uzdaily", "kabar", "akipress", "gazeta.uz", "kun.uz",
        "fergana.agency", "fergana", "ozodlik", "ca-news", "novastan",
    ]
    central_asia_source = find_terms(source_context, central_asia_source_terms)

    body_geography = list(dict.fromkeys(
        _find_terms_with_russian_stems(
            body, CENTRAL_ASIA_TERMS, ru_central_asia_stems
        )
        + _find_terms_with_russian_stems(
            body, CAUCASUS_TERMS, ru_caucasus_stems
        )
        + find_terms(body, UYGHUR_TERMS)
    ))
    body_geo_count = len(body_geography)
    body_has_geography = body_geo_count >= 1
    strong_body_geography = body_geo_count >= 2

    # Une SEULE mention incidente dans le corps (ex : "press freedom
    # issues have also been documented in Uzbekistan, Syria...") ne
    # doit pas, à elle seule, faire passer un article sans aucun
    # ancrage régional en titre : repéré en audit réel le 2026-09-11
    # sur un article CPJ concernant un journaliste allemand détenu en
    # SYRIE, remonté en niveau A ("CAS HR CRITIQUE") uniquement parce
    # que le mot "Uzbekistan" apparaissait une fois dans le corps.
    # Deux mentions distinctes (strong_body_geography) restent un
    # signal suffisant quand le titre lui-même ne porte aucun ancrage.
    regional_context = bool(
        central_asia or caucasus or uyghur or central_asia_source
        or strong_body_geography
    )

    human_rights = find_terms(headline, HUMAN_RIGHTS_TERMS)
    repression = find_terms(headline, REPRESSION_TERMS)
    legal_repression = find_terms(headline, LEGAL_REPRESSION_TERMS)
    specific_rights = find_terms(headline, SPECIFIC_RIGHTS_TERMS)
    journalists = find_terms(headline, JOURNALIST_TERMS)
    activists = find_terms(headline, ACTIVIST_TERMS)
    central_asia_hr = find_terms(headline, CENTRAL_ASIA_HR_TERMS)
    domestic = find_terms(headline, DOMESTIC_POLITICAL_TERMS)
    major_geo = find_terms(headline, MAJOR_GEOPOLITICAL_TERMS)
    routine_geo = find_terms(headline, ROUTINE_GEO_TERMS)
    actors = find_terms(headline, REGIONAL_ACTORS)
    historical = find_terms(headline, HISTORICAL_TERMS)
    non_news = find_terms(headline, NON_NEWS_TERMS)
    noise = find_terms(headline, NOISE_TERMS)
    legal_context = find_terms(headline, LEGAL_CONTEXT_TERMS)
    low_signal_context = find_terms(headline, LOW_SIGNAL_CONTEXT_TERMS)

    body_repression = find_terms(body, REPRESSION_TERMS)
    body_legal_repression = find_terms(body, LEGAL_REPRESSION_TERMS)
    body_specific_rights = find_terms(body, SPECIFIC_RIGHTS_TERMS)
    body_human_rights = find_terms(body, HUMAN_RIGHTS_TERMS)
    body_journalists = find_terms(body, JOURNALIST_TERMS)
    body_activists = find_terms(body, ACTIVIST_TERMS)
    body_legal_context = find_terms(body, LEGAL_CONTEXT_TERMS)

    has_hr_defender = any(normalize(x) in full_text for x in HUMAN_RIGHTS_DEFENDER_TERMS)
    forced_labor_detected = any(normalize(x) in full_text for x in FORCED_LABOR_TERMS)

    has_detention = bool(_compiled(
        r"\b(detained|detention|arrested|arrest|задерж\w*|арест\w*)\b", re.I
    ).search(full_text))
    has_imprisonment = bool(_compiled(
        r"\b(imprisoned|imprisonment|prison sentence|sentenced|осужден\w*|приговор\w*|заключ\w*)\b",
        re.I
    ).search(full_text))
    has_censorship = bool(_compiled(r"(censorship|censored|цензур\w*)", re.I).search(full_text))
    has_government_involvement = bool(_compiled(
        r"\b(government|authorities|state|government-backed|ilo|правительство|власти|государств\w*)\b",
        re.I
    ).search(full_text))

    has_restriction = bool(_compiled(
        r"(restriction|restrictions|restricted access|ограничени\w*|запрет\w*)",
        re.I
    ).search(full_text))

    # --------------------------------------------------------
    # V9 — PRIMARY SIGNALS
    # --------------------------------------------------------

    event_terms = find_terms(primary_hr_text, CENTRAL_ASIA_HR_EVENT_TERMS_V9)
    primary_event_anchor = bool(event_terms)

    primary_repression = bool(
        find_terms(primary_hr_text, REPRESSION_TERMS_V9)
        or (is_russian_source and has_russian_repression_morphology(primary_hr_text))
        or contains_pattern(primary_hr_text, [
            r"\bconvicted\b", r"\bsentenc\w*\b", r"\bbehind bars\b",
            r"\bunder threat\b", r"\bunder pressure\b",
        ])
    )

    primary_defender = bool(find_terms(primary_hr_text, HUMAN_RIGHTS_DEFENDER_TERMS))
    primary_forced_labor = bool(
        find_terms(primary_hr_text, FORCED_LABOR_TERMS)
        or find_terms(primary_hr_text, [
            "forced picking", "forced cotton harvesting",
            "mobilized for cotton", "mandatory cotton picking",
            "labor mobilization", "labour mobilization",
        ])
    )

    primary_specific_right = bool(find_terms(
        primary_hr_text, STRONG_PRIMARY_RIGHTS_V9
    ))

    primary_press = bool(find_terms(primary_hr_text, PRESS_REPRESSION_TERMS_V9))
    primary_gender = bool(find_terms(primary_hr_text, GENDER_VIOLENCE_TERMS_V9))
    primary_transnational = bool(find_terms(
        primary_hr_text, TRANSNATIONAL_REPRESSION_TERMS_V9
    ))
    primary_political_prisoner = bool(find_terms(
        primary_hr_text, POLITICAL_PRISONER_TERMS_V9
    ))
    primary_political_context = bool(find_terms(
        primary_hr_text, STRONG_POLITICAL_CONTEXT_V9
    ))
    primary_democracy = bool(find_terms(
        primary_hr_text, DEMOCRACY_CIVIC_SPACE_TERMS_V9
    ))

    primary_journalist_pressure = bool(
        find_terms(primary_hr_text, JOURNALIST_TERMS_V7)
        and (
            primary_repression
            or primary_press
            or has_censorship
            or has_restriction
        )
    )

    primary_academic_case = bool(
        find_terms(primary_hr_text, ACADEMIC_HR_TERMS_V9)
        and (primary_repression or has_detention or has_imprisonment)
    )

    primary_defender_case = bool(
        primary_defender
        and (
            primary_repression
            or has_detention
            or has_imprisonment
        )
    )

    primary_lgbt_pressure = bool(
        _compiled(r"\blgbt\w*|\bqueer\b", re.I).search(primary_hr_text)
        and (primary_repression or primary_specific_right or primary_press)
    )

    primary_hr_anchor = bool(
        primary_repression
        or primary_defender_case
        or primary_forced_labor
        or primary_specific_right
        or primary_press
        or primary_gender
        or primary_transnational
        or primary_political_prisoner
        or primary_journalist_pressure
        or primary_academic_case
        or primary_lgbt_pressure
        or primary_event_anchor
    )

    # --------------------------------------------------------
    # V9 — BODY CONFIRMATION
    # --------------------------------------------------------

    body_v9_repression = find_terms(body, REPRESSION_TERMS_V9)
    body_v9_rights = find_terms(body, STRONG_PRIMARY_RIGHTS_V9)
    body_v9_press = find_terms(body, PRESS_REPRESSION_TERMS_V9)
    body_v9_gender = find_terms(body, GENDER_VIOLENCE_TERMS_V9)
    body_v9_transnational = find_terms(body, TRANSNATIONAL_REPRESSION_TERMS_V9)
    body_v9_political = find_terms(body, STRONG_POLITICAL_CONTEXT_V9)
    body_v9_prisoner = find_terms(body, POLITICAL_PRISONER_TERMS_V9)
    body_v9_actions = find_terms(body, EXPLICIT_HR_ACTION_TERMS_V9)
    body_v9_events = find_terms(body, CENTRAL_ASIA_HR_EVENT_TERMS_V9)

    body_morphology = (
        is_russian_source and has_russian_repression_morphology(body[:12000])
    )

    body_strong_hr_confirmation = bool(
        body_v9_repression
        or body_v9_rights
        or body_v9_press
        or body_v9_gender
        or body_v9_transnational
        or body_v9_political
        or body_v9_prisoner
        or body_v9_actions
        or body_morphology
    )

    # --------------------------------------------------------
    # V9 — TARGET / ACTION RELATIONS
    # --------------------------------------------------------

    # ACTIVIST_REPRESSION_RU_PATTERNS/FA_PATTERNS ne peuvent matcher que
    # du texte écrit dans leur script (cyrillique / persan) — inutile de
    # les lancer sur un article dont la langue résolue n'est pas celle-là.
    activist_relation = (
        contains_pattern(headline, ACTIVIST_REPRESSION_PATTERNS)
        or contains_pattern(body[:12000], ACTIVIST_REPRESSION_PATTERNS)
        or (is_russian_source and contains_pattern(headline, ACTIVIST_REPRESSION_RU_PATTERNS))
        or (is_russian_source and contains_pattern(body[:12000], ACTIVIST_REPRESSION_RU_PATTERNS))
        or (is_farsi_source and contains_pattern(headline, ACTIVIST_REPRESSION_FA_PATTERNS))
        or (is_farsi_source and contains_pattern(body[:12000], ACTIVIST_REPRESSION_FA_PATTERNS))
        or relation_present(full_text, ACTIVIST_TERMS, EXPLICIT_HR_ACTION_TERMS_V9)
    )

    journalist_relation = (
        contains_pattern(headline, JOURNALIST_REPRESSION_PATTERNS)
        or contains_pattern(body[:12000], JOURNALIST_REPRESSION_PATTERNS)
        or (is_russian_source and contains_pattern(headline, JOURNALIST_REPRESSION_RU_PATTERNS))
        or (is_russian_source and contains_pattern(body[:12000], JOURNALIST_REPRESSION_RU_PATTERNS))
        or (is_farsi_source and contains_pattern(headline, JOURNALIST_REPRESSION_FA_PATTERNS))
        or (is_farsi_source and contains_pattern(body[:12000], JOURNALIST_REPRESSION_FA_PATTERNS))
        or relation_present(full_text, JOURNALIST_TERMS, EXPLICIT_HR_ACTION_TERMS_V9)
    )

    target_repression_relation = relation_present(
        full_text, TARGET_TERMS_V9, EXPLICIT_HR_ACTION_TERMS_V9
    )

    has_activist = bool(activists or body_activists or primary_defender)
    has_journalist = bool(journalists or body_journalists)
    has_specific_rights = bool(specific_rights or body_specific_rights or primary_specific_right)
    has_human_rights = bool(human_rights or body_human_rights)
    has_repression = bool(
        repression or legal_repression or body_repression or body_legal_repression
        or primary_repression or body_v9_repression
    )
    has_legal_context = bool(legal_context or body_legal_context)

    confirmed_repression = regional_context and has_repression
    confirmed_rights = regional_context and has_specific_rights
    confirmed_activist_pressure = regional_context and activist_relation
    confirmed_journalist_pressure = regional_context and journalist_relation

    severe_morphology = bool(_compiled(
        r"(?:пыточ\w*\s+услов\w*|\bшизо\b|\bкарцер\b|произволь\w*\s+задерж\w*)",
        re.I
    ).search(full_text))

    severe_detected = bool(
        severe_morphology
        or any(normalize(x) in full_text for x in SEVERE_REPRESSION_TERMS)
    )

    prison_sentence_signal = bool(_compiled(
        r"(?:\b(?:8|9|10|11|12|13|14|15|16|17|18|19|20)\s*(?:лет|года|год|years?)\b.{0,80}"
        r"\b(?:тюрьм|заключ|лишен|лишени)|\b(?:приговорен|осужден|осуждён)\b.{0,80}"
        r"\b(?:лет|года|год)\b)",
        re.I
    ).search(full_text))

    # ========================================================
    # SOUS-SCORES
    # ========================================================

    geography_score = 0
    if central_asia:
        geography_score = 12
        reasons.append("Asie centrale: " + ", ".join(central_asia[:6]))
    elif caucasus:
        geography_score = 12
        reasons.append("Caucase: " + ", ".join(caucasus[:6]))
    elif uyghur:
        geography_score = 12
        reasons.append("Ouïghours: " + ", ".join(uyghur[:6]))
    elif central_asia_source:
        geography_score = 10
        reasons.append("source spécialisée Asie centrale")

    if (central_asia or caucasus or uyghur) and body_has_geography:
        geography_score = capped_add(geography_score, 3, 15)
        reasons.append("géographie confirmée dans le corps")

    target_score = 0
    if confirmed_activist_pressure:
        target_score = 20
        reasons.append("activiste / défenseur des droits ciblé")
    elif confirmed_journalist_pressure:
        target_score = 18
        reasons.append("journaliste / média ciblé")
    elif has_activist:
        target_score = 10
    elif has_journalist:
        target_score = 7
    elif "civil society" in headline or "ngo" in headline or "ngos" in headline:
        target_score = 5

    repression_terms_all = list(dict.fromkeys(
        repression + legal_repression + body_repression + body_legal_repression
        + body_v9_repression
    ))
    repression_score = weighted_score(
        repression_terms_all, REPRESSION_WEIGHTS, 25
    ) if repression_terms_all else 0

    if legal_repression and repression_score < 10:
        repression_score = 8

    if has_legal_context and repression_terms_all:
        repression_score = capped_add(
            repression_score,
            min(3, len(legal_context or body_legal_context)),
            30,
        )

    if confirmed_repression:
        repression_score = capped_add(repression_score, 5, 30)

    if confirmed_activist_pressure or confirmed_journalist_pressure:
        repression_score = capped_add(repression_score, 5, 30)

    rights_terms_all = list(dict.fromkeys(
        specific_rights + body_specific_rights + body_v9_rights
    ))
    rights_score = weighted_score(
        rights_terms_all, SPECIFIC_RIGHTS_WEIGHTS, 8
    ) if rights_terms_all else 0

    if has_human_rights and rights_score == 0:
        rights_score = 4

    if confirmed_rights:
        rights_score = capped_add(rights_score, 2, 10)

    journalism_score = 0
    if confirmed_activist_pressure or confirmed_journalist_pressure:
        journalism_score = 7
    elif journalist_relation and regional_context:
        journalism_score = 6
    elif confirmed_repression:
        journalism_score = 6
    elif major_geo:
        journalism_score = 5
    elif domestic and (has_human_rights or has_repression or has_specific_rights):
        journalism_score = 4
    elif has_human_rights:
        journalism_score = 3
    elif domestic:
        journalism_score = 2

    geopolitical_score = 0
    if major_geo:
        geopolitical_score = 7
    elif routine_geo:
        geopolitical_score = 2

    has_sco = bool(_compiled(
        r"\b(sco|shanghai cooperation organization|shanghai cooperation organisation)\b",
        re.I
    ).search(full_text))
    if has_sco and major_geo:
        geopolitical_score = capped_add(geopolitical_score, 3, 10)

    # Pas de bonus/malus de fraîcheur dans le score : le score et le
    # niveau (A/B/C/D) mesurent la pertinence sémantique d'un article,
    # pas son âge — un vieux rapport toujours pertinent (ex. republié
    # via Google News) doit garder le même niveau qu'un article frais
    # équivalent. La fraîcheur est gérée ailleurs, uniquement pour le
    # tri d'affichage (le plus récent en premier au sein d'un même
    # niveau) et l'indicateur d'âge sur chaque carte — jamais en
    # ajoutant/retirant des points. Décidé avec l'utilisateur le
    # 2026-09-11 après avoir remarqué que age_days n'était de toute
    # façon jamais renseigné nulle part dans le pipeline (le bonus
    # n'avait donc jamais été appliqué en pratique).
    score = (
        geography_score + target_score + repression_score
        + rights_score + journalism_score
        + geopolitical_score
    )

    # ========================================================
    # PÉNALITÉS
    # ========================================================

    penalties = 0

    if routine_geo and not (
        has_activist or has_journalist or has_specific_rights
        or has_repression or has_human_rights
    ):
        penalties += 10
        reasons.append("géopolitique / économie ordinaire")

    if historical and not (
        has_activist or has_journalist or has_repression
        or has_specific_rights or has_human_rights
        or primary_event_anchor
    ):
        penalties += 12
        reasons.append("histoire / culture")

    if actors and not (
        (central_asia or caucasus or uyghur) and (
            has_activist or has_journalist or has_repression
            or has_specific_rights or domestic or major_geo
        )
    ):
        penalties += 5

    if non_news:
        score = min(score, 5)
        reasons.append("contenu non journalistique")

    if noise:
        score = 0
        reasons.append("bruit")
    else:
        score -= penalties

    # ========================================================
    # V9 — BONUS INTELLIGENTS
    # ========================================================

    # Événement HR régional reconnu.
    if regional_context and primary_event_anchor:
        score += 12
        reasons.append(
            "ancre événement HR régional: " + ", ".join(event_terms[:4])
        )

        if body_v9_events and body_strong_hr_confirmation:
            score += 10
            reasons.append("événement HR confirmé dans le body")

        if primary_repression or body_v9_repression or body_morphology:
            score += 18
            reasons.append("événement régional + répression")

        if target_repression_relation or activist_relation or journalist_relation:
            score += 14
            reasons.append("événement régional + cible réprimée")

    # Cible + action : beaucoup plus fiable qu'un mot isolé.
    if activist_relation and regional_context:
        score += 18
        reasons.append("activiste/HRD + action répressive")

    if journalist_relation and regional_context:
        score += 20
        reasons.append("journaliste + action répressive")

    if primary_political_prisoner:
        score += 22
        reasons.append("prisonnier politique / détenu politique")

    if primary_transnational:
        score += 18
        reasons.append("répression transnationale")

    if primary_gender:
        score += 12
        reasons.append("violence / droits des femmes")
        if body_v9_gender:
            score += 5

    if primary_press:
        score += 15
        reasons.append("restriction de presse / média")

    if primary_political_context:
        score += 8
        reasons.append("état de droit / concentration du pouvoir")
        if body_v9_political:
            score += 5

    if primary_democracy and regional_context:
        score += 5
        reasons.append("dégradation démocratique / espace civique")

    if primary_specific_right:
        score += 8
        reasons.append("droit spécifique fortement signalé")

    if primary_hr_anchor and body_strong_hr_confirmation:
        score += 8
        reasons.append("signal HR confirmé par le corps")

    if severe_detected and regional_context and has_repression:
        score += 15
        reasons.append("répression grave confirmée")

    if prison_sentence_signal and regional_context and has_activist:
        score += 8
        reasons.append("peine de prison liée à un activiste")

    # Cas HR critique.
    critical_hr_case = bool(
        regional_context
        and (has_activist or has_hr_defender)
        and (
            primary_repression or primary_defender_case
            or primary_forced_labor or primary_journalist_pressure
            or primary_academic_case
        )
        and (confirmed_repression or severe_detected)
        and (prison_sentence_signal or has_repression)
    )

    if critical_hr_case:
        score += 25
        reasons.append("CAS HR CRITIQUE")

    # ========================================================
    # V9 — SMART CAPS
    # ========================================================

    if not regional_context:
        score = min(score, 20)
        reasons.append("porte régionale: aucun ancrage régional")

    if regional_context and primary_event_anchor:
        # Un événement HR connu est un ancrage valide.
        score = max(score, 42)

        if body_strong_hr_confirmation:
            score = max(score, 55)

    elif regional_context and not primary_hr_anchor:
        # Le body peut maintenant sauver un article si une vraie
        # action HR y est confirmée, mais avec un plafond prudent.
        if target_repression_relation or body_strong_hr_confirmation:
            score = min(score, 55)
            reasons.append("plafond V9: confirmation HR dans le body")
        elif any(phrase_present(primary_hr_text, x) for x in GENERIC_REFORM_TERMS_V7):
            score = min(score, 35)
            reasons.append("plafond V9: réforme générale")
        elif any(phrase_present(primary_hr_text, x) for x in NON_HR_TOPIC_TERMS_V7):
            score = min(score, 28)
            reasons.append("plafond V9: sujet non-HR")
        else:
            score = min(score, 35)
            reasons.append("plafond V9: aucun ancrage HR principal")

    # Politique/rule-of-law sans véritable affaire HR.
    only_political_context = (
        regional_context
        and primary_political_context
        and not (
            primary_repression or primary_event_anchor
            or primary_specific_right or primary_political_prisoner
            or primary_press or primary_gender
            or primary_transnational
        )
    )
    if only_political_context:
        score = min(score, 48)

    # Plafonds éditoriaux.
    if regional_context:
        if primary_forced_labor:
            score = min(score, 82 if has_government_involvement else 76)
        elif primary_academic_case:
            score = min(score, 82)
        elif primary_journalist_pressure or primary_press:
            score = min(score, 85)
        elif primary_defender_case or critical_hr_case:
            score = min(score, 100)
        elif primary_lgbt_pressure:
            score = min(score, 85)
        elif primary_transnational:
            score = min(score, 85)
        elif primary_repression:
            score = min(score, 78)
        elif primary_event_anchor and body_strong_hr_confirmation:
            score = min(score, 72)
        elif primary_specific_right or primary_gender:
            score = min(score, 65)

    # Sujet femmes/réformes sans violence ou contrainte explicite.
    if regional_context and not (
        primary_defender_case
        or primary_forced_labor
        or primary_journalist_pressure
        or primary_press
        or primary_academic_case
        or primary_lgbt_pressure
        or primary_repression
        or primary_event_anchor
        or primary_gender
    ):
        if any(phrase_present(primary_hr_text, term) for term in [
            "women's rights", "права женщин",
            "democratic reform", "democratic reforms",
            "political reform", "political reforms",
            "social stability",
        ]):
            score = min(score, 48)
            reasons.append("plafond V9: politique/droits sans événement concret")

    score = max(0, min(round(score), 100))

    # ========================================================
    # NIVEAU
    # ========================================================

    # Un article hors région (Asie centrale/Caucase/Ouïghours) qui
    # porte tout de même un vrai signal droits humains/activiste
    # (ex : HRW sur un défenseur des droits en Iran ou au Rwanda) est
    # distingué du pur bruit (sport, économie ordinaire, culture...) :
    # niveau D, réservé aux activistes/répression d'autres régions.
    # Le niveau E regroupe tout le reste (l'ancien niveau D).
    # "primary_repression" seul (mots comme "arrêté"/"détenu" sans
    # aucune cible activiste/journaliste identifiée) est trop
    # permissif ici : de la pure actualité criminelle/militaire sans
    # rapport avec les droits humains (ex. TASS/Regnum sur un agent
    # ukrainien du SBU détenu, un Moldave arrêté pour un projet
    # d'assassinat) déclenchait "primary_repression" et atterrissait
    # dans le niveau D "activistes d'autres régions" au lieu du bruit
    # (repéré en audit réel le 2026-09-11). "severe_detected" (torture,
    # disparition forcée, exécution extrajudiciaire...) reste un
    # signal fort même sans cible identifiée par son nom.
    global_hr_signal = bool(
        has_activist or has_journalist or has_hr_defender
        or severe_detected or primary_defender_case
        or primary_forced_labor or primary_specific_right
        or primary_press or primary_gender or primary_transnational
        or primary_political_prisoner or primary_journalist_pressure
        or primary_academic_case or primary_lgbt_pressure
        or critical_hr_case
    )

    if not regional_context:
        level = "D" if global_hr_signal else "E"
    elif non_news or noise:
        level = "E"
    elif score >= 75 and (
        confirmed_activist_pressure
        or confirmed_journalist_pressure
        or severe_detected
        or confirmed_repression
        or primary_forced_labor
        or primary_lgbt_pressure
        or primary_press
        or critical_hr_case
    ):
        level = "A"
    elif score >= 55:
        level = "B"
    elif score >= 35:
        level = "C"
    else:
        level = "E"

    if score >= 90:
        priority = "ABSOLUE"
    elif score >= 75:
        priority = "TRÈS HAUTE"
    elif score >= 60:
        priority = "HAUTE"
    elif score >= 40:
        priority = "MOYENNE"
    elif score >= 20:
        priority = "FAIBLE"
    else:
        priority = "BRUIT"

    # ========================================================
    # THÈME
    # ========================================================

    if confirmed_activist_pressure:
        theme = "Activistes / dissidents sous pression"
    elif confirmed_journalist_pressure:
        theme = "Journalistes sous pression"
    elif primary_event_anchor:
        theme = "Événement HR / répression régionale"
    elif primary_transnational:
        theme = "Répression transnationale"
    elif primary_gender:
        theme = "Droits des femmes / violences"
    elif confirmed_repression:
        theme = "Répression / droits humains"
    elif has_specific_rights:
        theme = "Droits spécifiques"
    elif primary_political_context or primary_democracy:
        theme = "État de droit / espace civique"
    elif domestic:
        theme = "Politique intérieure"
    elif major_geo:
        theme = "Géopolitique majeure"
    elif historical:
        theme = "Histoire / culture / contexte"
    elif non_news:
        theme = "Contenu institutionnel"
    elif routine_geo:
        theme = "Économie / géopolitique ordinaire"
    else:
        theme = "Faible priorité"

    relevant = bool(
        regional_context
        and score >= 40
        and not non_news
        and not noise
        and (
            has_activist or has_journalist or has_repression
            or has_specific_rights or has_human_rights
            or major_geo or primary_event_anchor
            or primary_gender or primary_political_context
            or primary_democracy
        )
    )

    if confirmed_activist_pressure or confirmed_journalist_pressure:
        relevant = True

    # ========================================================
    # AUDIT
    # ========================================================

    signals = {
        "central_asia": central_asia,
        "caucasus": caucasus,
        "uyghur": uyghur,
        "body_geography": body_geography,
        "body_geo_count": body_geo_count,
        "strong_body_geography": strong_body_geography,
        "global_hr_signal": global_hr_signal,

        "activists": activists,
        "body_activists": body_activists,
        "journalists": journalists,
        "body_journalists": body_journalists,

        "human_rights": human_rights,
        "body_human_rights": body_human_rights,
        "specific_rights": specific_rights,
        "body_specific_rights": body_specific_rights,

        "repression": repression,
        "legal_repression": legal_repression,
        "body_repression": body_repression,
        "body_legal_repression": body_legal_repression,
        "legal_context": legal_context,
        "body_legal_context": body_legal_context,
        "has_legal_context": has_legal_context,

        "domestic": domestic,
        "major_geo": major_geo,
        "routine_geo": routine_geo,
        "actors": actors,
        "has_sco": has_sco,

        "central_asia_hr": central_asia_hr,
        "historical": historical,
        "non_news": non_news,
        "noise": noise,
        "low_signal_context": low_signal_context,
        "regional_context": regional_context,

        "has_activist": has_activist,
        "has_journalist": has_journalist,
        "has_repression": has_repression,
        "has_specific_rights": has_specific_rights,
        "has_human_rights": has_human_rights,

        "activist_relation": activist_relation,
        "journalist_relation": journalist_relation,
        "target_repression_relation": target_repression_relation,

        "confirmed_repression": confirmed_repression,
        "confirmed_rights": confirmed_rights,
        "confirmed_activist_pressure": confirmed_activist_pressure,
        "confirmed_journalist_pressure": confirmed_journalist_pressure,

        "severe_detected": severe_detected,

        # V9 audit
        "primary_hr_anchor": primary_hr_anchor,
        "primary_event_anchor": primary_event_anchor,
        "event_terms": event_terms,
        "primary_repression": primary_repression,
        "primary_specific_right": primary_specific_right,
        "primary_forced_labor": primary_forced_labor,
        "primary_press": primary_press,
        "primary_gender": primary_gender,
        "primary_transnational": primary_transnational,
        "primary_political_prisoner": primary_political_prisoner,
        "primary_political_context": primary_political_context,
        "primary_democracy": primary_democracy,
        "body_strong_hr_confirmation": body_strong_hr_confirmation,
        "body_v9_repression": body_v9_repression,
        "body_v9_rights": body_v9_rights,
        "body_v9_press": body_v9_press,
        "body_v9_gender": body_v9_gender,
        "body_v9_events": body_v9_events,

        "geography_score": geography_score,
        "target_score": target_score,
        "repression_score": repression_score,
        "rights_score": rights_score,
        "journalism_score": journalism_score,
        "geopolitical_score": geopolitical_score,
        "penalties": penalties,
    }

    article["score"] = score
    article["level"] = level
    article["priority"] = priority
    article["theme"] = theme
    article["reasons"] = reasons
    article["relevant"] = relevant
    article["signals"] = signals

    return article
