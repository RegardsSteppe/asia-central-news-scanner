# ============================================================
# KEYWORDS — VEILLE ASIE CENTRALE / ACTIVISTES / DROITS HUMAINS
# VERSION 3 — détection renforcée
# ============================================================


# ============================================================
# 1. GÉOGRAPHIE — ASIE CENTRALE
# ============================================================

HUMAN_RIGHTS_DEFENDER_TERMS = [
    "human rights defender",
    "human rights defenders",
    "human rights activist",
    "human rights activists",
    "rights defender",
    "rights defenders",
    "rights activist",
    "rights activists",
    "human rights lawyer",
    "human rights lawyers",

    # Russe
    "правозащитник",
    "правозащитники",
    "правозащитница",
    "правозащитницы",
    "правозащитник и журналист",
    "правозащитница и журналист",
    "правозащитник-юрист",
    "правозащитница-юрист",
    "адвокат по правам человека",
]


FORCED_LABOR_TERMS = [
    "forced labor",
    "forced labour",
    "forced work",
    "forced workers",
    "child labor",
    "child labour",
    "cotton quotas",
    "forced cotton picking",
    "forced cotton harvest",
    "forced agricultural labor",
    "forced agricultural labour",

    "принудительный труд",
    "принудительные работы",
    "принудительный сбор хлопка",
    "принудительный труд на сборе хлопка",
    "принудительный сбор урожая",
    "принудительная уборка урожая",
    "квоты на производство и сбор хлопка",
    "детский труд",
]


CENTRAL_ASIA_TERMS = [
    "central asia",
    "central asian",

    # Kazakhstan
    "kazakhstan",
    "kazakh",
    "kazakhs",

    # Kyrgyzstan
    "kyrgyzstan",
    "kyrgyz",
    "kirghizstan",
    "kirghiz",

    # Tajikistan
    "tajikistan",
    "tajik",
    "tadjikistan",
    "tadjik",

    # Turkmenistan
    "turkmenistan",
    "turkmen",

    # Uzbekistan
    "uzbekistan",
    "uzbek",
    "ouzbekistan",
    "ouzbek",

    # Karakalpakstan
    "karakalpakstan",
    "karakalpak",

    # Villes
    "almaty",
    "astana",
    "nur-sultan",
    "nur sultan",
    "shymkent",

    "bishkek",
    "osh",
    "jalal-abad",
    "jalalabad",

    "dushanbe",
    "khujand",
    "khorog",

    "ashgabat",
    "turkmenabat",

    "tashkent",
    "samarkand",
    "bukhara",
    "fergana",
    "andijan",
    "nukus",

    # Russe
    "центральная азия",
    "центральноазиат",
    "казахстан",
    "казах",
    "казахи",
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
    "каракалпак",

    "алматы",
    "астана",
    "шымкент",
    "бишкек",
    "ош",
    "джалал-абад",
    "душанбе",
    "худжанд",
    "хорог",
    "ашхабад",
    "туркменабат",
    "ташкент",
    "ташкенте",
    "самарканд",
    "бухара",
    "фергана",
    "ферганы",
    "андижан",
    "нукус",
]


# ============================================================
# 2. GÉOGRAPHIE — CAUCASE
# ============================================================

CAUCASUS_TERMS = [
    "georgia",
    "georgian",
    "armenia",
    "armenian",
    "azerbaijan",
    "azerbaijani",
    "south caucasus",
    "caucasus",

    "грузия",
    "грузин",
    "армения",
    "армян",
    "азербайджан",
    "азербайджанский",
    "южный кавказ",
    "кавказ",
]


# ============================================================
# 3. DROITS HUMAINS — GÉNÉRAL
# ============================================================

HUMAN_RIGHTS_TERMS = [
    "human rights",
    "human rights violation",
    "human rights violations",
    "rights violation",
    "rights violations",

    "civil rights",
    "political rights",

    "freedom of expression",
    "freedom of speech",
    "freedom of assembly",
    "freedom of association",
    "freedom of religion",
    "freedom of movement",
    "freedom of information",

    "press freedom",
    "freedom of the press",
    "media freedom",

    "civil society",

    "human rights defender",
    "human rights defenders",
    "rights defender",
    "rights defenders",

    # Russe
    "права человека",
    "нарушение прав человека",
    "нарушения прав человека",
    "гражданские права",
    "политические права",
    "свобода слова",
    "свобода выражения",
    "свобода собраний",
    "свобода объединений",
    "свобода вероисповедания",
    "свобода передвижения",
    "свобода прессы",
    "свобода информации",
    "правозащитник",
    "правозащитники",
    "гражданское общество",
]


# ============================================================
# 4. ACTIVISTES / DISSIDENTS / OPPOSITION / SOCIÉTÉ CIVILE
# ============================================================

