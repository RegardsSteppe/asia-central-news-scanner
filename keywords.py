# ============================================================
# KEYWORDS — VEILLE ASIE CENTRALE / ACTIVISTES / DROITS HUMAINS
# VERSION 4 — détection renforcée à partir de l'analyse CSV
#
# IMPORTANT :
# - Conserve toutes les listes de la V3.
# - Ce fichier est additif : il importe V3 puis enrichit les listes.
# - À utiliser comme drop-in si le moteur accepte les mêmes constantes.
# - Les nouveaux termes privilégient les signaux contextuels précis
#   plutôt que l'ajout massif de mots génériques.
# ============================================================

from keywords_v3 import *  # noqa: F401,F403


# ============================================================
# 1. ALIAS / VARIANTES GÉOGRAPHIQUES
# ============================================================

CENTRAL_ASIA_TERMS += [
    # Variantes anglaises
    "central asian states",
    "central asian countries",
    "central asian republics",
    "central asian republic",
    "central asian region",
    "five central asian states",

    # Kazakhstan
    "republic of kazakhstan",
    "kazakhstani",
    "kazakhstani government",
    "kazakhstani authorities",
    "kazakh capital",

    # Kyrgyzstan
    "kyrgyz republic",
    "republic of kyrgyzstan",
    "kyrgyzstani",

    # Tajikistan
    "republic of tajikistan",
    "tajikistani",
    "tajikistan's gbao",

    # Turkmenistan
    "republic of turkmenistan",
    "turkmenistani",

    # Uzbekistan
    "republic of uzbekistan",
    "uzbekistani",

    # Karakalpakstan / variantes
    "qaraqalpaqstan",
    "qaraqalpakstan",
    "qaraqalpak",
    "nukus",

    # Variantes russes fréquentes
    "центральноазиатские страны",
    "страны центральной азии",
    "центральноазиатские государства",
    "республики центральной азии",
    "казахстанский",
    "казахстанцы",
    "кыргызская республика",
    "таджикистанский",
    "туркменский",
    "узбекистанский",
    "узбекистанцы",
    "каракалпакский",
    "каракалпакская",
    "каракалпакстане",
    "каракалпакстанский",
]


# ============================================================
# 2. DÉFENSEURS / ACTIVISTES — VARIANTES ET SIGNATURES
# ============================================================

HUMAN_RIGHTS_DEFENDER_TERMS += [
    "rights advocate",
    "rights advocates",
    "human rights advocate",
    "human rights advocates",
    "human rights campaigner",
    "human rights campaigners",
    "rights campaigner",
    "rights campaigners",
    "civil rights activist",
    "civil rights activists",
    "women's rights activist",
    "women's rights activists",
    "lgbt activist",
    "lgbti activist",
    "feminist activist",
    "feminist activists",
    "pro-democracy activist",
    "pro-democracy activists",
    "pro-democracy campaigner",
    "civil society leader",
    "civil society leaders",
    "civil society organization",
    "civil society organisation",

    # Russe
    "правозащитник и адвокат",
    "правозащитница и адвокат",
    "защитник прав человека",
    "защитники прав человека",
    "активист по правам человека",
    "активисты по правам человека",
    "борец за права человека",
    "борцы за права человека",
    "правозащитное движение",
    "правозащитная организация",
    "правозащитные организации",
]


ACTIVIST_TERMS += [
    "activist group",
    "activist groups",
    "rights group",
    "rights groups",
    "campaigner",
    "campaigners",
    "civil society leader",
    "civil society leaders",
    "pro-democracy",
    "pro-democracy movement",
    "pro-democracy group",
    "dissident writer",
    "political dissident",
    "political dissidents",
    "opposition figure",
    "opposition figures",

    # Russe
    "группа активистов",
    "группы активистов",
    "правозащитная организация",
    "правозащитные организации",
    "правозащитное движение",
    "общественная организация",
    "общественные организации",
    "гражданский активист",
    "гражданские активисты",
    "политический диссидент",
    "политические диссиденты",
]


