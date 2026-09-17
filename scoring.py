import re

from matching import (
    looks_like_section_page,
    compiled,
    contains_pattern,
    detect_language,
    find_caucasus_terms,
    find_central_asia_terms,
    find_terms,
    has_russian_repression_morphology,
    normalize,
    phrase_present,
    relation_present,
    resolve_language,
)

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
    # Vocabulaire russe ajouté le 2026-09-14, même démarche que le
    # français la veille : 93 des 323 titres HRW sans corps restés en
    # E sont en russe. Les racines sont volontairement tronquées —
    # _borner() ne pose pas de limite de mot après un caractère non
    # latin, donc "депортаци" couvre депортация/депортации/депортацию.
    #
    # ATTENTION, piège vérifié de près : find_terms() n'est PAS
    # _alternation_pattern(). Il impose une limite de mot APRÈS le
    # terme, pour tous les termes, y compris cyrilliques. Une racine
    # tronquée y est donc totalement inerte — "депортаци" ne matche ni
    # "депортация" ni "депортации". C'est exactement le défaut que
    # categorisation.py documente pour les racines de REPRESSION_TERMS
    # et qu'il corrige avec _TRAITEMENT_STEM_PATTERNS. Les formes sont
    # donc énumérées ici, une par une.
    #
    # Audit sur les 9556 articles, titres ET corps :
    #
    #   депортаци        11 occurrences, justes        RETENU
    #   выдворени         3 occurrences, justes        RETENU
    #   нарушени* прав   11 occurrences, justes        RETENU
    #   насильственн* исчезновени (forme qualifiée)    RETENU
    #   не выпускают из страны    1, juste             RETENU
    #   принудительн* содержани   1, juste             RETENU
    #
    # Trois rejets, tous pour cause de sens non répressif dominant :
    #
    #   эксплуатаци   2 justes / 11 — dans les corps le mot signifie
    #                 "mise en service" : "сдали в эксплуатацию",
    #                 "срок эксплуатации", "ввели в эксплуатацию".
    #   нападени      le sens militaire ou criminel domine largement
    #                 ("нападение России на Украину", morsures de
    #                 chien, attaques d'infrastructures).
    #   исчезновени   nu, même piège que "disappeared" en anglais :
    #                 disparition d'oiseaux, de Telegram de l'App
    #                 Store, d'un bâtiment aimé des habitants. Seule
    #                 la forme qualifiée entre.
    "депортация", "депортации", "депортацию", "депортацией",
    "депортаций", "депортациям", "депортирован", "депортировали",
    "выдворение", "выдворения", "выдворению", "выдворении",
    "нарушение прав", "нарушения прав",
    "нарушений прав", "нарушениях прав",
    "насильственное исчезновение", "насильственных исчезновений",
    "насильственные исчезновения",
    "не выпускают из страны", "не выпускали из страны",
    "принудительное содержание", "принудительном содержании",
    # Ajoutés le 2026-09-14, même forme de trou que "crackdown" nu la
    # veille, en français cette fois : la liste contenait "répression
    # policière" et "répression politique" — les formes qualifiées —
    # mais pas "répression" seul. Or les titres HRW en français
    # écrivent "Ouzbékistan : Répression létale au Karakalpakstan" et
    # "Géorgie : Répression de manifestations pro-UE", qui
    # ressortaient sans ancrage HR principal, donc en E.
    #
    # Mesuré sur les 9556 articles : 7 titres, 7 justes ; 15 corps,
    # 15 justes. Contrairement à "crackdown", le mot n'a pas d'usage
    # anodin en français — pas de sens sportif, pas d'idiome.
    "répression", "répressions", "répressif", "répressive",
    "répressives", "lois répressives", "подавление", "подавления",
    # Constructions sans ambiguïté possible, relevées sur des titres
    # HRW que rien n'ancrait : "Turkmenistan Forcibly Hospitalizes
    # Human Rights Defender", "Azerbaijan Rearrests Journalist
    # Forcibly Returned from Georgia".
    "forcibly hospitalizes", "forcibly hospitalized",
    "forcibly hospitalised", "forcibly returned", "forcibly deported",
    "forcibly evicted", "forcibly detained",
    # "<rôle> targeted" : le rôle porte la spécificité, pas le verbe.
    "human rights defenders targeted", "defenders targeted",
    "journalists targeted", "activists targeted", "lawyers targeted",
    # Ajoutés le 2026-09-14. Diagnostic : des articles que la
    # catégorisation décrit parfaitement — "Kazakhstan: Crackdown on
    # Government Critics" ressort acteur=opposant,
    # traitement=pression_administrative — restaient plafonnés à 34
    # (LEVEL_C_MIN_SCORE - 1) faute d'ancrage HR principal. La liste
    # contenait "political crackdown" mais pas "crackdown" nu.
    #
    # Mesuré avant ajout : 18 titres du corpus contiennent "crackdown",
    # les 18 sont des contextes de répression ("opposition faces
    # crackdown", "unprecedented crackdown on free press",
    # "dissidents fear crackdown in Turkish exile").
    "crackdown", "crackdowns", "разгон", "répression policière",
    # Formule standard des rapports HRW/Amnesty, absente : 3 titres,
    # 3 justes ("POWs Abused in Custody", "Farmers Exploited, Abused").
    "abused in custody", "abuse in custody", "ill-treatment",
    "ill treatment", "mistreated", "mistreatment",
    "жестокое обращение", "maltraité", "mauvais traitements",
    # "disappeared" et "missing after" NUS ont été mesurés puis
    # REJETÉS : 3 des 5 titres étaient faux — "The Aral Sea has all
    # but disappeared", "130 missing after ferry sinks". Seules les
    # formes qualifiées entrent.
    "forcibly disappeared", "enforced disappearance", "porté disparu",
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
    # Français, ajouté le 2026-09-17 : la forme existait déjà en
    # anglais et en russe, pas en français — "Ouzbékistan : Le
    # calvaire des prisonniers politiques" (HRW) restait à 23 (E)
    # faute de primary_political_prisoner, malgré une géographie et
    # un ancrage confirmés. Passe à 45 (C) une fois ajouté.
    "prisonnier politique", "prisonniers politiques",
]