ACTIVIST_TERMS = [
    "activist",
    "activists",

    "human rights activist",
    "human rights activists",

    "civil society activist",
    "civil society activists",

    "political activist",
    "political activists",

    "opposition activist",
    "opposition activists",

    "opposition figure",
    "opposition figures",
    "opposition politician",
    "opposition politicians",
    "opposition leader",
    "opposition leaders",

    "government critic",
    "government critics",
    "political critic",
    "political critics",

    "dissident",
    "dissidents",

    "human rights defender",
    "human rights defenders",

    "civil society organization",
    "civil society organizations",
    "civil society group",
    "civil society groups",

    "ngo",
    "ngos",
    "non-governmental organization",
    "non-governmental organizations",

    "lawyer",
    "lawyers",
    "human rights lawyer",
    "human rights lawyers",

    # Russe
    "активист",
    "активисты",
    "активистка",
    "активистки",
    "правозащитник",
    "правозащитники",
    "правозащитница",
    "правозащитницы",
    "диссидент",
    "диссиденты",
    "политический активист",
    "политические активисты",
    "общественный активист",
    "общественные активисты",
    "общественный деятель",
    "общественные деятели",
    "оппозиционер",
    "оппозиционеры",
    "оппозиционный политик",
    "оппозиционные политики",
    "лидер оппозиции",
    "лидеры оппозиции",
    "критик власти",
    "критики власти",
    "критик правительства",
    "критики правительства",
    "адвокат",
    "адвокаты",
]


# ============================================================
# 5. RÉPRESSION — FORTE
# ============================================================

REPRESSION_TERMS = [

    # Arrestation / détention
    "arrested",
    "arrest",
    "arrests",
    "detained",
    "detention",
    "detentions",
    "detain",
    "taken into custody",
    "held in custody",
    "held without charge",
    "arbitrary detention",
    "arbitrarily detained",
    "detained without charge",
    "in custody",

    # Prison
    "prison",
    "prisons",
    "prisoner",
    "prisoners",
    "imprisoned",
    "imprisonment",
    "jailed",
    "jail",
    "prison sentence",
    "prison term",
    "sentenced to prison",
    "serving a sentence",
    "serving a prison sentence",
    "behind bars",
    "solitary confinement",
    "punitive isolation",
    "prison conditions",
    "detention conditions",
    "inhuman conditions",
    "torturous conditions",

    # Condamnation
    "convicted",
    "conviction",
    "sentenced",
    "sentence",

    # Justice pénale
    "criminal case",
    "criminal cases",
    "criminal prosecution",
    "criminal prosecutions",
    "prosecuted",
    "prosecution",
    "prosecutions",
    "charged with",
    "criminal charges",
    "charges filed",
    "charges brought",

    # Procès
    "trial",
    "trials",
    "closed-door trial",
    "closed door trial",
    "secret trial",

    # Torture / mauvais traitements
    "torture",
    "tortured",
    "ill-treatment",
    "mistreatment",
    "abuse in custody",
    "police abuse",
    "custodial abuse",

    # Violence / menaces
    "attacked",
    "physically attacked",
    "assaulted",
    "beaten",
    "beaten up",
    "threatened",
    "death threats",
    "intimidated",
    "intimidation",
    "harassed",
    "harassment",
    "persecuted",
    "persecution",

    # Disparitions / enlèvements
    "disappeared",
    "forcibly disappeared",
    "enforced disappearance",
    "forced disappearance",
    "missing in custody",
    "abducted",
    "abduction",
    "kidnapped",
    "kidnapping",

    # Restrictions
    "travel ban",
    "travel bans",
    "exit ban",
    "banned from leaving",
    "barred from leaving",
    "prevented from leaving",
    "passport confiscated",
    "passport revoked",
    "travel restricted",
    "movement restricted",

    # Pression / surveillance
    "surveillance",
    "under surveillance",
    "monitored by authorities",
    "pressure from authorities",
    "pressure by authorities",
    "official pressure",
    "blacklisted",
    "blacklisted journalist",
    "blacklisted activist",

    # Censure / Internet
    "censorship",
    "censored",
    "online censorship",
    "internet censorship",
    "website blocked",
    "website blocked by authorities",
    "social media blocked",
    "internet shutdown",
    "website shut down",
    "website taken down",
    "media outlet closed",
    "media outlet shut down",

    # Amendes / sanctions administratives
    "fined",
    "fine",
    "administrative fine",
    "administrative penalty",
    "penalty for criticism",

    # Répression politique
    "political prisoner",
    "political prisoners",
    "political repression",
    "political persecution",
    "political crackdown",
    "media crackdown",
    "press crackdown",
    "opposition crackdown",
    "opposition repression",
    "crackdown on activists",
    "crackdown on journalists",

    # Russe
    "политический заключенный",
    "политические заключенные",
    "политический арест",
    "политические аресты",
    "арестован",
    "арестована",
    "арестованы",
    "арест",
    "задержан",
    "задержана",
    "задержаны",
    "задержание",
    "тюрьма",
    "тюрьме",
    "заключен",
    "заключена",
    "заключены",
    "заключенный",
    "заключенные",
    "осужден",
    "осуждена",
    "осуждены",
    "приговорен",
    "приговорена",
    "приговорены",
    "уголовное дело",
    "уголовные дела",
    "уголовное преследование",
    "уголовные обвинения",
    "предъявлено обвинение",
    "предъявлены обвинения",
    "пытка",
    "пытки",
    "жестокое обращение",
    "избит",
    "избита",
    "избиты",
    "нападение",
    "напали",
    "угрозы",
    "угрозы убийством",
    "запугивание",
    "преследование",
    "преследуют",
    "преследуется",
    "похищен",
    "похищена",
    "похищение",
    "слежка",
    "наблюдение",
    "находится под наблюдением",
    "шизо",
    "сизо",
    "карцер",
    "одиночное заключение",
    "условия содержания",
    "пыточные условия",
    "жестокие условия содержания",
    "за решеткой",
    "за решёткой",
    "отбывает срок",
    "отбывает наказание",
    "содержится в заключении",
    "произвольное задержание",
    "задержание без предъявления обвинения",
    "насильственное исчезновение",
    "исчезновение",
    "запрет на выезд",
    "ограничение передвижения",
    "конфискация паспорта",
    "цензура",
    "блокировка сайта",
    "блокировка интернета",
    "закрытие СМИ",
    "закрытие сайта",
    "заблокирован сайт",
    "черный список",
    "чёрный список",
    "штраф",
    "оштрафован",
    "административный штраф",
    "репрессии",
    "политические репрессии",
]