VICTIM_TERMS += [
    "rights advocate",
    "human rights advocate",
    "campaigner",
    "civil rights activist",
    "women's rights activist",
    "lgbt activist",
    "lgbti activist",
    "pro-democracy activist",
    "civil society leader",

    # Russe
    "защитник прав человека",
    "защитники прав человека",
    "активист по правам человека",
    "активисты по правам человека",
    "борец за права человека",
    "гражданский активист",
    "гражданские активисты",
]


# ============================================================
# 3. RÉPRESSION — NOUVEAUX SIGNAUX JURIDIQUES
# ============================================================

REPRESSION_TERMS += [
    # Arrestation / détention
    "detainee",
    "detainees",
    "detained in custody",
    "detained by police",
    "detained by authorities",
    "pretrial detention",
    "pre-trial detention",
    "pretrial detainee",
    "pre-trial detainee",
    "remand",
    "remanded in custody",
    "detention center",
    "detention centre",
    "detention facility",
    "held in pretrial detention",
    "held in pre-trial detention",
    "held on remand",
    "house arrest",
    "under house arrest",
    "kept in custody",
    "remain in custody",

    # Prison / peine
    "prison colony",
    "penal colony",
    "correctional colony",
    "correctional facility",
    "prison camp",
    "prison authorities",
    "prisoner of conscience",
    "prisoners of conscience",
    "life sentence",
    "life imprisonment",
    "long prison sentence",
    "lengthy prison sentence",
    "years in prison",
    "years in jail",
    "released from prison",
    "released from custody",
    "denied parole",
    "parole denied",

    # Procédure pénale
    "investigation opened",
    "criminal investigation",
    "criminal investigation against",
    "investigation against",
    "indicted",
    "indictment",
    "accused of",
    "charged under",
    "charged under the law",
    "prosecuted under",
    "criminal proceedings",
    "criminal proceedings against",
    "court proceedings",
    "legal proceedings",
    "hearing",
    "court hearing",
    "appeal court",
    "appeal hearing",
    "appeal rejected",
    "appeal dismissed",

    # Perquisitions / saisies
    "police raid",
    "police raids",
    "raided",
    "raid on",
    "search warrant",
    "searches of homes",
    "home search",
    "house search",
    "police searched",
    "authorities searched",
    "equipment confiscated",
    "equipment seized",
    "phone confiscated",
    "passport confiscated",
    "documents confiscated",
    "property confiscated",

    # Restrictions administratives / médias
    "banned from practicing",
    "professional ban",
    "registration revoked",
    "license revoked",
    "licence revoked",
    "organization dissolved",
    "organization banned",
    "organisation dissolved",
    "organisation banned",
    "ngo registration revoked",
    "ngo deregistered",
    "deregistered ngo",
    "account blocked",
    "account suspended",
    "access restricted",
    "access blocked",
    "media restrictions",
    "press restrictions",
    "restrictions on journalists",
    "restrictions on media",
    "journalists denied access",
    "denied access to parliament",
    "denied access",

    # Russe
    "задержанный",
    "задержанные",
    "под стражей",
    "содержится под стражей",
    "содержание под стражей",
    "предварительное заключение",
    "досудебное заключение",
    "следственный изолятор",
    "изолятор временного содержания",
    "домашний арест",
    "колония",
    "исправительная колония",
    "колония строгого режима",
    "пожизненное заключение",
    "пожизненное лишение свободы",
    "лишение свободы",
    "годы лишения свободы",
    "освобожден из тюрьмы",
    "освобождена из тюрьмы",
    "отказано в освобождении",
    "уголовное производство",
    "уголовное преследование против",
    "уголовное дело против",
    "расследование против",
    "расследование возбуждено",
    "обвиняемый",
    "обвиняемая",
    "обвиняемые",
    "подозреваемый",
    "подозреваемая",
    "подозреваемые",
    "судебное разбирательство",
    "судебное заседание",
    "апелляционный суд",
    "апелляция отклонена",
    "обыск",
    "обыски",
    "обыскали",
    "обыск в доме",
    "изъятие документов",
    "изъятие техники",
    "конфискация",
    "запрет на деятельность",
    "лишение лицензии",
    "регистрация отозвана",
    "ликвидация организации",
    "запрет организации",
    "организация признана экстремистской",
    "доступ ограничен",
    "доступ заблокирован",
    "ограничения для журналистов",
    "ограничения для СМИ",
]


