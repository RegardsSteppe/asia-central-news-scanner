# keywords.py

# ============================================================
# GEOGRAPHIE
# ============================================================

CENTRAL_ASIA_TERMS = [
    "central asia",
    "central asian",

    "kazakhstan",
    "kazakh",
    "kazakhs",

    "kyrgyzstan",
    "kyrgyz",
    "kirghizstan",
    "kirghiz",

    "tajikistan",
    "tajik",
    "tadjikistan",
    "tadjik",

    "turkmenistan",
    "turkmen",

    "uzbekistan",
    "uzbek",
    "ouzbekistan",
    "ouzbek",

    "karakalpakstan",
    "karakalpak",

    # Russian
    "центральная азия",
    "центральноазиат",
    "казахстан",
    "казах",
    "киргизстан",
    "кыргызстан",
    "киргиз",
    "кыргыз",
    "таджикистан",
    "таджик",
    "туркменистан",
    "туркмен",
    "узбекистан",
    "узбек",
    "каракалпакстан",
]


# ============================================================
# NIVEAU A — SIGNAUX CRITIQUES
# ============================================================

CRITICAL_HR_TERMS = [

    "political prisoner",
    "political prisoners",

    "political arrest",
    "political arrests",

    "politically motivated arrest",

    "journalist arrested",
    "journalists arrested",

    "journalist detained",
    "journalists detained",

    "journalist imprisoned",
    "journalists imprisoned",

    "activist arrested",
    "activists arrested",

    "activist detained",
    "activists detained",

    "dissident arrested",
    "dissidents arrested",

    "opposition activist",
    "opposition activists",

    "political crackdown",
    "political repression",

    "media crackdown",
    "press crackdown",

    "press freedom",
    "freedom of the press",

    "media pressure",

    "travel ban",
    "travel bans",

    "criminal case",
    "criminal cases",

    "prosecution",
    "prosecuted",

    "persecuted",
    "persecution",

    "torture",
    "tortured",

    "ill-treatment",
    "abuse in custody",

    "forced confession",
    "forced confessions",

    "repression of activists",
    "repression of journalists",

    "civil society crackdown",
    "ngo crackdown",
    "ngo repression",

    # Russian
    "политический заключенный",
    "политические заключенные",
    "политический арест",
    "политические аресты",
    "журналист арестован",
    "журналисты арестованы",
    "журналист задержан",
    "журналисты задержаны",
    "активист арестован",
    "активисты арестованы",
    "политические репрессии",
    "репрессии",
    "пытки",
    "преследование журналистов",
    "преследование активистов",
    "запрет на выезд",
    "уголовное дело",
    "уголовные дела",

    # French
    "prisonnier politique",
    "prisonniers politiques",
    "arrestation politique",
    "journaliste arrêté",
    "journalistes arrêtés",
    "militant arrêté",
    "militants arrêtés",
    "dissident arrêté",
    "répression politique",
    "répression",
    "liberté de la presse",
    "interdiction de voyager",
    "affaire pénale",
]


# ============================================================
# NIVEAU A — DROITS HUMAINS
# ============================================================

STRONG_HR_TERMS = [

    "human rights",
    "human rights violations",
    "rights violations",
    "rights abuse",

    "civil rights",

    "freedom of expression",
    "freedom of speech",
    "freedom of assembly",
    "freedom of association",

    "activist",
    "activists",

    "dissident",
    "dissidents",

    "human rights defender",
    "human rights defenders",

    "journalist",
    "journalists",

    "independent journalist",
    "independent media",

    "opposition",
    "political opposition",

    "civil society",
    "ngo",

    "press freedom",
    "censorship",
    "internet censorship",
    "blocked website",

    # Russian
    "права человека",
    "нарушение прав человека",
    "правозащитник",
    "правозащитники",
    "активист",
    "активисты",
    "диссидент",
    "журналист",
    "журналисты",
    "оппозиция",
    "гражданское общество",
    "цензура",
    "свобода слова",
    "свобода прессы",

    # French
    "droits humains",
    "droits de l'homme",
    "violations des droits",
    "défenseur des droits",
    "militant",
    "militants",
    "dissident",
    "journaliste",
    "journalistes",
    "opposition",
    "société civile",
    "censure",
    "liberté d'expression",
    "liberté de la presse",
]


# ============================================================
# NIVEAU B — POLITIQUE INTÉRIEURE
# ============================================================