# ============================================================
# 6. RÉPRESSION JURIDIQUE / ADMINISTRATIVE
# ============================================================

LEGAL_REPRESSION_TERMS = [
    "extremism charges",
    "extremism charge",
    "extremism law",
    "extremist organization",
    "extremist activity",

    "inciting unrest",
    "incitement to unrest",
    "inciting mass unrest",
    "mass unrest charges",

    "false information",
    "spreading false information",

    "defamation",
    "criminal defamation",

    "insulting the president",
    "insult to the president",

    "anti-government activity",
    "anti-government charges",
    "national security charges",

    "terrorism charges",
    "terrorist charges",

    "separatism charges",
    "separatist charges",

    "treason charges",

    "foreign agents law",
    "foreign agent law",
    "foreign representatives law",
    "foreign representative law",

    "foreign funding restrictions",

    "unauthorized protest",
    "illegal protest",
    "illegal assembly",

    "political persecution",
    "politically motivated charges",
    "politically motivated prosecution",
    "politically motivated trial",
    "retaliatory prosecution",
    "reprisal",
    "reprisals",
    "retaliation",

    "administrative detention",
    "administrative arrest",
    "administrative charges",
    "administrative offense",
    "administrative offence",

    "persecution of activists",
    "persecution of journalists",
    "penalized for criticism",
    "punished for criticism",

    # Russe
    "экстремизм",
    "экстремистская деятельность",
    "экстремистская организация",
    "экстремистское сообщество",
    "разжигание массовых беспорядков",
    "массовые беспорядки",
    "ложная информация",
    "распространение ложной информации",
    "клевета",
    "уголовная клевета",
    "оскорбление президента",
    "антиправительственная деятельность",
    "антиправительственная деятельность",
    "государственная измена",
    "терроризм",
    "сепаратизм",
    "иностранные агенты",
    "иностранный представитель",
    "иностранное финансирование",
    "несанкционированный митинг",

    "политическое преследование",
    "политически мотивированное обвинение",
    "политически мотивированное преследование",
    "политически мотивированный процесс",
    "преследование активистов",
    "преследование журналистов",
    "преследование за критику",
    "наказание за критику",
    "месть властей",

    "административный арест",
    "административное задержание",
    "административное дело",
    "административное правонарушение",
    "административный штраф",
]


# ============================================================
# 6bis. CONTEXTE JURIDIQUE / JUDICIAIRE
# ============================================================

LEGAL_CONTEXT_TERMS = [
    "court",
    "courts",
    "courtroom",
    "prosecutor",
    "prosecutors",
    "prosecutor's office",
    "judge",
    "judges",
    "verdict",
    "appeal",
    "appeals",
    "police",
    "law enforcement",
    "investigator",
    "investigators",
    "interrogation",
    "interrogated",
    "case",
    "case against",
    "criminal case against",
    "charges against",
    "indictment",
    "indicted",
    "alleged",
    "allegedly",
    "illegal",
    "illegally",
    "unlawful",
    "unlawfully",

    # Russe
    "суд",
    "суды",
    "прокурор",
    "прокуратура",
    "судья",
    "приговор",
    "апелляция",
    "полиция",
    "следователь",
    "следователи",
    "допрос",
    "дело",
    "дело против",
    "обвинение",
    "обвинения",
    "предъявлено обвинение",
    "предъявлены обвинения",
    "предполагаемый",
    "якобы",
    "незаконно",
    "незаконный",
]