SEVERE_REPRESSION_TERMS += [
    "pretrial detention",
    "pre-trial detention",
    "prisoner of conscience",
    "life imprisonment",
    "police raid",
    "raided",
    "forcibly disappeared",
    "enforced disappearance",
    "house arrest",
    "torture in custody",

    # Russe
    "пытки в заключении",
    "пытки в тюрьме",
    "пытки под стражей",
    "следственный изолятор",
    "пожизненное лишение свободы",
    "признан политическим заключенным",
    "признана политическим заключенным",
    "политический заключенный",
]


REPRESSION_WEIGHTS.update({
    "pretrial detention": 7,
    "pre-trial detention": 7,
    "remanded in custody": 7,
    "house arrest": 7,
    "prison colony": 7,
    "penal colony": 7,
    "prisoner of conscience": 9,
    "life imprisonment": 9,
    "police raid": 6,
    "raided": 6,
    "search warrant": 4,
    "equipment confiscated": 5,
    "account blocked": 5,
    "access restricted": 4,
    "media restrictions": 5,
    "press restrictions": 5,
    "restrictions on journalists": 6,
    "journalists denied access": 6,

    "под стражей": 7,
    "предварительное заключение": 7,
    "следственный изолятор": 8,
    "домашний арест": 7,
    "исправительная колония": 7,
    "пожизненное лишение свободы": 9,
    "обыск": 5,
    "обыски": 5,
    "конфискация": 5,
    "ограничения для журналистов": 6,
    "ограничения для СМИ": 6,
})


# ============================================================
# 4. LIBERTÉ D'EXPRESSION / MÉDIAS — VARIANTES MANQUANTES
# ============================================================

HUMAN_RIGHTS_TERMS += [
    "right to information",
    "access to information",
    "access to public information",
    "freedom of the media",
    "freedom of journalism",
    "freedom of the internet",
    "internet freedom",
    "digital rights",
    "online freedom",
    "freedom of assembly and association",
    "freedom of association and assembly",
    "right to peaceful assembly",
    "right to peaceful protest",
    "arbitrary restrictions",
    "restrictions on free speech",
    "restrictions on freedom of expression",
    "restrictions on civil society",

    # Russe
    "право на информацию",
    "доступ к информации",
    "свобода СМИ",
    "свобода журналистики",
    "свобода интернета",
    "интернет-свобода",
    "цифровые права",
    "право на мирные собрания",
    "право на мирный протест",
    "ограничение свободы слова",
    "ограничения свободы выражения",
    "ограничения для гражданского общества",
]


JOURNALIST_TERMS += [
    "journalism",
    "journalistic",
    "journalistic work",
    "media organization",
    "media organisation",
    "news website",
    "news websites",
    "online media",
    "digital media",
    "independent newsroom",
    "independent newsrooms",
    "editor-in-chief",
    "editor in chief",
    "journalist's access",
    "journalists' access",
    "access for journalists",
    "press access",
    "media access",

    # Russe
    "журналистика",
    "журналистский",
    "журналистская деятельность",
    "медиорганизация",
    "медиаорганизация",
    "новостной сайт",
    "новостные сайты",
    "онлайн-СМИ",
    "независимая редакция",
    "главный редактор",
    "доступ журналистов",
    "доступ СМИ",
]