DEMOCRACY_CIVIC_SPACE_TERMS_V9 = [
    "democracy score", "democratic decline", "democracy decline",
    "civic space", "shrinking civic space", "civil society restrictions",
    "political pluralism", "political participation", "democratic backsliding",
    "демократия", "снижение демократии", "гражданское пространство",
    "ограничение гражданского общества", "политический плюрализм",
]

TARGET_TERMS_V9 = [
    # Ajoutés le 2026-09-14. Diagnostic : les titres HRW en français
    # gagnaient bien un ancrage répressif (voir REPRESSION_TERMS_V9)
    # mais restaient à 25 points, faute de CIBLE. "Azerbaïdjan :
    # Répression virulente contre les détracteurs du gouvernement"
    # n'avait personne à qui rattacher la répression.
    #
    # Audit des titres réellement déclenchés sur les 9556 articles :
    #
    #   protester / protesters   8 titres, 8 justes
    #   détracteur(s)            1 titre,  1 juste
    #   manifestant(s)           1 titre,  1 juste
    #   opposant(s)              1 titre,  1 juste
    #
    # Ce sont des rôles pour lesquels on se fait arrêter, pas des
    # catégories de population — la ligne tenue depuis le début.
    #   opposant (singulier)     1 faux sur 2   REJETÉ
    #
    # Le singulier "opposant" est aussi le participe présent du verbe
    # opposer : "une querelle de voisinage opposant un éleveur au
    # maire" n'a rien d'un opposant politique. Le pluriel, lui, est
    # sûr — un participe présent est invariable, donc "opposants" ne
    # peut être que le nom.
    "protester", "protesters", "détracteur", "détracteurs",
    "manifestant", "manifestants", "opposants", "opposant politique",
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
     "activiste", "activistes",
    "défenseur des droits humains", "défenseurs des droits humains",
    "défenseur des droits de l'homme", "défenseurs des droits de l'homme",
    "journaliste", "journalistes", "avocat", "avocate", "avocats",
    "blogueur", "blogueuse", "blogueurs", "société civile", "ong",
    # Ajoutés le 2026-09-14, en miroir des acteurs ouverts dans
    # categorisation.py : une cible que le scoring ne connaît pas ne
    # peut pas entrer en relation avec une action répressive, donc
    # l'article reste sans ancrage quoi qu'il décrive.
    "political prisoner", "political prisoners", "detainee", "detainees",
    "prisoner of conscience", "prisoners of conscience",
    "professor", "academic", "academics", "scholar",
    "writer", "writers", "poet", "artist", "artists", "filmmaker",
    "prisonnier politique", "prisonniers politiques", "détenu",
    "universitaire", "professeur", "écrivain", "poète", "artiste",
    "политзаключенный", "политзаключенные", "ученый", "профессор",
    "писатель", "поэт", "художник",
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
    # Modes de répression ouverts le 2026-09-14 côté catégorisation
    # (surveillance, psychiatrie punitive, interdiction de sortie,
    # exil contraint). Sans eux ici, un article décrivant une
    # surveillance de masse ou un internement forcé n'avait aucune
    # action répressive reconnue, donc aucune relation cible/action.
    "surveilled", "wiretapped", "spied on", "under surveillance",
    "exiled", "driven into exile", "barred from leaving",
    "forcibly committed", "forcibly injected",
    "surveillé", "mis sur écoute", "exilé", "interné",
    "под наблюдением", "прослушивал", "выслан", "изгнан",
    "принудительно госпитализирован",
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


# La détection de texte (normalisation, cache de regex, recherche de
# termes, morphologie russe, détection de langue) vit désormais dans
# matching.py, partagée avec categorisation.py — voir l'entête de ce
# module. Ne restent ici que les maths de score.


def capped_add(current, value, maximum):
    return min(current + value, maximum)


def weighted_score(terms, weights, maximum):
    score = 0
    for term in terms:
        score += weights.get(normalize(term), 2)
    return min(score, maximum)

# ============================================================
# DÉCISIONS DÉRIVÉES DES SIGNAUX
# ============================================================
#
# Niveau, priorité, thème et pertinence ne regardent QUE le score et le
# dict de signaux produit par la détection. Les isoler de
# classify_article() (864 lignes, 116 variables locales) rend testable
# ce qui change le plus souvent — les règles éditoriales — sans toucher
# à la détection, et rejoint la séparation déjà en place entre
# categorisation.py (les faits) et regles_editoriales.py (les choix).


# Seuils de score. Un article doit franchir le seuil ET porter un
# signal confirmé de la liste ci-dessous pour atteindre A : le score
# seul suffisait autrefois, ce qui faisait monter en A des articles
# très scorés sans aucune cible identifiée.
LEVEL_A_MIN_SCORE = 75
LEVEL_B_MIN_SCORE = 55
LEVEL_C_MIN_SCORE = 35

_LEVEL_A_CONFIRMATIONS = (
    "confirmed_activist_pressure",
    "confirmed_journalist_pressure",
    "severe_detected",
    "confirmed_repression",
    "primary_forced_labor",
    "primary_lgbt_pressure",
    "primary_press",
    "critical_hr_case",
)


def decide_level(score, signals):
    """
    Niveau A-F.

    Hors région, un article portant tout de même un vrai signal droits
    humains (ex. HRW sur un défenseur en Iran ou au Rwanda) tombe en D
    plutôt que dans le bruit ; E regroupe tout le reste.

    F est à part : ce ne sont pas des articles faibles mais des pages
    de rubrique (pays, région, thème) et du mobilier de site — "Burkina
    Faso" chez CPJ, "Cookie Statement" chez Amnesty. Les mettre en E
    revenait à dire "article sans intérêt" d'une page qui n'est pas un
    article ; et comme certaines sont longues et bien remplies, elles
    remontaient parfois au-dessus de vrais sujets. F les sort du
    classement sans les supprimer : elles restent auditables.

    Décidé en premier, avant même le contexte régional : une page pays
    mentionne évidemment son pays, donc les tests de géographie la
    valideraient à tort.
    """
    if signals.get("section_page"):
        return "F"

    if not signals.get("regional_context"):
        return "D" if signals.get("global_hr_signal") else "E"

    if signals.get("non_news") or signals.get("noise"):
        return "E"

    if score >= LEVEL_A_MIN_SCORE and any(
        signals.get(key) for key in _LEVEL_A_CONFIRMATIONS
    ):
        return "A"

    if score >= LEVEL_B_MIN_SCORE:
        return "B"

    if score >= LEVEL_C_MIN_SCORE:
        return "C"

    return "E"


_PRIORITY_THRESHOLDS = (
    (90, "ABSOLUE"),
    (75, "TRÈS HAUTE"),
    (60, "HAUTE"),
    (40, "MOYENNE"),
    (20, "FAIBLE"),
)


def decide_priority(score):
    """Libellé de priorité, fonction du seul score."""
    for minimum, label in _PRIORITY_THRESHOLDS:
        if score >= minimum:
            return label

    return "BRUIT"


# Thèmes par ordre de priorité : le premier signal présent gagne. Une
# table plutôt qu'une cascade de `elif` — l'ordre reste la règle, mais
# il devient lisible d'un coup d'œil et modifiable sans toucher au code.
_THEME_RULES = (
    ("confirmed_activist_pressure", "Activistes / dissidents sous pression"),
    ("confirmed_journalist_pressure", "Journalistes sous pression"),
    ("primary_event_anchor", "Événement HR / répression régionale"),
    ("primary_transnational", "Répression transnationale"),
    ("primary_gender", "Droits des femmes / violences"),
    ("confirmed_repression", "Répression / droits humains"),
    ("has_specific_rights", "Droits spécifiques"),
    ("primary_political_context", "État de droit / espace civique"),
    ("primary_democracy", "État de droit / espace civique"),
    ("domestic", "Politique intérieure"),
    ("major_geo", "Géopolitique majeure"),
    ("historical", "Histoire / culture / contexte"),
    ("non_news", "Contenu institutionnel"),
    ("routine_geo", "Économie / géopolitique ordinaire"),
)


def decide_theme(signals):
    """Thème d'affichage : premier signal présent dans l'ordre de priorité."""
    for key, theme in _THEME_RULES:
        if signals.get(key):
            return theme

    return "Faible priorité"


RELEVANCE_MIN_SCORE = 40

_RELEVANCE_SIGNALS = (
    "has_activist",
    "has_journalist",
    "has_repression",
    "has_specific_rights",
    "has_human_rights",
    "major_geo",
    "primary_event_anchor",
    "primary_gender",
    "primary_political_context",
    "primary_democracy",
)


def decide_relevance(score, signals):
    """
    Article retenu pour la sélection du jour.

    Une pression confirmée sur un activiste ou un journaliste passe
    outre le seuil de score : c'est le cœur éditorial du scanner, il ne
    doit jamais être écarté pour quelques points.
    """
    if signals.get("confirmed_activist_pressure") or signals.get(
        "confirmed_journalist_pressure"
    ):
        return True

    return bool(
        signals.get("regional_context")
        and score >= RELEVANCE_MIN_SCORE
        and not signals.get("non_news")
        and not signals.get("noise")
        and any(signals.get(key) for key in _RELEVANCE_SIGNALS)
    )


def classify_article(article):
    title = normalize(article.get("title", ""))
    summary = normalize(article.get("summary", ""))
    body = normalize(article.get("body", ""))

    source_text = normalize(article.get("source", ""))
    link_text = normalize(article.get("link", article.get("url", "")))
    source_context = source_text + " " + link_text

    # Sur l'URL BRUTE, pas normalisée : la comparaison porte sur le
    # dernier segment du chemin, que normalize() abîmerait.
    section_page = looks_like_section_page(
        article.get("url") or article.get("link") or "",
        article.get("title") or "",
    )

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
    resolved_language = resolve_language(article.get("language"), full_text)
    article["language"] = resolved_language

    is_russian_source = resolved_language == "ru"
    is_farsi_source = resolved_language == "fa"

    central_asia = find_central_asia_terms(
        headline, CENTRAL_ASIA_TERMS, resolved_language
    )
    caucasus = find_caucasus_terms(headline, CAUCASUS_TERMS, resolved_language)
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
        find_central_asia_terms(body, CENTRAL_ASIA_TERMS, resolved_language)
        + find_caucasus_terms(body, CAUCASUS_TERMS, resolved_language)
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

    has_detention = bool(compiled(
        r"\b(detained|detention|arrested|arrest|задерж\w*|арест\w*)\b", re.I
    ).search(full_text))
    has_imprisonment = bool(compiled(
        r"\b(imprisoned|imprisonment|prison sentence|sentenced|осужден\w*|приговор\w*|заключ\w*)\b",
        re.I
    ).search(full_text))
    has_censorship = bool(compiled(r"(censorship|censored|цензур\w*)", re.I).search(full_text))
    has_government_involvement = bool(compiled(
        r"\b(government|authorities|state|government-backed|ilo|правительство|власти|государств\w*)\b",
        re.I
    ).search(full_text))

    has_restriction = bool(compiled(
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
        compiled(r"\blgbt\w*|\bqueer\b", re.I).search(primary_hr_text)
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

    severe_morphology = bool(compiled(
        r"(?:пыточ\w*\s+услов\w*|\bшизо\b|\bкарцер\b|произволь\w*\s+задерж\w*)",
        re.I
    ).search(full_text))

    severe_detected = bool(
        severe_morphology
        or any(normalize(x) in full_text for x in SEVERE_REPRESSION_TERMS)
    )

    prison_sentence_signal = bool(compiled(
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

    has_sco = bool(compiled(
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
        # Ces plafonds valaient 55 et 35 : exactement LEVEL_B_MIN_SCORE
        # et LEVEL_C_MIN_SCORE. Un plafond posé SUR un seuil ne retient
        # rien, il promeut — le test est ">=", donc l'article plafonné
        # atteint pile le niveau qu'on voulait lui refuser. Mesuré le
        # 2026-09-14 avant correction : 85 des 102 articles de niveau B
        # étaient à exactement 55/100, et 41 des 106 en C à exactement
        # 35/100. D'où un changement d'indicatif téléphonique, la mort
        # d'un acteur ou un trafiquant de MDMA en niveau B.
        #
        # Un cran en dessous du seuil, donc, pour que le plafond fasse
        # ce que son nom dit.
        if target_repression_relation or body_strong_hr_confirmation:
            score = min(score, LEVEL_B_MIN_SCORE - 1)
            reasons.append("plafond V9: confirmation HR dans le body")
        elif any(phrase_present(primary_hr_text, x) for x in GENERIC_REFORM_TERMS_V7):
            score = min(score, LEVEL_C_MIN_SCORE - 1)
            reasons.append("plafond V9: réforme générale")
        elif any(phrase_present(primary_hr_text, x) for x in NON_HR_TOPIC_TERMS_V7):
            score = min(score, 28)
            reasons.append("plafond V9: sujet non-HR")
        else:
            score = min(score, LEVEL_C_MIN_SCORE - 1)
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
    # SIGNAUX — sortie explicite de la phase de détection
    # ========================================================
    #
    # Construits ici, avant les décisions qui en découlent :
    # niveau, thème, priorité et pertinence sont désormais des
    # fonctions pures de (score, signals). Elles étaient quatre
    # cascades de `if` au milieu de 116 variables locales, donc
    # intestables isolément — alors que ce sont précisément les
    # règles éditoriales, celles qui bougent le plus souvent.

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

    signals = {
        "section_page": section_page,
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

        "global_hr_signal": global_hr_signal,
    }

    level = decide_level(score, signals)
    priority = decide_priority(score)
    theme = decide_theme(signals)
    relevant = decide_relevance(score, signals)

    article["score"] = score
    article["level"] = level
    article["priority"] = priority
    article["theme"] = theme
    article["reasons"] = reasons
    article["relevant"] = relevant
    article["signals"] = signals

    return article