# ============================================================
# 7. JOURNALISTES / MÉDIAS
# ============================================================

JOURNALIST_TERMS = [
    "journalist",
    "journalists",
    "reporter",
    "reporters",
    "editor",
    "editors",

    "independent journalist",
    "independent journalists",

    "investigative journalist",
    "investigative journalists",

    "photojournalist",
    "blogger",
    "bloggers",
    "blog",
    "media worker",
    "media workers",

    "independent media",
    "independent outlet",
    "independent news outlet",
    "media outlet",
    "news outlet",

    "editorial independence",
    "freelance journalist",
    "freelance journalists",
    "correspondent",
    "correspondents",

    # Russe
    "журналист",
    "журналисты",
    "репортер",
    "репортеры",
    "репортёр",
    "репортёры",
    "редактор",
    "редакторы",
    "блогер",
    "блогеры",
    "независимый журналист",
    "независимые журналисты",
    "независимое СМИ",
    "независимые СМИ",
    "СМИ",
    "корреспондент",
    "корреспонденты",
]


# ============================================================
# 8. DROITS SPÉCIFIQUES
# ============================================================

SPECIFIC_RIGHTS_TERMS = [

    # Femmes / genre
    "women's rights",
    "women rights",
    "gender equality",
    "gender discrimination",
    "gender-based discrimination",
    "gender-based violence",
    "violence against women",
    "violence against girls",
    "domestic violence",
    "sexual violence",
    "sexual harassment",
    "forced marriage",
    "child marriage",
    "bride kidnapping",
    "marriage by abduction",
    "kidnapping for marriage",
    "abduction for marriage",
    "feminist",
    "feminists",

    # Liberté académique
    "academic freedom",
    "academic freedoms",
    "academic repression",
    "academic persecution",
    "academic censorship",
    "professor arrested",
    "professor detained",
    "scholar arrested",
    "scholar detained",
    "researcher arrested",
    "researcher detained",
    "scholar at risk",
    "scholars at risk",

    # LGBT
    "lgbt",
    "lgbti",
    "lgbtq",
    "lgbt rights",
    "lgbti rights",
    "gay rights",
    "sexual orientation",
    "gender identity",
    "same-sex relations",
    "same-sex conduct",

    # Minorités
    "minority rights",
    "ethnic minority",
    "ethnic minorities",
    "religious minority",
    "religious minorities",
    "ethnic discrimination",
    "religious discrimination",

    # Enfants
    "children's rights",
    "child rights",
    "child abuse",
    "child labor",
    "child labour",

    # Travail forcé
    "forced labor",
    "forced labour",
    "forced workers",
    "forced work",

    # Migrants
    "migrant rights",
    "migrant workers",
    "labor migrants",
    "labour migrants",
    "refugee rights",
    "refugee protection",

    # Russe
    "академическая свобода",
    "академические свободы",
    "академические репрессии",
    "академическая цензура",
    "преследование ученых",
    "преследование учёных",
    "арест профессора",
    "задержание профессора",
    "ученый арестован",
    "учёный арестован",
    "ученый задержан",
    "учёный задержан",

    "права женщин",
    "гендерное равенство",
    "гендерная дискриминация",
    "насилие в отношении женщин",
    "домашнее насилие",
    "сексуальное насилие",
    "сексуальные домогательства",
    "принудительный брак",
    "детский брак",
    "похищение невесты",
    "похищение девушки",
    "похищение с целью брака",
    "феминист",
    "феминистка",

    "лгбт",
    "права меньшинств",
    "этническое меньшинство",
    "религиозное меньшинство",
    "этническая дискриминация",
    "религиозная дискриминация",
    "дискриминация",

    "права детей",
    "детский труд",
    "принудительный труд",

    "трудовые мигранты",
    "права мигрантов",
]


# ============================================================
# 9. SIGNAUX SPÉCIFIQUES ASIE CENTRALE / DROITS HUMAINS
# ============================================================