# ============================================================
# 5. JOURNALISTES — PATTERNS PLUS ROBUSTES
# ============================================================

JOURNALIST_REPRESSION_PATTERNS += [
    r"\b(journalist|journalists|reporter|reporters|editor|blogger|bloggers)\b.{0,180}\b(restrictions?|restricted|banned|blocked|denied access|access restricted|raided|searched|confiscated|revoked|suspended)\b",
    r"\b(journalist|journalists|reporter|reporters|editor|blogger|bloggers)\b.{0,180}\b(prosecuted|indicted|charged|accused|investigated|questioned|interrogated|detained|arrested|imprisoned|jailed)\b",
    r"\b(media|news outlet|independent media|news website)\b.{0,180}\b(blocked|banned|restricted|shut down|closed|raided|searched|suspended|deregistered)\b",
    r"\b(restricting|restricted|denied|blocked)\b.{0,120}\b(journalists?|reporters?|media|press)\b",
]


JOURNALIST_REPRESSION_RU_PATTERNS += [
    r"(журналист|журналисты|репортер|репортеры|репортёр|репортёры|редактор|блогер|блогеры).{0,180}(ограничен|ограничены|запрещен|запрещены|заблокирован|заблокированы|лишен доступа|лишены доступа|обыск|обыскали|изъят|изъяты|отозвана лицензия|закрыт|закрыты)",
    r"(журналист|журналисты|репортер|репортеры|репортёр|репортёры|редактор|блогер|блогеры).{0,180}(допрошен|допрошены|обвинен|обвинены|подозреваемый|подозреваемые|расследуется|задержан|задержаны|арестован|арестованы|осужден|осуждены|преследуется|преследуются)",
    r"(ограничен|ограничены|запрещен|запрещены|заблокирован|заблокированы|лишен доступа|лишены доступа).{0,120}(журналист|журналисты|СМИ|пресса)",
]


# ============================================================
# 6. ACTIVISTES — PATTERNS PLUS ROBUSTES
# ============================================================

ACTIVIST_REPRESSION_PATTERNS += [
    r"\b(campaigner|campaigners|rights advocate|human rights advocate|civil rights activist|women's rights activist|lgbt activist|pro-democracy activist)\b.{0,180}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|prosecuted|persecuted|threatened|attacked|harassed|raided|searched|fined|banned|blacklisted)\b",
    r"\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|prosecuted|persecuted|threatened|attacked|harassed|raided|searched|fined|banned|blacklisted)\b.{0,180}\b(campaigner|rights advocate|human rights advocate|civil rights activist|women's rights activist|lgbt activist|pro-democracy activist)\b",
    r"\b(civil society)\b.{0,180}\b(crackdown|repression|persecution|raided|banned|deregistered|dissolved|restricted)\b",
]


ACTIVIST_REPRESSION_RU_PATTERNS += [
    r"(борец за права человека|защитник прав человека|активист по правам человека|гражданский активист|правозащитная организация|правозащитное движение).{0,180}(арестован|задержан|осужден|приговорен|преследуется|угрожают|избит|похищен|обыск|оштрафован|запрещен|ликвидирован)",
    r"(арестован|задержан|осужден|приговорен|преследуется|угрожают|избит|похищен|обыск|оштрафован|запрещен|ликвидирован).{0,180}(борец за права человека|защитник прав человека|активист по правам человека|гражданский активист|правозащитная организация|правозащитное движение)",
]


# ============================================================
# 7. DROITS SPÉCIFIQUES — ENRICHISSEMENT
# ============================================================