DOMESTIC_POLITICAL_TERMS = [

    "election",
    "elections",
    "parliamentary election",
    "presidential election",
    "parliamentary vote",

    "parliament",
    "parliamentary",

    "constitution",
    "constitutional reform",
    "constitutional changes",

    "political reform",
    "political reforms",

    "president",
    "presidential",

    "government reshuffle",
    "cabinet reshuffle",

    "opposition party",
    "opposition parties",

    "political party",
    "political parties",

    "protest",
    "protests",

    "demonstration",
    "demonstrations",

    "rally",

    "pro-democracy",

    "referendum",

    "legislative vote",

    # Russian
    "выборы",
    "парламентские выборы",
    "президентские выборы",
    "парламент",
    "конституция",
    "конституционная реформа",
    "политическая реформа",
    "президент",
    "правительство",
    "оппозиционная партия",
    "политическая партия",
    "протест",
    "протесты",
    "митинг",
    "референдум",

    # French
    "élection",
    "élections",
    "élections législatives",
    "élection présidentielle",
    "parlement",
    "constitution",
    "réforme constitutionnelle",
    "réforme politique",
    "président",
    "gouvernement",
    "parti d'opposition",
    "manifestation",
    "manifestations",
    "référendum",
]


# ============================================================
# NIVEAU C — GÉOPOLITIQUE EXCEPTIONNELLE
# ============================================================

MAJOR_REGIONAL_EVENTS = [

    # SCO
    "shanghai cooperation organization",
    "sco summit",
    "sco leaders",
    "sco heads of state",
    "sco meeting",
    "sco summit",
    "sco at",
    "шос",
    "шанхайская организация сотрудничества",

    # Conflits
    "armed conflict",
    "major conflict",
    "military escalation",
    "war",
    "ceasefire",
    "peace agreement",

    "border conflict",
    "border clashes",
    "border crisis",

    "terrorist attack",
    "major security crisis",

    # Sanctions
    "major sanctions",
    "new sanctions",
    "sanctions against",
    "sanctions imposed",

    # Crises diplomatiques
    "diplomatic crisis",
    "diplomatic dispute",
    "diplomatic rupture",
    "expelled ambassador",
    "ambassador expelled",

    # Changements stratégiques
    "strategic partnership",
    "strategic realignment",
    "major strategic shift",
    "security alliance",
    "military alliance",
]


# ============================================================
# GÉOPOLITIQUE / ÉCONOMIE ORDINAIRE
# ============================================================

ROUTINE_GEO_TERMS = [

    "trade",
    "trading",

    "investment",
    "investments",

    "gas",
    "oil",
    "uranium",

    "pipeline",
    "railway",
    "railroad",

    "road corridor",
    "trade corridor",
    "transport corridor",

    "logistics",

    "energy cooperation",
    "economic cooperation",

    "business forum",
    "investment forum",
    "economic forum",

    "memorandum",
    "memorandum of understanding",

    "delegation",
    "official visit",

    "bilateral talks",
    "bilateral meeting",

    "economic partnership",
]


# ============================================================
# ACTEURS EXTÉRIEURS
# ============================================================

REGIONAL_ACTORS = [

    "russia",
    "russian",
    "kremlin",
    "putin",

    "china",
    "chinese",
    "beijing",
    "xi jinping",

    "afghanistan",
    "afghan",

    "iran",
    "iranian",

    "turkey",
    "turkish",

    "azerbaijan",
    "armenia",
    "georgia",

    "european union",
    "eu",

    "united states",
    "us",
    "washington",
]


# ============================================================
# CONTENU NON JOURNALISTIQUE
# ============================================================

NON_NEWS_TERMS = [

    "vacancy",
    "vacancies",
    "job opening",
    "job openings",
    "hiring",
    "we are hiring",
    "careers",

    "employment opportunity",
    "job opportunity",
    "apply now",

    "call for applications",

    "project evaluator",
    "project evaluation",

    "request for proposals",
    "tender",

    "grant opportunity",
    "funding opportunity",

    "workshop",
    "webinar",
    "training",

    "conference registration",
    "event registration",

    "project results",
    "annual report",

    # Russian
    "вакансия",
    "вакансии",
    "требуется",
    "прием на работу",
    "грант",
    "тендер",
    "семинар",
    "вебинар",
    "тренинг",

    # French
    "offre d'emploi",
    "offres d'emploi",
    "recrutement",
    "poste à pourvoir",
    "appel à candidatures",
    "atelier",
    "webinaire",
    "formation",
    "rapport annuel",
]


# ============================================================
# BRUIT
# ============================================================

BUSINESS_SPORTS_TECH_TERMS = [

    "football",
    "soccer",
    "basketball",
    "boxing",
    "tennis",
    "olympics",
    "championship",
    "match",
    "player",
    "coach",

    "iphone",
    "android",
    "smartphone",

    "software release",
    "app launch",

    "startup funding",
    "cryptocurrency",
    "stock market",
]