CENTRAL_ASIA_HR_TERMS = [

    # Kazakhstan
    "january 2022",
    "january events",
    "bloody january",
    "bloody january events",
    "qantar",
    "qantar events",
    "january tragedy",
    "january crackdown",
    "january killings",

    # Kyrgyzstan
    "foreign representatives law",
    "foreign agent law",
    "foreign agents law",
    "media law",
    "mass media law",
    "kloop",
    "kyrgyz media law",
    "ngo law",

    # Tajikistan
    "gorno-badakhshan",
    "gorno badakhshan",
    "gbao",
    "pamiri",
    "pamiris",
    "pamir",
    "khorog crackdown",
    "gbao crackdown",
    "gbao repression",

    # Turkmenistan
    "turkmen.news",
    "turkmen news",
    "turkmenistan journalist",
    "turkmenistan activist",
    "turkmenistan dissident",
    "political prisoner in turkmenistan",
    "internet censorship in turkmenistan",
    "vpn in turkmenistan",
    "turkmenistan censorship",
    "turkmenistan repression",
    "turkmenistan human rights",

    # Uzbekistan
    "karakalpakstan protests",
    "karakalpakstan unrest",
    "karakalpakstan crackdown",
    "karakalpakstan repression",
    "forced psychiatric treatment",
    "forced psychiatric detention",
    "psychiatric detention",
    "psychiatric treatment",
    "blogger in uzbekistan",
    "journalist in uzbekistan",
    "uzbekistan censorship",
    "uzbekistan repression",

    # Russe
    "январские события",
    "январь 2022",
    "кровавый январь",
    "январская трагедия",
    "январские протесты",
    "январские репрессии",
    "гбaо",
    "гбао",
    "горно-бадахшан",
    "памирцы",
    "памир",
    "репрессии в гбао",
    "подавление протестов в гбао",
    "каракалпакстан",
    "каракалпаки",
    "протесты в каракалпакстане",
    "подавление протестов",
]


# ============================================================
# 10. POLITIQUE INTÉRIEURE
# ============================================================

DOMESTIC_POLITICAL_TERMS = [
    "election",
    "elections",
    "electoral",
    "parliamentary election",
    "presidential election",
    "parliamentary vote",

    "parliament",
    "parliamentary",

    "constitution",
    "constitutional reform",
    "constitutional changes",
    "constitutional amendment",

    "political reform",
    "political reforms",

    "president",
    "presidential",
    "government",

    "cabinet reshuffle",
    "government reshuffle",

    "opposition party",
    "opposition parties",
    "political opposition",
    "political party",
    "political parties",

    "protest",
    "protests",
    "demonstration",
    "demonstrations",
    "rally",
    "rallies",
    "mass protest",
    "mass protests",

    "referendum",

    "political corruption",
    "corruption scandal",

    # Nouveaux signaux politiques utiles
    "power consolidation",
    "concentration of power",
    "executive power",
    "presidential powers",
    "political crackdown",
    "government critics",
    "political critics",
    "opposition crackdown",

    # Russe
    "выборы",
    "парламентские выборы",
    "президентские выборы",
    "парламент",
    "конституция",
    "конституционная реформа",
    "конституционные изменения",
    "политическая реформа",
    "президент",
    "правительство",
    "оппозиционная партия",
    "политическая оппозиция",
    "политическая партия",
    "протест",
    "протесты",
    "массовые протесты",
    "митинг",
    "митинги",
    "референдум",
    "концентрация власти",
    "расширение полномочий президента",
    "политические репрессии",
    "подавление оппозиции",
]


# ============================================================
# 11. GÉOPOLITIQUE MAJEURE
# ============================================================

MAJOR_GEOPOLITICAL_TERMS = [
    "shanghai cooperation organization",
    "shanghai cooperation organisation",
    "sco summit",
    "sco leaders",
    "sco heads of state",
    "sco meeting",

    "шанхайская организация сотрудничества",
    "шос",

    "armed conflict",
    "major conflict",
    "military escalation",

    "ceasefire",
    "peace agreement",

    "border conflict",
    "border clashes",
    "border crisis",

    "major security crisis",

    "terrorist attack",
    "terrorist attacks",

    "major sanctions",
    "new sanctions",
    "sanctions imposed",

    "diplomatic crisis",
    "diplomatic rupture",
    "diplomatic dispute",

    "ambassador expelled",
    "expelled ambassador",

    "strategic partnership",
    "strategic realignment",
    "major strategic shift",

    "security alliance",
    "military alliance",
    "military cooperation agreement",
]


# ============================================================
# 12. GÉOPOLITIQUE / ÉCONOMIE ORDINAIRE
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

    "economic partnership",

    "gdp",
    "gdp growth",
    "economic growth",
    "export",
    "exports",
    "import",
    "imports",
    "currency",
    "stock exchange",
    "tourism",
    "tourist",
    "agriculture",
    "harvest",

    # Russe
    "торговля",
    "инвестиции",
    "газ",
    "нефть",
    "уран",
    "трубопровод",
    "железная дорога",
    "экономическое сотрудничество",
    "бизнес-форум",
    "меморандум",
    "экспорт",
    "импорт",
    "туризм",
]


# ============================================================
# 12bis. CONTEXTE GÉNÉRIQUE / FAIBLE SIGNAL
# ============================================================