SPECIFIC_RIGHTS_TERMS += [
    # Académique
    "academic researcher",
    "academic researchers",
    "academic community",
    "university professor",
    "university lecturer",
    "university researcher",
    "academic freedom at risk",
    "academic freedom under threat",
    "academic freedom under pressure",
    "scholarship restrictions",

    # Femmes
    "women human rights defenders",
    "women human rights defender",
    "women activists",
    "female activist",
    "female activists",
    "gender-based persecution",
    "gender-based repression",
    "forced marriage",
    "forced marriages",
    "bride abduction",
    "bride kidnapping",

    # LGBT
    "anti-lgbt",
    "anti-lgbt legislation",
    "anti-lgbt law",
    "lgbti community",
    "lgbt community",
    "sexual minorities",
    "gender minorities",

    # Travail / exploitation
    "forced agricultural work",
    "forced agricultural labour",
    "forced cotton harvesting",
    "cotton harvesting",
    "cotton harvest quotas",
    "labor rights",
    "labour rights",
    "worker rights",
    "workers' rights",
    "workplace abuse",
    "labor exploitation",
    "labour exploitation",

    # Migrants
    "migrant worker abuse",
    "abuse of migrant workers",
    "migrant detention",
    "deportation of migrants",
    "deportation of activists",
    "refugee protection",

    # Minorités
    "ethnic minority rights",
    "religious minority rights",
    "minority discrimination",
    "minority persecution",

    # Russe
    "академическое сообщество",
    "университетский профессор",
    "университетский преподаватель",
    "исследователь",
    "исследователи",
    "академическая среда",
    "академическая свобода под угрозой",
    "защитницы прав человека",
    "женщины-активисты",
    "женщина-активист",
    "гендерные репрессии",
    "гендерное преследование",
    "принудительные браки",
    "похищение невесты",
    "анти-лгбт",
    "лгбти-сообщество",
    "лгбт-сообщество",
    "сексуальные меньшинства",
    "гендерные меньшинства",
    "принудительная сельскохозяйственная работа",
    "принудительный сбор хлопка",
    "квоты на сбор хлопка",
    "трудовые права",
    "эксплуатация труда",
    "эксплуатация работников",
    "задержание мигрантов",
    "депортация мигрантов",
    "права этнических меньшинств",
    "права религиозных меньшинств",
    "преследование меньшинств",
]


SPECIFIC_RIGHTS_WEIGHTS.update({
    "academic freedom at risk": 9,
    "academic freedom under threat": 8,
    "academic freedom under pressure": 8,
    "gender-based persecution": 8,
    "gender-based repression": 8,
    "women human rights defenders": 8,
    "anti-lgbt legislation": 7,
    "anti-lgbt law": 7,
    "sexual minorities": 6,
    "forced agricultural work": 7,
    "forced agricultural labour": 7,
    "forced cotton harvesting": 8,
    "cotton harvest quotas": 7,
    "labor rights": 5,
    "labour rights": 5,
    "labor exploitation": 7,
    "labour exploitation": 7,
    "migrant detention": 6,
    "minority persecution": 8,

    "академическая свобода под угрозой": 9,
    "гендерные репрессии": 8,
    "гендерное преследование": 8,
    "принудительный сбор хлопка": 8,
    "квоты на сбор хлопка": 7,
    "эксплуатация труда": 7,
    "задержание мигрантов": 6,
    "преследование меньшинств": 8,
})


# ============================================================
# 8. SIGNAUX SPÉCIFIQUES PAR PAYS
# ============================================================