LOW_SIGNAL_CONTEXT_TERMS = [
    "delegation",
    "official visit",
    "bilateral talks",
    "bilateral meeting",
    "state visit",
    "meeting",
    "summit",
    "forum",
    "conference",
    "ceremony",
    "announcement",
    "statement",
    "international community",
    "authorities",
    "official",
    "officials",

    "делегация",
    "официальный визит",
    "двусторонние переговоры",
    "двусторонняя встреча",
    "государственный визит",
    "встреча",
    "саммит",
    "форум",
    "конференция",
    "церемония",
    "заявление",
    "международное сообщество",
    "власти",
    "официальный",
    "официальные лица",
]


# ============================================================
# 13. ACTEURS EXTÉRIEURS
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

    "european union",
    "eu",

    "united states",
    "washington",
]


# ============================================================
# 14. HISTOIRE / CULTURE
# ============================================================

HISTORICAL_TERMS = [
    "history",
    "historical",
    "historian",
    "century",
    "19th century",
    "20th century",
    "21st century",
    "ancient",

    "soviet era",
    "soviet period",
    "former soviet",
    "cold war",

    "biography",
    "biographical",
    "born in",
    "died in",
    "legacy",
    "heritage",

    "museum",
    "photography",
    "photographer",
    "book review",
    "film review",
    "archive",
    "archives",
]


# ============================================================
# 15. CONTENU NON JOURNALISTIQUE
# ============================================================

NON_NEWS_TERMS = [
    "vacancy",
    "vacancies",
    "job opening",
    "job openings",
    "hiring",
    "we are hiring",

    "career",
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

    # Russe
    "вакансия",
    "вакансии",
    "требуется",
    "прием на работу",
    "тендер",
    "грант",
    "семинар",
    "вебинар",
    "тренинг",

    # Français
    "offre d'emploi",
    "recrutement",
    "poste à pourvoir",
    "appel à candidatures",
    "atelier",
    "webinaire",
    "formation",
    "rapport annuel",
]


# ============================================================
# 16. BRUIT
# ============================================================

NOISE_TERMS = [
    "football",
    "soccer",
    "basketball",
    "boxing",
    "tennis",
    "olympics",

    "match",
    "player",
    "coach",

    "iphone",
    "android",
    "smartphone",

    "software release",
    "app launch",

    "cryptocurrency",
    "stock market",
]


# ============================================================
# 17. MOTS FORTS — RÉPRESSION
# ============================================================

SEVERE_REPRESSION_TERMS = [
    "torture",
    "tortured",
    "enforced disappearance",
    "forced disappearance",
    "forcibly disappeared",
    "political prisoner",
    "political prisoners",
    "political repression",
    "political persecution",
    "arbitrary detention",
    "solitary confinement",
    "inhuman conditions",
    "torturous conditions",
    "political crackdown",
    "opposition crackdown",
    "abducted",
    "abduction",
    "kidnapped",
    "kidnapping",

    # Russe
    "пытка",
    "пытки",
    "насильственное исчезновение",
    "политический заключенный",
    "политические заключенные",
    "политические репрессии",
    "политическое преследование",
    "произвольное задержание",
    "одиночное заключение",
    "пыточные условия",
    "пыточных условиях",
    "пыточном состоянии",
    "шизо",
    "карцер",
    "похищение",
    "похищен",
    "похищена",
    "репрессии",
]


# ============================================================
# 18. PATTERNS — RELATIONS ACTIVISTES
# ============================================================

ACTIVIST_REPRESSION_PATTERNS = [
    r"\bactivist\b.{0,150}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|serving|harassed|threatened|attacked|abducted|kidnapped|prosecuted|persecuted|blacklisted|fined)\b",
    r"\bactivists\b.{0,150}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|serving|harassed|threatened|attacked|abducted|kidnapped|prosecuted|persecuted|blacklisted|fined)\b",

    r"\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|serving|harassed|threatened|attacked|abducted|kidnapped|prosecuted|persecuted|blacklisted|fined)\b.{0,150}\bactivist\b",
    r"\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|serving|harassed|threatened|attacked|abducted|kidnapped|prosecuted|persecuted|blacklisted|fined)\b.{0,150}\bactivists\b",

    r"\bhuman rights defender\b.{0,150}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|serving|harassed|threatened|attacked|abducted|prosecuted|persecuted)\b",
    r"\bhuman rights defenders\b.{0,150}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|serving|harassed|threatened|attacked|abducted|prosecuted|persecuted)\b",

    r"\b(opposition figure|opposition politician|government critic|political critic)\b.{0,150}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|prosecuted|persecuted|threatened|attacked)\b",
]


# ============================================================
# 19. PATTERNS — RELATIONS JOURNALISTES
# ============================================================

JOURNALIST_REPRESSION_PATTERNS = [
    r"\bjournalist\b.{0,150}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|attacked|beaten|threatened|harassed|prosecuted|blacklisted|fined)\b",
    r"\bjournalists\b.{0,150}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|attacked|beaten|threatened|harassed|prosecuted|blacklisted|fined)\b",

    r"\breporter\b.{0,150}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|attacked|beaten|threatened|harassed|prosecuted|blacklisted|fined)\b",
    r"\breporters\b.{0,150}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|attacked|beaten|threatened|harassed|prosecuted|blacklisted|fined)\b",

    r"\bjournalist\b.{0,150}\b(censorship|censored|blocked|banned|closed|shut down)\b",
    r"\bindependent media\b.{0,150}\b(blocked|banned|closed|shut down)\b",
    r"\bmedia outlet\b.{0,150}\b(blocked|banned|closed|shut down)\b",
]


# ============================================================
# 20. PATTERNS — RUSSE / RELATIONS
# ============================================================

ACTIVIST_REPRESSION_RU_PATTERNS = [
    r"(активист|активисты|активистка|активистки|правозащитник|правозащитники|правозащитница|правозащитницы|диссидент|диссиденты|оппозиционер|оппозиционеры).{0,150}(арестован|арестована|арестованы|задержан|задержана|задержаны|осужден|осуждена|осуждены|заключен|заключена|заключены|приговорен|приговорена|приговорены|отбывает|содержится|посажен|посажена|преследуется|преследуют|угрожают|угрожал|избит|избита|избиты|напали|похищен|похищена|похищение|запугивают|запугивание|оштрафован|оштрафована|оштрафованы)",

    r"(арестован|арестована|арестованы|задержан|задержана|задержаны|осужден|осуждена|осуждены|заключен|заключена|заключены|приговорен|приговорена|приговорены|отбывает|содержится|посажен|посажена|преследуется|преследуют|угрожают|угрожал|избит|избита|избиты|напали|похищен|похищена|похищение|запугивают|запугивание|оштрафован|оштрафована|оштрафованы).{0,150}(активист|активисты|активистка|активистки|правозащитник|правозащитники|правозащитница|правозащитницы|диссидент|диссиденты|оппозиционер|оппозиционеры)",
]


JOURNALIST_REPRESSION_RU_PATTERNS = [
    r"(журналист|журналисты|репортер|репортеры|репортёр|репортёры|корреспондент|корреспонденты|блогер|блогеры).{0,150}(арестован|арестована|арестованы|задержан|задержана|задержаны|осужден|осуждена|осуждены|заключен|заключена|заключены|приговорен|приговорена|приговорены|отбывает|содержится|посажен|посажена|преследуется|преследуют|оштрафован|оштрафована|угрожают|угрожал|избит|избита|избиты|напали|похищен|похищена|запугивают)",

    r"(журналист|журналисты|репортер|репортеры|репортёр|репортёры|корреспондент|корреспонденты|блогер|блогеры).{0,150}(угроз|напад|избит|запрет|цензур|задерж|преслед|запуг|оштраф)",

    r"(арестован|арестована|арестованы|задержан|задержана|задержаны|осужден|осуждена|осуждены|приговорен|приговорена|приговорены|преследуется|преследуют).{0,150}(журналист|журналисты|репортер|репортеры|репортёр|репортёры|блогер|блогеры)",
]


# ============================================================
# 21. WEIGHTS — RÉPRESSION
# ============================================================

REPRESSION_WEIGHTS = {
    "torture": 10,
    "tortured": 10,
    "enforced disappearance": 10,
    "forced disappearance": 10,
    "forcibly disappeared": 10,
    "political prisoner": 10,
    "political prisoners": 10,
    "political persecution": 9,
    "political repression": 9,
    "political crackdown": 9,
    "opposition crackdown": 9,

    "imprisoned": 8,
    "imprisonment": 8,
    "jailed": 8,
    "jail": 7,
    "prison": 7,
    "prisons": 7,
    "prisoner": 7,
    "prisoners": 7,
    "prison sentence": 8,
    "prison term": 8,
    "sentenced to prison": 8,

    "arrested": 7,
    "arrest": 6,
    "arrests": 6,
    "detained": 7,
    "detention": 6,

    "convicted": 6,
    "conviction": 6,
    "sentenced": 6,

    "criminal prosecution": 5,
    "prosecuted": 5,
    "charged with": 5,
    "criminal charges": 5,

    "trial": 4,
    "closed-door trial": 5,
    "secret trial": 5,

    "travel ban": 4,
    "exit ban": 4,
    "passport confiscated": 4,

    "censorship": 3,
    "online censorship": 3,
    "internet censorship": 4,
    "website blocked": 3,
    "internet shutdown": 5,

    "police abuse": 6,
    "abuse in custody": 7,
    "custodial abuse": 7,

    "attacked": 5,
    "physically attacked": 6,
    "assaulted": 6,
    "beaten": 6,
    "beaten up": 6,
    "threatened": 4,
    "death threats": 6,
    "intimidated": 4,
    "intimidation": 4,

    "harassed": 4,
    "harassment": 4,
    "persecuted": 6,
    "persecution": 6,
    "abducted": 8,
    "abduction": 7,
    "kidnapped": 8,
    "kidnapping": 7,

    "blacklisted": 5,
    "blacklisted journalist": 6,
    "blacklisted activist": 6,

    "fined": 4,
    "fine": 3,
    "administrative fine": 5,
    "administrative penalty": 5,

    # Russe
    "репрессии": 8,
    "политические репрессии": 9,
    "политическое преследование": 9,
    "пытка": 10,
    "пытки": 10,
    "арестован": 7,
    "арестована": 7,
    "арестованы": 7,
    "задержан": 7,
    "задержана": 7,
    "задержаны": 7,
    "осужден": 6,
    "осуждена": 6,
    "осуждены": 6,
    "заключен": 8,
    "заключена": 8,
    "заключены": 8,
    "приговорен": 6,
    "приговорена": 6,
    "приговорены": 6,
    "тюрьма": 7,
    "тюрьме": 7,
    "избит": 6,
    "избита": 6,
    "избиты": 6,
    "угрозы": 4,
    "угрозы убийством": 6,
    "запугивание": 4,
    "преследование": 6,
    "преследуются": 6,
    "похищен": 8,
    "похищена": 8,
    "похищение": 8,
    "слежка": 4,
    "наблюдение": 3,
    "штраф": 3,
    "оштрафован": 4,
    "административный штраф": 5,
    "шизо": 8,
    "карцер": 8,
    "пыточные условия": 10,
    "пыточных условиях": 10,
    "одиночное заключение": 9,
    "произвольное задержание": 9,
    "за решеткой": 7,
    "за решёткой": 7,
    "отбывает срок": 7,
    "отбывает наказание": 7,
}