CENTRAL_ASIA_HR_TERMS += [
    # Kazakhstan — événements de janvier 2022 / pression politique
    "january 2022 protests",
    "january 2022 crackdown",
    "january 2022 killings",
    "january events in kazakhstan",
    "qantar 2022",
    "qantar 2022 events",
    "kazakhstan human rights",
    "kazakhstan activists",
    "kazakhstan activist",
    "kazakhstan journalist",
    "kazakhstan journalists",
    "kazakhstan press freedom",
    "kazakhstan political prisoners",
    "kazakhstan political repression",
    "kazakhstan civil society",
    "kazakhstan freedom of expression",

    # Kyrgyzstan
    "kyrgyzstan human rights",
    "kyrgyzstan activists",
    "kyrgyzstan activist",
    "kyrgyzstan journalist",
    "kyrgyzstan journalists",
    "kyrgyzstan press freedom",
    "kyrgyzstan lgbt",
    "kyrgyzstan civil society",
    "kyrgyzstan repression",
    "kyrgyzstan torture",
    "kyrgyzstan detention",
    "kyrgyzstan media law",

    # Tajikistan / GBAO
    "tajikistan human rights",
    "tajikistan activists",
    "tajikistan journalist",
    "tajikistan journalists",
    "tajikistan repression",
    "tajikistan political prisoners",
    "gbao protests",
    "gbao crackdown",
    "gbao activists",
    "gbao human rights",
    "pamiri activists",
    "pamiri community",
    "khorog protests",
    "khorog crackdown",

    # Turkmenistan
    "turkmenistan human rights defender",
    "turkmenistan human rights defenders",
    "turkmenistan political prisoner",
    "turkmenistan political prisoners",
    "turkmenistan opposition",
    "turkmenistan dissident",
    "turkmenistan journalist",
    "turkmenistan journalists",
    "turkmenistan activist",
    "turkmenistan activists",
    "turkmenistan torture",
    "turkmenistan forced labor",
    "turkmenistan forced labour",
    "turkmenistan cotton quotas",
    "turkmenistan censorship",
    "turkmenistan internet censorship",
    "turkmenistan media freedom",
    "turkmenistan press freedom",

    # Uzbekistan / Karakalpakstan
    "uzbekistan human rights",
    "uzbekistan human rights defender",
    "uzbekistan activists",
    "uzbekistan activist",
    "uzbekistan journalist",
    "uzbekistan journalists",
    "uzbekistan political prisoners",
    "uzbekistan political repression",
    "uzbekistan censorship",
    "uzbekistan press freedom",
    "uzbekistan freedom of expression",
    "uzbekistan forced labor",
    "uzbekistan forced labour",
    "uzbekistan cotton quotas",
    "karakalpakstan human rights",
    "karakalpakstan activists",
    "karakalpakstan activist",
    "karakalpakstan journalist",
    "karakalpakstan repression",
    "karakalpakstan crackdown",
    "karakalpakstan protests",
    "nukus protests",
    "nukus crackdown",

    # Russe — signaux pays
    "права человека в казахстане",
    "правозащитники в казахстане",
    "активисты в казахстане",
    "журналисты в казахстане",
    "репрессии в казахстане",
    "пытки в казахстане",
    "права человека в кыргызстане",
    "правозащитники в кыргызстане",
    "активисты в кыргызстане",
    "журналисты в кыргызстане",
    "репрессии в кыргызстане",
    "пытки в кыргызстане",
    "права человека в таджикистане",
    "правозащитники в таджикистане",
    "активисты в таджикистане",
    "журналисты в таджикистане",
    "репрессии в таджикистане",
    "права человека в туркменистане",
    "правозащитники в туркменистане",
    "активисты в туркменистане",
    "журналисты в туркменистане",
    "репрессии в туркменистане",
    "принудительный труд в туркменистане",
    "права человека в узбекистане",
    "правозащитники в узбекистане",
    "активисты в узбекистане",
    "журналисты в узбекистане",
    "репрессии в узбекистане",
    "каракалпакстанские протесты",
    "протесты в нукусе",
    "подавление протестов в нукусе",
]


# ============================================================
# 9. ACTEURS / ORGANISATIONS — SIGNAUX UTILES
# ============================================================

REGIONAL_ACTORS += [
    "human rights watch",
    "amnesty international",
    "committee to protect journalists",
    "cpj",
    "reporters without borders",
    "rsf",
    "freedom house",
    "international labour organization",
    "international labor organization",
    "ilo",
    "office of the united nations high commissioner for human rights",
    "ohchr",
    "un human rights",
    "un special rapporteur",
    "special rapporteur",
    "organization for security and cooperation in europe",
    "osce",
    "european parliament",

    # Acteurs / médias particulièrement présents dans le CSV
    "turkmen.news",
    "turkmen news",
    "fergana agency",
    "fergana.agency",
    "novastan",
    "the diplomat",
    "kloop",
    "kaktus media",
    "occ rp",
    "occrp",
]