# ============================================================
# 22. WEIGHTS — DROITS SPÉCIFIQUES
# ============================================================

SPECIFIC_RIGHTS_WEIGHTS = {
    "academic freedom": 7,
    "academic freedoms": 7,
    "academic censorship": 7,
    "academic repression": 8,
    "academic persecution": 8,
    "academic freedom at risk": 8,
    "scholars at risk": 7,
    "scholar at risk": 7,
    "professor arrested": 6,
    "professor detained": 6,

    "gender-based violence": 8,
    "violence against women": 8,
    "violence against girls": 8,
    "sexual violence": 8,
    "forced marriage": 7,
    "child marriage": 7,

    "gender discrimination": 6,
    "gender-based discrimination": 6,

    "lgbt rights": 7,
    "lgbti rights": 7,
    "gay rights": 7,
    "lgbt": 5,
    "lgbti": 5,
    "lgbtq": 5,
    "same-sex relations": 5,
    "same-sex conduct": 5,

    "ethnic discrimination": 7,
    "religious discrimination": 7,
    "minority rights": 6,

    "child abuse": 8,
    "child labor": 7,
    "child labour": 7,

    "forced labor": 8,
    "forced labour": 8,

    "migrant rights": 5,
    "refugee rights": 5,

    "права женщин": 5,
    "гендерная дискриминация": 6,
    "насилие в отношении женщин": 8,
    "домашнее насилие": 7,
    "сексуальное насилие": 8,
    "сексуальные домогательства": 7,
    "принудительный брак": 7,
    "детский брак": 7,
    "лгбт": 5,
    "права меньшинств": 6,
    "этническая дискриминация": 7,
    "религиозная дискриминация": 7,
    "дискриминация": 4,
    "права детей": 5,
    "детский труд": 7,
    "принудительный труд": 8,
    "права мигрантов": 5,

    "академическая свобода": 7,
    "академические свободы": 7,
    "академические репрессии": 8,
    "академическая цензура": 7,
    "преследование ученых": 8,
    "преследование учёных": 8,
    "арест профессора": 7,
    "задержание профессора": 7,
}


# ============================================================
# 23. MOTS FORTS POUR IDENTIFIER UNE VICTIME
# ============================================================

VICTIM_TERMS = [
    "activist",
    "activists",
    "human rights activist",
    "human rights defender",
    "human rights defenders",
    "dissident",
    "dissidents",

    "opposition figure",
    "opposition politician",
    "opposition leader",
    "government critic",
    "political critic",

    "journalist",
    "journalists",
    "reporter",
    "reporters",
    "blogger",
    "bloggers",
    "independent journalist",

    "lawyer",
    "human rights lawyer",

    # Russe
    "активист",
    "активисты",
    "активистка",
    "активистки",
    "правозащитник",
    "правозащитники",
    "правозащитница",
    "правозащитницы",
    "диссидент",
    "диссиденты",
    "оппозиционер",
    "оппозиционеры",
    "оппозиционный политик",
    "лидер оппозиции",
    "критик власти",
    "критик правительства",

    "журналист",
    "журналисты",
    "репортер",
    "репортеры",
    "репортёр",
    "репортёры",
    "блогер",
    "блогеры",

    "адвокат",
    "адвокаты",
]