# ============================================================
# 10. POLITIQUE INTÉRIEURE — SIGNAUX À VALEUR AJOUTÉE
# ============================================================

DOMESTIC_POLITICAL_TERMS += [
    "democratic reform",
    "democratic reforms",
    "democracy score",
    "democratic backsliding",
    "democratic decline",
    "authoritarianism",
    "authoritarian rule",
    "authoritarian government",
    "political pluralism",
    "political participation",
    "civil liberties",
    "political liberties",
    "rule of law",
    "judicial independence",
    "independent judiciary",
    "electoral reform",
    "electoral reforms",
    "electoral fraud",
    "election irregularities",
    "managed competition",
    "political competition",
    "power succession",
    "succession plan",
    "presidential powers",
    "presidential authority",
    "concentration of power",
    "power consolidation",
    "constitutional court",
    "constitutional amendment",

    # Russe
    "демократические реформы",
    "демократический откат",
    "авторитаризм",
    "авторитарное правление",
    "политический плюрализм",
    "гражданские свободы",
    "политические свободы",
    "верховенство закона",
    "независимость судебной системы",
    "избирательная реформа",
    "избирательные нарушения",
    "управляемая конкуренция",
    "политическая конкуренция",
    "преемник президента",
    "преемственность власти",
    "полномочия президента",
    "усиление президентских полномочий",
]


# ============================================================
# 11. NON-NEWS — ENRICHISSEMENT LÉGER POUR COMPENSER LES
#     NOUVEAUX TERMES SANS CASSER LA DÉTECTION
# ============================================================

NON_NEWS_TERMS += [
    "call for papers",
    "call for proposals",
    "terms of reference",
    "terms of reference (tor)",
    "consultancy",
    "consultant",
    "consultants",
    "fellowship",
    "fellowships",
    "scholarship application",
    "internship",
    "internships",
    "volunteer opportunity",
    "volunteers wanted",
    "registration is open",
    "register now",
    "join us",
    "donate",
    "donation",
    "fundraising",
    "annual conference",
    "training course",
    "online course",
    "course registration",

    # Russe
    "конкурс заявок",
    "прием заявок",
    "приём заявок",
    "техническое задание",
    "консультант",
    "консультационные услуги",
    "стипендия",
    "стипендии",
    "стажировка",
    "стажировки",
    "волонтер",
    "волонтёр",
    "регистрация открыта",
    "зарегистрироваться",
    "пожертвование",
    "сбор средств",
    "ежегодная конференция",
    "курс обучения",
]


# ============================================================
# 12. NOISE — ÉVITER QUELQUES COLLISIONS
# ============================================================

NOISE_TERMS += [
    "sports event",
    "sports league",
    "match report",
    "transfer window",
    "video game",
    "gaming",
    "app store",
    "mobile app",
    "tech review",
    "product launch",
]


# ============================================================
# 13. PATTERNS — CONTEXTE JURIDIQUE / DROITS HUMAINS
# ============================================================

HUMAN_RIGHTS_CONTEXT_PATTERNS = [
    # Anglais : droit / restriction / acteur ciblé
    r"\b(human rights?|civil rights?|civil liberties|freedom of expression|press freedom|media freedom)\b.{0,180}\b(repression|crackdown|restriction|restricted|violation|violations|abuse|persecution|censorship|detention|arrest|torture)\b",
    r"\b(activist|activists|human rights defender|rights advocate|campaigner|journalist|journalists|reporter|blogger)\b.{0,180}\b(rights violation|repression|crackdown|restriction|arrested|detained|charged|prosecuted|sentenced|threatened|attacked|harassed|censored|blocked)\b",
    r"\b(women|women's rights|lgbt|lgbti|minority|minorities)\b.{0,180}\b(discrimination|violence|persecution|repression|harassment|abuse|arrested|detained|banned)\b",

    # Russe
    r"(права человека|гражданские права|гражданские свободы|свобода слова|свобода прессы|свобода СМИ).{0,180}(репресс|преслед|наруш|цензур|задерж|арест|пытк|огранич)",
    r"(активист|правозащитник|защитник прав человека|журналист|блогер|правозащитная организация).{0,180}(репресс|преслед|арест|задерж|обвин|приговор|угроз|напад|цензур|запрет)",
    r"(женщин|лгбт|лгбти|меньшинств).{0,180}(дискриминац|насили|преслед|репресс|домашн|сексуальн|запрет)",
]


# ============================================================
# 14. PATTERNS — SIGNAUX SPÉCIFIQUES ASIE CENTRALE
# ============================================================

CENTRAL_ASIA_HR_PATTERNS = [
    r"\b(kazakhstan|kazakhstani|kyrgyzstan|tajikistan|turkmenistan|uzbekistan|karakalpakstan)\b.{0,180}\b(human rights|activist|journalist|dissident|political prisoner|repression|crackdown|torture|forced labor|press freedom|censorship)\b",
    r"\b(human rights|activist|journalist|dissident|political prisoner|repression|crackdown|torture|forced labor|press freedom|censorship)\b.{0,180}\b(kazakhstan|kazakhstani|kyrgyzstan|tajikistan|turkmenistan|uzbekistan|karakalpakstan)\b",

    r"(казахстан|кыргызстан|таджикистан|туркменистан|узбекистан|каракалпакстан).{0,180}(правозащит|активист|журналист|диссидент|политическ.*заключ|репресс|пытк|принудительн.*труд|свобода прессы|цензур)",
    r"(правозащит|активист|журналист|диссидент|политическ.*заключ|репресс|пытк|принудительн.*труд|свобода прессы|цензур).{0,180}(казахстан|кыргызстан|таджикистан|туркменистан|узбекистан|каракалпакстан)",
]


# ============================================================
# 15. DÉDUPLICATION
# ============================================================

def _dedupe(items):
    seen = set()
    out = []
    for item in items:
        key = item if isinstance(item, str) else repr(item)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


for _name in [
    "HUMAN_RIGHTS_DEFENDER_TERMS",
    "FORCED_LABOR_TERMS",
    "CENTRAL_ASIA_TERMS",
    "CAUCASUS_TERMS",
    "HUMAN_RIGHTS_TERMS",
    "ACTIVIST_TERMS",
    "REPRESSION_TERMS",
    "LEGAL_REPRESSION_TERMS",
    "LEGAL_CONTEXT_TERMS",
    "JOURNALIST_TERMS",
    "SPECIFIC_RIGHTS_TERMS",
    "CENTRAL_ASIA_HR_TERMS",
    "DOMESTIC_POLITICAL_TERMS",
    "MAJOR_GEOPOLITICAL_TERMS",
    "ROUTINE_GEO_TERMS",
    "LOW_SIGNAL_CONTEXT_TERMS",
    "REGIONAL_ACTORS",
    "HISTORICAL_TERMS",
    "NON_NEWS_TERMS",
    "NOISE_TERMS",
    "SEVERE_REPRESSION_TERMS",
    "VICTIM_TERMS",
    "ACTIVIST_REPRESSION_PATTERNS",
    "JOURNALIST_REPRESSION_PATTERNS",
    "ACTIVIST_REPRESSION_RU_PATTERNS",
    "JOURNALIST_REPRESSION_RU_PATTERNS",
    "HUMAN_RIGHTS_CONTEXT_PATTERNS",
    "CENTRAL_ASIA_HR_PATTERNS",
]:
    if _name in globals():
        globals()[_name] = _dedupe(globals()[_name])


# ============================================================
# FIN
# ============================================================
