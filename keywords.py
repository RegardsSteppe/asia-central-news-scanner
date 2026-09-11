# ============================================================
# keywords.py — Central Asia News Scanner V9
# ============================================================

# ------------------------------------------------------------
# 1. HUMAN RIGHTS DEFENDERS
# ------------------------------------------------------------

HUMAN_RIGHTS_DEFENDER_TERMS = [
    "human rights defender",
    "human rights defenders",
    "rights defender",
    "rights defenders",
    "defender",
    "activist",
    "activists",
    "civil society activist",
    "civil society activists",
    "human rights activist",
    "human rights activists",
    "ngo worker",
    "ngo workers",
    "civil society",
    "rights group",
    "rights groups",
    "human rights group",
    "human rights groups",
    "dissident",
    "dissidents",
    "opposition activist",
    "opposition activists",
    "political activist",
    "political activists",
    "pro-democracy activist",
    "pro-democracy activists",
    "peaceful activist",
    "peaceful activists",
]

# ------------------------------------------------------------
# 2. FORCED LABOR
# ------------------------------------------------------------

FORCED_LABOR_TERMS = [
    "forced labor",
    "forced labour",
    "forced work",
    "forced recruitment",
    "forced recruitment of workers",
    "forced picking",
    "forced cotton picking",
    "forced cotton harvesting",
    "cotton picking",
    "cotton harvesting",
    "mandatory cotton picking",
    "mandatory cotton harvesting",
    "mobilized for cotton",
    "mobilised for cotton",
    "labor mobilization",
    "labour mobilisation",
    "labor mobilisation",
    "state-imposed quotas",
    "state imposed quotas",
    "compulsory labor",
    "compulsory labour",
    "work under coercion",
    "coerced labor",
    "coerced labour",
    "unpaid labor",
    "unpaid labour",
    "forced agricultural work",

    # Russian
    "принудительный труд",
    "принудительный труд работников",
    "принудительная работа",
    "принудительная уборка",
    "принудительный сбор хлопка",
    "обязательный сбор хлопка",
    "принудительная уборка хлопка",
    "трудовая мобилизация",
    "принудительная мобилизация",
    "принудительное привлечение к труду",
    "обязательный труд",
    "бесплатный труд",
]

# ------------------------------------------------------------
# 3. CENTRAL ASIA
# ------------------------------------------------------------

CENTRAL_ASIA_TERMS = [
    "central asia",
    "central asian",
    "kazakhstan",
    "uzbekistan",
    "kyrgyzstan",
    "kyrgyz republic",
    "tajikistan",
    "turkmenistan",

    # common country adjectives / forms
    "kazakh",
    "uzbek",
    "kyrgyz",
    "tajik",
    "turkmen",

    # Grandes villes — un article peut nommer la ville sans jamais
    # nommer le pays (ex. un titre mentionnant seulement "Samarkand").
    "almaty",
    "astana",
    "nur-sultan",
    "shymkent",
    "karaganda",
    "aktobe",
    "atyrau",
    "tashkent",
    "samarkand",
    "bukhara",
    "khiva",
    "namangan",
    "andijan",
    "fergana",
    "nukus",
    "bishkek",
    "osh",
    "jalal-abad",
    "karakol",
    "dushanbe",
    "khujand",
    "khorog",
    "ashgabat",
    "turkmenabat",
    "dashoguz",

    # Russian
    "центральная азия",
    "центральноазиатский",
    "казахстан",
    "узбекистан",
    "кыргызстан",
    "киргизия",
    "таджикистан",
    "туркменистан",

    # Grandes villes — russe
    "алматы",
    "астана",
    "нур-султан",
    "шымкент",
    "караганда",
    "актобе",
    "атырау",
    "ташкент",
    "самарканд",
    "бухара",
    "хива",
    "наманган",
    "андижан",
    "фергана",
    "нукус",
    "бишкек",
    "ош",
    "джалал-абад",
    "каракол",
    "душанбе",
    "худжанд",
    "хорог",
    "ашхабад",
    "туркменабат",
    "дашогуз",

    # Farsi — le persan est proche du tadjik et l'Iran couvre
    # largement la région (nouvelles sources IRNA/Fararu) ; sans ces
    # formes, un article persan sur l'Asie centrale ne franchit jamais
    # la porte géographique et reste en niveau D quel que soit son
    # contenu.
    "آسیای مرکزی",
    "قزاقستان",
    "ازبکستان",
    "قرقیزستان",
    "قیرقیزستان",
    "تاجیکستان",
    "ترکمنستان",

    # adjectifs de pays — persan
    "قزاق",
    "ازبک",
    "قرقیز",
    "تاجیک",
    "ترکمن",

    # Grandes villes — persan. Astana ("آستانه", aussi le mot courant
    # pour "seuil"/"à la veille de") et Douchanbé ("دوشنبه", aussi le
    # mot pour "lundi") volontairement absentes : trop ambiguës en
    # persan courant, elles feraient passer la porte géographique à
    # des articles sans rapport. Les noms de pays ci-dessus suffisent
    # à couvrir l'essentiel des articles sur ces deux villes.
    "آلماتی",
    "تاشکند",
    "سمرقند",
    "بخارا",
    "بیشکک",
    "عشق‌آباد",
    "عشق آباد",

    # French — plusieurs sources publient en français (HRW, Amnesty,
    # RSF, Novastan...) : sans les formes françaises, un article sur
    # "l'Ouzbékistan" ou "Douchanbé" ne franchit jamais la porte
    # géographique et reste plafonné en niveau E quel que soit son
    # contenu (repéré en audit réel le 2026-09-11 sur un article HRW
    # français concernant Anar Mammadli, resté à 7/E faute de
    # reconnaître "Azerbaïdjan" — voir aussi CAUCASUS_TERMS).
    "asie centrale",
    "ouzbékistan",
    "kirghizistan",
    "kirghizstan",
    "tadjikistan",
    "turkménistan",

    # adjectifs de pays — français
    "ouzbek",
    "kirghize",
    "tadjik",
    "turkmène",

    # Grandes villes — français (orthographe distincte du russe/anglais)
    "samarcande",
    "boukhara",
    "douchanbé",
    "achgabat",
    "bichkek",
    "tachkent",
]

# ------------------------------------------------------------
# 4. CAUCASUS
# ------------------------------------------------------------

CAUCASUS_TERMS = [
    "caucasus",
    "south caucasus",
    "north caucasus",
    "armenia",
    "azerbaijan",
    "georgia",
    "chechnya",
    "dagestan",
    "north ossetia",
    "ingushetia",

    # Grandes villes
    "baku",
    "tbilisi",
    "yerevan",
    "grozny",
    "makhachkala",

    # Russian
    "кавказ",
    "южный кавказ",
    "северный кавказ",
    "армения",
    "азербайджан",
    "грузия",
    "чечня",
    "дагестан",
    "ингушетия",

    # Grandes villes — russe
    "баку",
    "тбилиси",
    "ереван",
    "грозный",
    "махачкала",

    # Farsi
    "قفقاز",
    "قفقاز جنوبی",
    "قفقاز شمالی",
    "ارمنستان",
    "آذربایجان",
    "گرجستان",
    "چچن",
    "داغستان",

    # Grandes villes — persan
    "باکو",
    "تفلیس",
    "ایروان",

    # French — voir la note sur CENTRAL_ASIA_TERMS : sans ces formes,
    # un article français sur l'Azerbaïdjan ne franchit jamais la
    # porte géographique.
    "azerbaïdjan",
    "arménie",
    "géorgie",
    "tchétchénie",
    "daguestan",
    "ossétie du nord",
    "ingouchie",

    # adjectifs de pays — français
    "azerbaïdjanais",
    "arménien",
    "géorgien",

    # Grandes villes — français
    "bakou",
    "tbilissi",
    "erevan",
    "makhatchkala",
]

# ------------------------------------------------------------
# 4bis. UYGHURS / XINJIANG
# ------------------------------------------------------------
# Traité comme une région ciblée à part entière, au même titre que
# l'Asie centrale et le Caucase (pas seulement un sujet secondaire).

UYGHUR_TERMS = [
    "uyghur",
    "uyghurs",
    "uighur",
    "uighurs",
    "xinjiang",
    "east turkestan",
    "eastern turkestan",
    "urumqi",
    "kashgar",
    "kashgar prefecture",

    # Russian
    "уйгур",
    "уйгуры",
    "уйгурский",
    "уйгурская",
    "синьцзян",
    "восточный туркестан",
    "урумчи",
    "кашгар",

    # Farsi
    "اویغور",
    "اویغورها",
    "شینجیانگ",
    "ترکستان شرقی",
    "ارومچی",
    "کاشغر",

    # French
    "ouïghour",
    "ouïghours",
    "ouïghoure",
    "turkestan oriental",
    "ouroumtsi",
    "kachgar",
]

# ------------------------------------------------------------
# 5. GENERAL HUMAN RIGHTS
# ------------------------------------------------------------

HUMAN_RIGHTS_TERMS = [
    "human rights",
    "human rights violations",
    "rights violations",
    "rights abuse",
    "abuse of rights",
    "civil rights",
    "political rights",
    "fundamental rights",
    "freedom of expression",
    "freedom of speech",
    "freedom of assembly",
    "freedom of association",
    "freedom of religion",
    "freedom of belief",
    "freedom of conscience",
    "freedom of movement",
    "right to protest",
    "right to privacy",
    "due process",
    "fair trial",
    "rule of law",
    "civic space",
    "shrinking civic space",
    "civil liberties",

    # Russian
    "права человека",
    "нарушение прав человека",
    "нарушения прав",
    "гражданские права",
    "политические права",
    "основные права",
    "свобода выражения мнения",
    "свобода слова",
    "свобода собраний",
    "свобода объединений",
    "свобода вероисповедания",
    "свобода совести",
    "свобода передвижения",
    "право на протест",
    "право на частную жизнь",
    "надлежащая правовая процедура",
    "справедливый суд",
    "верховенство закона",
    "гражданское пространство",
    "гражданские свободы",

    # Farsi
    "حقوق بشر",
    "نقض حقوق بشر",
    "حقوق مدنی",
    "حقوق سیاسی",
    "آزادی بیان",
    "آزادی اجتماعات",
    "آزادی تجمع",
    "آزادی مذهب",
    "آزادی عقیده",
    "دادرسی عادلانه",
    "محاکمه عادلانه",
    "حاکمیت قانون",

    # French
    "droits humains",
    "droits de l'homme",
    "violation des droits humains",
    "violations des droits humains",
    "droits civils",
    "droits politiques",
    "liberté d'expression",
    "liberté de réunion",
    "liberté d'association",
    "liberté de religion",
    "liberté de conscience",
    "liberté de circulation",
    "droit de manifester",
    "procès équitable",
    "état de droit",
    "espace civique",
    "libertés civiles",
]

# ------------------------------------------------------------
# 6. ACTIVISTS
# ------------------------------------------------------------

ACTIVIST_TERMS = [
    "activist",
    "activists",
    "human rights activist",
    "human rights activists",
    "political activist",
    "political activists",
    "civil society activist",
    "civil society activists",
    "pro-democracy activist",
    "pro-democracy activists",
    "opposition activist",
    "opposition activists",
    "dissident",
    "dissidents",
    "opposition figure",
    "opposition figures",
    "civil society leader",
    "civil society leaders",

    # Russian morphology
    "активист",
    "активисты",
    "активиста",
    "активистов",
    "правозащитник",
    "правозащитники",
    "правозащитника",
    "правозащитников",
    "оппозиционер",
    "оппозиционеры",
    "оппозиционера",
    "оппозиционеров",
    "диссидент",
    "диссиденты",

    # Farsi
    "فعال",
    "فعالان",
    "فعال حقوق بشر",
    "فعالان حقوق بشر",
    "فعال سیاسی",
    "فعالان سیاسی",
    "فعال مدنی",
    "فعالان مدنی",
    "اپوزیسیون",
    "چهره اپوزیسیون",
    "چهره‌های اپوزیسیون",

    # French — voir la note sur CENTRAL_ASIA_TERMS : les sources
    # HRW/Amnesty/RSF en français perdaient tout signal "activiste"
    # faute de vocabulaire français (repéré en audit réel le
    # 2026-09-11).
    "militant",
    "militants",
    "militante",
    "militantes",
    "activiste",
    "activistes",
    "défenseur des droits humains",
    "défenseurs des droits humains",
    "défenseur des droits de l'homme",
    "défenseurs des droits de l'homme",
    "dissident",
    "dissidente",
    "dissidents",
    "dissidentes",
    "opposant",
    "opposante",
    "opposants",
]

# ------------------------------------------------------------
# 7. REPRESSION
# ------------------------------------------------------------

REPRESSION_TERMS = [
    "repression",
    "repressive",
    "crackdown",
    "crackdown on",
    "political repression",
    "state repression",
    "government repression",
    "persecution",
    "persecuted",
    "persecute",
    "harassment",
    "intimidation",
    "threatened",
    "threats",
    "retaliation",
    "reprisal",
    "reprisals",
    "punished for speaking out",
    "silencing",
    "suppression",
    "suppression of dissent",
    "political persecution",
    "political pressure",
    "state pressure",
    "government pressure",
    "abuse of power",
    "state abuse",

    # Russian stems / morphology handled by substring matching
    "репресс",
    "преследован",
    "преследова",
    "давлен",
    "запугив",
    "угроз",
    "подавлен",
    "подавля",
    "гонен",
    "притеснен",
    "притесн",
    "давлени",
    "репрессив",

    # Farsi
    "سرکوب",
    "آزار",
    "آزار و اذیت",
    "تهدید",
    "ارعاب",
    "فشار سیاسی",
    "فشار دولت",

    # French
    "répression",
    "répressif",
    "répression politique",
    "répression d'état",
    "persécution",
    "persécuté",
    "harcèlement",
    "intimidation",
    "menacé",
    "menaces",
    "représailles",
    "réduire au silence",
    "pression politique",
    "abus de pouvoir",
]

# ------------------------------------------------------------
# 8. LEGAL / POLITICAL REPRESSION
# ------------------------------------------------------------

LEGAL_REPRESSION_TERMS = [
    "political prosecution",
    "politically motivated prosecution",
    "politically motivated charges",
    "political charges",
    "political case",
    "politically motivated case",
    "politically motivated trial",
    "selective prosecution",
    "selective justice",
    "abuse of criminal law",
    "abuse of the law",
    "criminalization of dissent",
    "criminalisation of dissent",
    "criminalized for",
    "criminalised for",
    "prosecuted for criticizing",
    "prosecuted for criticising",
    "prosecuted for speaking out",
    "charged for criticizing",
    "charged for criticising",
    "charged over a protest",
    "convicted for protest",
    "convicted for activism",
    "prisoner of conscience",
    "prisoners of conscience",
    "political prisoner",
    "political prisoners",
    "political detainee",
    "political detainees",
    "arbitrary detention",
    "arbitrarily detained",
    "arbitrary arrest",
    "arbitrarily arrested",
    "unlawful detention",
    "unlawful arrest",

    # Russian
    "политическое преследование",
    "политическое дело",
    "политически мотивированное дело",
    "политически мотивированное обвинение",
    "политически мотивированное преследование",
    "политически мотивированный приговор",
    "политзаключенный",
    "политзаключенные",
    "политический заключенный",
    "политические заключенные",
    "узник совести",
    "узники совести",
    "произвольное задержание",
    "произвольный арест",
    "незаконное задержание",
    "незаконный арест",

    # Farsi
    "زندانی سیاسی",
    "زندانیان سیاسی",
    "زندانی عقیدتی",
    "پرونده سیاسی",
    "اتهامات سیاسی",
    "بازداشت خودسرانه",
    "بازداشت غیرقانونی",
]

# ------------------------------------------------------------
# 9. LEGAL / RULE OF LAW CONTEXT
# ------------------------------------------------------------

LEGAL_CONTEXT_TERMS = [
    "trial",
    "court",
    "court ruling",
    "court decision",
    "judiciary",
    "judicial independence",
    "independent judiciary",
    "rule of law",
    "constitutional court",
    "constitution",
    "due process",
    "fair trial",
    "legal proceedings",
    "prosecution",
    "prosecutor",
    "prosecutors",
    "charges",
    "conviction",
    "convicted",
    "sentenced",
    "sentence",
    "imprisoned",
    "detained",
    "detention",
    "arrest",
    "arrested",

    # Russian
    "суд",
    "судебное решение",
    "судебное разбирательство",
    "судебная система",
    "независимость судебной системы",
    "верховенство закона",
    "конституционный суд",
    "конституция",
    "правосудие",
    "обвинение",
    "обвинения",
    "приговор",
    "осужден",
    "осуждена",
    "осуждены",
    "задержан",
    "задержана",
    "задержание",
    "арест",
    "арестован",
    "арестована",
    "заключен",
    "заключена",

    # Farsi
    "دادگاه",
    "دادرسی",
    "محاکمه",
    "بازداشت",
    "دستگیری",
    "دستگیر",
    "بازجویی",
    "محکومیت",
    "محکوم",
    "حکم دادگاه",
    "حکم زندان",
    "زندانی",
]

# ------------------------------------------------------------
# 10. JOURNALISTS / PRESS FREEDOM
# ------------------------------------------------------------

JOURNALIST_TERMS = [
    "journalist",
    "journalists",
    "reporter",
    "reporters",
    "editor",
    "editors",
    "media outlet",
    "media outlets",
    "news outlet",
    "news outlets",
    "independent media",
    "independent journalist",
    "independent journalists",
    "press freedom",
    "media freedom",
    "freedom of the press",
    "censorship",
    "self-censorship",
    "online censorship",
    "internet censorship",
    "media restrictions",
    "press restrictions",
    "media crackdown",
    "media blocked",
    "website blocked",
    "website blocking",
    "internet shutdown",
    "internet blackout",
    "outlet closed",
    "outlet shut down",
    "media outlet closed",
    "journalist detained",
    "journalist arrested",
    "journalist sentenced",
    "journalist imprisoned",
    "journalist prosecuted",
    "journalist harassed",
    "journalist threatened",

    # Russian
    "журналист",
    "журналисты",
    "журналиста",
    "журналистов",
    "репортер",
    "репортеры",
    "СМИ",
    "независимые СМИ",
    "независимый журналист",
    "свобода прессы",
    "свобода слова",
    "цензура",
    "интернет-цензура",
    "ограничение СМИ",
    "ограничения для СМИ",
    "блокировка сайта",
    "заблокирован сайт",
    "отключение интернета",
    "закрытие СМИ",
    "СМИ закрыли",
    "журналист задержан",
    "журналист арестован",
    "журналист осужден",
    "журналист заключен",
    "журналист преследуется",
    "журналисту угрожали",

    # Farsi
    "روزنامه‌نگار",
    "روزنامه نگار",
    "روزنامه‌نگاران",
    "خبرنگار",
    "خبرنگاران",
    "رسانه مستقل",
    "رسانه‌های مستقل",
    "آزادی مطبوعات",
    "آزادی رسانه",
    "سانسور",
    "خودسانسوری",
    "فیلترینگ اینترنت",
    "قطعی اینترنت",
    "روزنامه‌نگار بازداشت",
    "روزنامه‌نگار زندانی",

    # French
    "journaliste",
    "journalistes",
    "rédacteur",
    "rédactrice",
    "média indépendant",
    "médias indépendants",
    "journaliste indépendant",
    "journalistes indépendants",
    "liberté de la presse",
    "liberté des médias",
    "censure",
    "autocensure",
    "censure en ligne",
    "restrictions pour les médias",
    "site bloqué",
    "coupure d'internet",
    "média fermé",
    "journaliste détenu",
    "journaliste arrêté",
    "journaliste condamné",
    "journaliste emprisonné",
    "journaliste poursuivi",
    "journaliste harcelé",
    "journaliste menacé",
]

# ------------------------------------------------------------
# 11. SPECIFIC RIGHTS
# ------------------------------------------------------------

SPECIFIC_RIGHTS_TERMS = [
    "torture",
    "tortured",
    "ill-treatment",
    "mistreatment",
    "abuse in custody",
    "custodial abuse",
    "police abuse",
    "police brutality",
    "forced disappearance",
    "enforced disappearance",
    "disappeared",
    "missing after detention",
    "extrajudicial killing",
    "unlawful killing",
    "death in custody",
    "custody death",
    "religious persecution",
    "religious repression",
    "religious freedom",
    "minority rights",
    "ethnic discrimination",
    "ethnic persecution",
    "discrimination",
    "gender-based violence",
    "gender violence",
    "domestic violence",
    "domestic abuse",
    "intimate partner violence",
    "marital violence",
    "sexual violence",
    "sexual abuse",
    "violence against women",
    "violence against girls",
    "coercive control",
    "forced marriage",
    "child marriage",
    "early marriage",
    "forced sterilization",
    "reproductive rights",
    "women's rights",
    "women rights",
    "girls' rights",
    "girls rights",
    "LGBT rights",
    "LGBTQ rights",
    "LGBT persecution",
    "anti-LGBT",
    "homophobia",
    "transphobia",

    # Surveillance / vie privée (ajouté pour couvrir la recherche
    # académique sur la surveillance numérique, ex. caméras chinoises
    # en Asie centrale).
    "mass surveillance",
    "surveillance cameras",
    "facial recognition",
    "biometric surveillance",
    "digital authoritarianism",
    "surveillance state",
    "chinese surveillance technology",
    "safe city surveillance",
    "privacy violation",
    "privacy rights",

    # Russian
    "пытк",
    "истязани",
    "жестокое обращение",
    "насилие в местах лишения свободы",
    "полицейское насилие",
    "насилие полиции",
    "насильственное исчезновение",
    "насильственно исчез",
    "исчезнувш",
    "внесудебное убийство",
    "смерть в заключении",
    "смерть в полиции",
    "религиозные преследования",
    "религиозная свобода",
    "дискриминаци",
    "этническая дискриминация",
    "гендерное насилие",
    "домашнее насилие",
    "семейное насилие",
    "насилие в семье",
    "насилие над женщинами",
    "насилие над детьми",
    "сексуальное насилие",
    "сексуальное насилие",
    "принудительный брак",
    "ранний брак",
    "детский брак",
    "принудительная стерилизация",
    "репродуктивные права",
    "права женщин",
    "права девушек",
    "ЛГБТ",
    "гомофоб",
    "трансфоб",

    # Surveillance / vie privée — russe
    "массовая слежка",
    "видеонаблюдение",
    "распознавание лиц",
    "биометрическая слежка",
    "цифровой авторитаризм",
    "слежка за гражданами",
    "нарушение приватности",

    # Farsi
    "شکنجه",
    "بدرفتاری",
    "خشونت پلیس",
    "ناپدید شدن اجباری",
    "اعدام",
    "حکم اعدام",
    "مجازات اعدام",
    "اعدام خارج از روند قضایی",
    "مرگ در بازداشت",
    "آزار مذهبی",
    "آزادی مذهبی",
    "تبعیض قومی",
    "خشونت خانگی",
    "خشونت علیه زنان",
    "خشونت جنسی",
    "آزار جنسی",
    "ازدواج اجباری",
    "ازدواج کودکان",
    "حقوق زنان",
    "حقوق دختران",
    "حقوق اقلیت‌های جنسی",
]

# ------------------------------------------------------------
# 12. CENTRAL ASIA HR TERMS
# ------------------------------------------------------------

CENTRAL_ASIA_HR_TERMS = [
    "human rights in kazakhstan",
    "human rights in uzbekistan",
    "human rights in kyrgyzstan",
    "human rights in tajikistan",
    "human rights in turkmenistan",
    "rights violations in kazakhstan",
    "rights violations in uzbekistan",
    "rights violations in kyrgyzstan",
    "rights violations in tajikistan",
    "rights violations in turkmenistan",
    "political repression in kazakhstan",
    "political repression in uzbekistan",
    "political repression in kyrgyzstan",
    "political repression in tajikistan",
    "political repression in turkmenistan",
]

# ------------------------------------------------------------
# 13. NEW V9 — CENTRAL ASIA REPRESSION EVENTS
# ------------------------------------------------------------

CENTRAL_ASIA_HR_EVENT_TERMS = [

    # Kazakhstan
    "bloody january",
    "bloody january 2022",
    "january events",
    "january 2022",
    "qantar",
    "qantar events",
    "almaty january",
    "january massacre",
    "january crackdown",
    "january protests",

    # Uzbekistan
    "nukus protests",
    "nukus protest",
    "nukus events",
    "nukus crackdown",
    "karakalpakstan protests",
    "karakalpakstan protest",
    "karakalpakstan crackdown",
    "july 2022 karakalpakstan",
    "karakalpakstan events",

    # Tajikistan
    "gorno-badakhshan",
    "gorno badakhshan",
    "gbao",
    "khorog protests",
    "khorog protest",
    "gbao crackdown",
    "pamiri crackdown",
    "pamiri repression",

    # Kyrgyzstan
    "kempir-abad",
    "kempir abad",
    "kempir-abad case",
    "kempir abad case",
    "october 2020 protests",
    "2020 protests kyrgyzstan",

    # Turkmenistan
    "turkmenistan political prisoners",
    "turkmenistan crackdown",
    "turkmenistan repression",

    # General
    "central asian crackdown",
    "central asia crackdown",
    "central asia repression",
    "central asian repression",

    # Russian
    "кровавый январь",
    "январские события",
    "январь 2022",
    "кантар",
    "кантарские события",
    "протесты в нукусе",
    "события в нукусе",
    "беспорядки в нукусе",
    "разгон протестов в нукусе",
    "каракалпакстан",
    "протесты в каракалпакстане",
    "события в каракалпакстане",
    "горно-бадахшан",
    "гбао",
    "протесты в хороге",
    "памирцы",
    "репрессии в горно-бадахшане",
    "кемпир-абад",
]

# ------------------------------------------------------------
# 14. NEW V9 — POLITICAL / RULE OF LAW
# ------------------------------------------------------------

POLITICAL_RIGHTS_TERMS_V9 = [
    "lifetime immunity",
    "immunity from prosecution",
    "immunity from criminal prosecution",
    "presidential immunity",
    "political immunity",
    "judicial independence",
    "lack of judicial independence",
    "political control of courts",
    "political interference in judiciary",
    "executive interference",
    "rule of law",
    "weak rule of law",
    "erosion of rule of law",
    "checks and balances",
    "concentration of power",
    "concentrate power",
    "concentration of executive power",
    "abuse of presidential power",
    "abuse of executive power",
    "constitutional changes",
    "constitutional amendment",
    "constitutional amendments",
    "authoritarian rule",
    "authoritarianism",
    "one-party rule",
    "political monopoly",
    "lack of accountability",
    "absence of accountability",
    "impunity",
    "official impunity",

    # Russian
    "пожизненный иммунитет",
    "пожизненная неприкосновенность",
    "иммунитет от уголовного преследования",
    "президентская неприкосновенность",
    "судебная независимость",
    "независимость судов",
    "зависимость судов",
    "политическое влияние на суд",
    "вмешательство в работу суда",
    "верховенство закона",
    "ослабление верховенства закона",
    "концентрация власти",
    "концентрация исполнительной власти",
    "злоупотребление властью",
    "злоупотребление полномочиями",
    "расширение полномочий президента",
    "отсутствие подотчетности",
    "безнаказанность",
    "политическая монополия",
    "авторитарное правление",
]

# ------------------------------------------------------------
# 15. NEW V9 — PRESS REPRESSION
# ------------------------------------------------------------

PRESS_REPRESSION_TERMS_V9 = [
    "journalist detained",
    "journalist arrested",
    "journalist imprisoned",
    "journalist sentenced",
    "journalist prosecuted",
    "journalist charged",
    "journalist convicted",
    "journalist attacked",
    "journalist assaulted",
    "journalist disappeared",
    "journalist threatened",
    "journalist harassed",
    "editor arrested",
    "editor detained",
    "media outlet blocked",
    "media outlet shut down",
    "news website blocked",
    "website blocked",
    "internet shutdown",
    "internet blackout",
    "online censorship",
    "press censorship",
    "media censorship",
    "media restrictions",
    "press restrictions",
    "ban on independent media",
    "independent media banned",
    "foreign agent law",
    "foreign agents law",

    # Russian
    "журналист задержан",
    "журналист арестован",
    "журналист заключен",
    "журналист осужден",
    "журналист привлечен",
    "журналист обвинен",
    "журналист атакован",
    "журналист избит",
    "журналист исчез",
    "журналисту угрожали",
    "журналиста преследуют",
    "редактор арестован",
    "редактор задержан",
    "СМИ заблокировано",
    "СМИ закрыто",
    "сайт заблокирован",
    "блокировка сайта",
    "отключение интернета",
    "интернет отключили",
    "интернет-цензура",
    "цензура СМИ",
    "ограничение СМИ",
    "запрет независимых СМИ",
]

# ------------------------------------------------------------
# 16. NEW V9 — GENDER-BASED VIOLENCE
# ------------------------------------------------------------

GENDER_VIOLENCE_TERMS_V9 = [
    "gender-based violence",
    "gender based violence",
    "domestic violence",
    "domestic abuse",
    "family violence",
    "intimate partner violence",
    "marital violence",
    "violence against women",
    "violence against girls",
    "violence against wives",
    "violence against daughters-in-law",
    "abuse of women",
    "abuse of girls",
    "coercive control",
    "forced marriage",
    "arranged marriage under coercion",
    "child marriage",
    "early marriage",
    "honor violence",
    "honour violence",
    "sexual violence",
    "sexual abuse",
    "rape",
    "marital rape",
    "women's rights",
    "women rights",
    "girls' rights",
    "girls rights",
    "daughters-in-law",
    "daughter-in-law",
    "bride abuse",
    "bride violence",

    # Russian
    "гендерное насилие",
    "домашнее насилие",
    "семейное насилие",
    "насилие в семье",
    "насилие над женщинами",
    "насилие над девушками",
    "насилие над женами",
    "насилие над невестками",
    "насилие над снохами",
    "жестокое обращение с женщинами",
    "принудительный брак",
    "принудительное замужество",
    "ранний брак",
    "детский брак",
    "насилие в браке",
    "сексуальное насилие",
    "сексуальное насилие над женщинами",
    "изнасилование",
    "супружеское изнасилование",
    "права женщин",
    "права девушек",
    "невестка",
    "сноха",
    "насилие над невестками",
]

# ------------------------------------------------------------
# 17. NEW V9 — TRANSNATIONAL REPRESSION
# ------------------------------------------------------------

TRANSNATIONAL_REPRESSION_TERMS_V9 = [
    "transnational repression",
    "transnational persecution",
    "targeted abroad",
    "harassed abroad",
    "threatened abroad",
    "surveillance abroad",
    "dissidents abroad",
    "activists abroad",
    "opposition abroad",
    "extradition request",
    "extradition request against",
    "extradited",
    "deported",
    "deportation",
    "rendition",
    "kidnapped abroad",
    "abducted abroad",
    "detained abroad",
    "arrested abroad",
    "forced return",
    "forced repatriation",
    "political asylum",
    "asylum seeker",
    "asylum seekers",

    # Russian
    "транснациональные репрессии",
    "транснациональные репрессии",
    "преследование за рубежом",
    "преследуется за рубежом",
    "угрозы за рубежом",
    "слежка за рубежом",
    "диссиденты за рубежом",
    "активисты за рубежом",
    "оппозиция за рубежом",
    "запрос на экстрадицию",
    "экстрадиция",
    "экстрадирован",
    "депортирован",
    "депортация",
    "похищен за рубежом",
    "задержан за рубежом",
    "арестован за рубежом",
    "принудительное возвращение",
    "политическое убежище",
]

# ------------------------------------------------------------
# 18. NEW V9 — POLITICAL PRISONERS / DETAINEES
# ------------------------------------------------------------

POLITICAL_PRISONER_TERMS_V9 = [
    "political prisoner",
    "political prisoners",
    "political detainee",
    "political detainees",
    "prisoner of conscience",
    "prisoners of conscience",
    "wrongfully imprisoned",
    "wrongfully detained",
    "arbitrarily detained",
    "arbitrary detention",
    "arbitrarily arrested",
    "arbitrary arrest",
    "politically motivated imprisonment",
    "politically motivated detention",
    "politically motivated charges",
    "political prosecution",
    "political trial",
    "show trial",
    "political conviction",

    # Russian
    "политический заключенный",
    "политические заключенные",
    "политзаключенный",
    "политзаключенные",
    "политический узник",
    "узник совести",
    "узники совести",
    "произвольно задержан",
    "произвольное задержание",
    "произвольный арест",
    "политически мотивированное обвинение",
    "политически мотивированное дело",
    "политическое преследование",
    "политический процесс",
    "показательный процесс",
]

# ------------------------------------------------------------
# 19. DOMESTIC POLITICAL TERMS
# ------------------------------------------------------------

DOMESTIC_POLITICAL_TERMS = [
    "president",
    "presidential",
    "government",
    "parliament",
    "parliamentary",
    "prime minister",
    "ministry",
    "minister",
    "authorities",
    "officials",
    "election",
    "elections",
    "opposition",
    "political opposition",
    "protest",
    "protests",
    "demonstration",
    "demonstrations",
    "rally",
    "rallies",
    "referendum",
    "constitutional reform",
    "political reform",
    "political crisis",
    "political unrest",
    "political instability",

    # Russian
    "президент",
    "президентский",
    "правительство",
    "парламент",
    "премьер-министр",
    "министерство",
    "министр",
    "власти",
    "чиновники",
    "выборы",
    "оппозиция",
    "протест",
    "протесты",
    "митинг",
    "митинги",
    "демонстрация",
    "референдум",
    "конституционная реформа",
    "политическая реформа",
    "политический кризис",
]

# ------------------------------------------------------------
# 20. MAJOR GEOPOLITICS
# ------------------------------------------------------------

MAJOR_GEOPOLITICAL_TERMS = [
    "war",
    "invasion",
    "military operation",
    "armed conflict",
    "conflict",
    "ceasefire",
    "peace agreement",
    "sanctions",
    "sanction",
    "security alliance",
    "military alliance",
    "troops",
    "military base",
    "border conflict",
    "border clashes",
    "terrorism",
    "terrorist attack",
    "counterterrorism",
    "security operation",
    "geopolitical",
    "foreign interference",
    "foreign influence",
    "strategic partnership",
    "security cooperation",
    "china",
    "russia",
    "united states",
    "european union",
    "iran",
    "afghanistan",
    "ukraine",

    # Sécurité régionale (ajouté pour les sources spécialisées
    # sécurité/think tanks — cf. profil "security_analysis").
    "insurgency",
    "insurgent",
    "insurgents",
    "militant",
    "militants",
    "extremism",
    "violent extremism",
    "radicalization",
    "radicalisation",
    "jihadist",
    "islamist militant",
    "islamic state",
    "isis-k",
    "al-qaeda",
    "taliban",
    "drug trafficking",
    "narcotics trafficking",
    "arms trafficking",
    "weapons smuggling",
    "border security",
    "security threat",
    "national security",
    "collective security treaty organization",
    "csto",
    "hybrid warfare",
    "cyberattack",
    "cyber attack",
    "proxy war",
    "destabilization",
    "instability",
    "power vacuum",
    "cross-border attack",
    "security cooperation agreement",

    # Russian
    "война",
    "вторжение",
    "военная операция",
    "вооруженный конфликт",
    "конфликт",
    "перемирие",
    "мирное соглашение",
    "санкции",
    "военный союз",
    "войска",
    "военная база",
    "пограничный конфликт",
    "пограничные столкновения",
    "терроризм",
    "террористический акт",
    "контртеррористическая операция",
    "иностранное вмешательство",
    "иностранное влияние",
    "стратегическое партнерство",
    "китай",
    "россия",
    "сша",
    "евросоюз",
    "иран",
    "афганистан",
    "украина",

    # Sécurité régionale — russe
    "повстанцы",
    "боевики",
    "экстремизм",
    "насильственный экстремизм",
    "радикализация",
    "исламист",
    "наркотрафик",
    "контрабанда оружия",
    "пограничная безопасность",
    "угроза безопасности",
    "национальная безопасность",
    "одкб",
    "гибридная война",
    "кибератака",
    "дестабилизация",
    "нестабильность",
    "игил",
    "аль-каида",
    "талибан",
]

# ------------------------------------------------------------
# 21. ROUTINE GEOPOLITICS
# ------------------------------------------------------------

ROUTINE_GEO_TERMS = [
    "meeting",
    "talks",
    "visit",
    "official visit",
    "delegation",
    "memorandum",
    "memorandum of understanding",
    "agreement signed",
    "trade agreement",
    "economic cooperation",
    "investment",
    "business forum",
    "summit",
    "conference",
    "bilateral relations",
    "diplomatic relations",
    "foreign minister",
    "president met",
    "leaders met",
]

# ------------------------------------------------------------
# 22. LOW-SIGNAL CONTEXT
# ------------------------------------------------------------

LOW_SIGNAL_CONTEXT_TERMS = [
    "development",
    "economic growth",
    "investment",
    "trade",
    "tourism",
    "culture",
    "cultural",
    "education",
    "sports",
    "football",
    "music",
    "festival",
    "infrastructure",
    "construction",
    "transport",
    "railway",
    "airport",
    "technology",
    "digitalization",
    "digitization",
    "startup",
    "business",
    "market",
    "industry",
    "agriculture",
    "weather",
    "climate",
    "environment",
]

# ------------------------------------------------------------
# 23. REGIONAL ACTORS
# ------------------------------------------------------------

REGIONAL_ACTORS = [
    "president",
    "government",
    "parliament",
    "ministry",
    "minister",
    "prosecutor",
    "prosecutors",
    "police",
    "security service",
    "national security",
    "intelligence service",
    "court",
    "judge",
    "judges",
    "prosecution",
    "authorities",
    "officials",
    "law enforcement",

    # Russian
    "президент",
    "правительство",
    "парламент",
    "министерство",
    "министр",
    "прокуратура",
    "прокурор",
    "полиция",
    "служба безопасности",
    "спецслужбы",
    "суд",
    "судья",
    "власти",
    "чиновники",
    "правоохранительные органы",
]

# ------------------------------------------------------------
# 24. HISTORICAL
# ------------------------------------------------------------

HISTORICAL_TERMS = [
    "history",
    "historical",
    "in the soviet era",
    "soviet era",
    "soviet period",
    "during the soviet union",
    "stalin",
    "stalinist",
    "deportation under stalin",
    "world war ii",
    "second world war",
    "cold war",
    "ussr",
    "soviet union",
    "historical memory",
    "commemoration",
    "anniversary",

    # Russian
    "история",
    "исторический",
    "советский период",
    "советское время",
    "советский союз",
    "сталин",
    "сталинский",
    "депортация при сталине",
    "вторая мировая война",
    "холодная война",
    "историческая память",
    "память",
    "годовщина",
]

# ------------------------------------------------------------
# 25. NON-NEWS
# ------------------------------------------------------------

NON_NEWS_TERMS = [
    "recipe",
    "horoscope",
    "weather forecast",
    "sports results",
    "football match",
    "celebrity",
    "fashion",
    "lifestyle",
    "real estate",
    "property",
    "car review",
    "restaurant",
    "travel guide",
    "tourist guide",
    "entertainment",
]

# ------------------------------------------------------------
# 26. NOISE
# ------------------------------------------------------------

NOISE_TERMS = [
    "advertisement",
    "sponsored",
    "promo",
    "promotion",
    "discount",
    "sale",
    "coupon",
    "shopping",
    "buy now",
    "subscribe now",
]

# ------------------------------------------------------------
# 27. SEVERE REPRESSION
# ------------------------------------------------------------

SEVERE_REPRESSION_TERMS = [
    "torture",
    "tortured",
    "forced disappearance",
    "enforced disappearance",
    "extrajudicial killing",
    "death in custody",
    "political prisoner",
    "political prisoners",
    "prisoner of conscience",
    "arbitrary detention",
    "arbitrary arrest",
    "forced labor",
    "forced labour",
    "mass detention",
    "mass arrests",
    "mass arrest",
    "violent crackdown",
    "deadly crackdown",
    "crackdown killed",
    "security forces killed",
    "security forces opened fire",
    "disappeared in custody",

    # Russian stems
    "пытк",
    "насильственное исчезновение",
    "внесудебное убийство",
    "смерть в заключении",
    "политзаключ",
    "узник совести",
    "произвольное задержание",
    "произвольный арест",
    "принудительный труд",
    "массовые задержания",
    "массовые аресты",
    "жесткий разгон",
    "жестокий разгон",
    "силы безопасности открыли огонь",
]

# ------------------------------------------------------------
# 28. ACTIVIST REPRESSION PATTERNS
# ------------------------------------------------------------

ACTIVIST_REPRESSION_PATTERNS = [
    r"\bactivist\b.{0,100}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|prosecuted)\b",
    r"\bactivists\b.{0,100}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|prosecuted)\b",
    r"\bhuman rights defender\b.{0,120}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|prosecuted)\b",
    r"\bdissident\b.{0,120}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|prosecuted)\b",
]

# ------------------------------------------------------------
# 29. JOURNALIST REPRESSION PATTERNS
# ------------------------------------------------------------

JOURNALIST_REPRESSION_PATTERNS = [
    r"\bjournalist\b.{0,100}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|prosecuted)\b",
    r"\breporter\b.{0,100}\b(arrested|detained|jailed|imprisoned|charged|convicted|sentenced|prosecuted)\b",
    r"\bjournalist\b.{0,100}\b(threatened|harassed|attacked|assaulted)\b",
    r"\bmedia outlet\b.{0,100}\b(blocked|banned|closed|shut down)\b",
    r"\bwebsite\b.{0,100}\b(blocked|banned|censored)\b",
]

# ------------------------------------------------------------
# 30. RUSSIAN ACTIVIST REPRESSION
# ------------------------------------------------------------

ACTIVIST_REPRESSION_RU_PATTERNS = [
    r"активист.{0,100}(задержан|арестован|осужден|заключен|преследуется|обвинен)",
    r"правозащитник.{0,120}(задержан|арестован|осужден|заключен|преследуется|обвинен)",
    r"оппозиционер.{0,120}(задержан|арестован|осужден|заключен|преследуется|обвинен)",
    r"диссидент.{0,120}(задержан|арестован|осужден|заключен|преследуется|обвинен)",
]

# ------------------------------------------------------------
# 31. RUSSIAN JOURNALIST REPRESSION
# ------------------------------------------------------------

JOURNALIST_REPRESSION_RU_PATTERNS = [
    r"журналист.{0,100}(задержан|арестован|осужден|заключен|обвинен|преследуется)",
    r"репортер.{0,100}(задержан|арестован|осужден|заключен|обвинен)",
    r"журналист.{0,100}(угрожали|избит|атакован|нападение)",
    r"СМИ.{0,100}(заблокировано|закрыто|запрещено)",
    r"сайт.{0,100}(заблокирован|запрещен)",
]

# ------------------------------------------------------------
# 30bis. FARSI ACTIVIST REPRESSION
#
# Ajouté après l'intégration d'IRNA/Fararu (sources iraniennes) :
# sans ces motifs, un article persan ne peut jamais atteindre
# confirmed_activist_pressure/confirmed_journalist_pressure — donc
# jamais le niveau A — quel que soit son contenu.
# ------------------------------------------------------------

ACTIVIST_REPRESSION_FA_PATTERNS = [
    r"فعال.{0,100}(بازداشت|دستگیر|زندانی|محکوم)",
    r"فعال حقوق بشر.{0,120}(بازداشت|دستگیر|زندانی|محکوم)",
    r"فعال مدنی.{0,120}(بازداشت|دستگیر|زندانی|محکوم)",
    r"چهره اپوزیسیون.{0,120}(بازداشت|دستگیر|زندانی|محکوم)",
]

# ------------------------------------------------------------
# 31bis. FARSI JOURNALIST REPRESSION
# ------------------------------------------------------------

JOURNALIST_REPRESSION_FA_PATTERNS = [
    r"روزنامه‌نگار.{0,100}(بازداشت|دستگیر|زندانی|محکوم)",
    r"روزنامه نگار.{0,100}(بازداشت|دستگیر|زندانی|محکوم)",
    r"خبرنگار.{0,100}(بازداشت|دستگیر|زندانی|محکوم)",
    r"روزنامه‌نگار.{0,100}(تهدید|ضرب و شتم|حمله)",
    r"رسانه.{0,100}(مسدود|بسته|ممنوع)",
    r"سایت.{0,100}(مسدود|فیلتر)",
]

# ------------------------------------------------------------
# 32. V9 — STRONG MORPHOLOGICAL REPRESSION PATTERNS
# ------------------------------------------------------------

REPRESSION_MORPHOLOGY_PATTERNS_V9 = [
    r"\bзадерж\w*\b",
    r"\bарест\w*\b",
    r"\bпреслед\w*\b",
    r"\bрепресс\w*\b",
    r"\bпыт\w*\b",
    r"\bцензур\w*\b",
    r"\bзапрет\w*\b",
    r"\bподав\w*\b",
    r"\bпритесн\w*\b",
    r"\bугрож\w*\b",
    r"\bзапуг\w*\b",
    r"\bзаключ\w*\b",
    r"\bосужден\w*\b",
    r"\bприговор\w*\b",
    r"\bобвин\w*\b",
]

# ------------------------------------------------------------
# 33. WEIGHTS
# ------------------------------------------------------------

REPRESSION_WEIGHTS = {
    "torture": 15,
    "forced disappearance": 15,
    "enforced disappearance": 15,
    "political prisoner": 14,
    "political prisoners": 14,
    "arbitrary detention": 12,
    "arbitrary arrest": 12,
    "political repression": 10,
    "crackdown": 9,
    "persecution": 9,
    "harassment": 6,
    "intimidation": 6,
    "censorship": 7,
    "suppression": 7,
    "political prosecution": 12,
    "politically motivated prosecution": 14,
}

# ------------------------------------------------------------
# 34. SPECIFIC RIGHTS WEIGHTS
# ------------------------------------------------------------

SPECIFIC_RIGHTS_WEIGHTS = {
    "torture": 10,
    "forced disappearance": 10,
    "enforced disappearance": 10,
    "extrajudicial killing": 10,
    "death in custody": 9,
    "gender-based violence": 7,
    "domestic violence": 7,
    "domestic abuse": 7,
    "sexual violence": 8,
    "sexual abuse": 8,
    "forced marriage": 7,
    "child marriage": 7,
    "religious persecution": 7,
    "religious freedom": 5,
    "ethnic discrimination": 6,
    "LGBT persecution": 8,
    "LGBT rights": 5,
}

# ------------------------------------------------------------
# 35. VICTIMS
# ------------------------------------------------------------

VICTIM_TERMS = [
    "victim",
    "victims",
    "survivor",
    "survivors",
    "family of",
    "families of",
    "relatives",
    "detainee",
    "detainees",
    "prisoner",
    "prisoners",
    "civilian",
    "civilians",
    "women",
    "girls",
    "children",
    "minority",
    "minorities",
    "dissident",
    "dissidents",

    # Russian
    "жертва",
    "жертвы",
    "пострадавший",
    "пострадавшие",
    "выживший",
    "выжившие",
    "родственники",
    "задержанный",
    "задержанные",
    "заключенный",
    "заключенные",
    "гражданские",
    "женщины",
    "девушки",
    "дети",
    "меньшинства",
]

# ------------------------------------------------------------
# 36. V9 — LOW-SIGNAL POLITICAL / REFORM TERMS
#     These should NEVER be strong on their own.
# ------------------------------------------------------------

GENERIC_REFORM_TERMS_V9 = [
    "reform",
    "reforms",
    "modernization",
    "modernisation",
    "new law",
    "new legislation",
    "law passed",
    "law adopted",
    "amendment",
    "amendments",
    "democracy score",
    "democratic decline",
    "democratic backsliding",
    "political reform",
    "institutional reform",
    "governance reform",
    "governance",
    "accountability",
    "transparency",
    "civic space",
    "civil society",

    # Russian
    "реформа",
    "реформы",
    "модернизация",
    "новый закон",
    "новое законодательство",
    "закон принят",
    "поправки",
    "демократический спад",
    "демократическое отступление",
    "политическая реформа",
    "институциональная реформа",
    "управление",
    "подотчетность",
    "прозрачность",
    "гражданское общество",
]

# ------------------------------------------------------------
# 37. V9 — NON-HR TOPICS
# ------------------------------------------------------------

NON_HR_TOPIC_TERMS_V9 = [
    "economy",
    "economic growth",
    "trade",
    "investment",
    "business",
    "tourism",
    "tourist",
    "culture",
    "cultural",
    "museum",
    "music",
    "film",
    "festival",
    "sport",
    "football",
    "construction",
    "infrastructure",
    "railway",
    "airport",
    "energy",
    "oil",
    "gas",
    "agriculture",
    "harvest",
    "technology",
    "digital",
    "startup",
    "real estate",

    # Russian
    "экономика",
    "экономический рост",
    "торговля",
    "инвестиции",
    "бизнес",
    "туризм",
    "турист",
    "культура",
    "музей",
    "музыка",
    "фильм",
    "фестиваль",
    "спорт",
    "футбол",
    "строительство",
    "инфраструктура",
    "железная дорога",
    "аэропорт",
    "энергетика",
    "нефть",
    "газ",
    "сельское хозяйство",
    "урожай",
    "технологии",
    "цифровизация",
    "стартап",
    "недвижимость",
]

# ------------------------------------------------------------
# 38. V9 — ACADEMIC / EDUCATIONAL RIGHTS
# ------------------------------------------------------------

ACADEMIC_HR_TERMS_V9 = [
    "academic freedom",
    "academic freedom violated",
    "university repression",
    "university crackdown",
    "professor arrested",
    "professor detained",
    "student activist",
    "student activists",
    "student protest",
    "student protests",
    "campus repression",
    "academic censorship",
    "researcher prosecuted",
    "researcher detained",
    "scholar persecuted",

    # Russian
    "академическая свобода",
    "репрессии в университете",
    "преследование преподавателя",
    "преподаватель арестован",
    "преподаватель задержан",
    "студент-активист",
    "студенты-активисты",
    "студенческий протест",
    "студенческие протесты",
    "цензура в университете",
    "ученый преследуется",
    "исследователь задержан",
]

# ------------------------------------------------------------
# 39. V9 — EVENT ANCHOR WEIGHTS
# ------------------------------------------------------------

EVENT_ANCHOR_WEIGHTS_V9 = {
    "bloody january": 12,
    "bloody january 2022": 12,
    "january events": 10,
    "qantar": 12,

    "nukus protests": 11,
    "nukus protest": 11,
    "nukus events": 10,
    "nukus crackdown": 13,
    "karakalpakstan protests": 11,
    "karakalpakstan crackdown": 13,

    "gorno-badakhshan": 8,
    "gbao": 8,
    "khorog protests": 11,
    "gbao crackdown": 13,
    "pamiri crackdown": 13,

    "kempir-abad": 7,
    "kempir-abad case": 9,

    "central asia crackdown": 10,
    "central asian repression": 10,
}

# ------------------------------------------------------------
# 40. V9 — REGIONAL SOURCE HINTS
# ------------------------------------------------------------

REGIONAL_SOURCE_HINTS_V9 = [
    "eurasianet",
    "diplomat",
    "occrp",
    "amnesty",
    "human rights watch",
    "hrw",
    "cpj",
    "rsf",
    "novastan",
    "times of central asia",
    "asia-plus",
    "asia plus",
    "kloop",
    "24.kg",
    "kaktus",
    "kabar",
    "radio ozodi",
    "radio azattyq",
    "gazeta.uz",
    "kun.uz",
    "spot.uz",
    "turkmen.news",
    "fergana",
    "central asia-caucasus analyst",
    "azernews",
    "uznews",
    "kursiv",
    "vlast",
    "orda",
    "tengrinews",
]

# ------------------------------------------------------------
# 41. V9 — TERMS THAT SHOULD NOT TRIGGER STRONG REPRESSION
# ------------------------------------------------------------

GENERIC_LEGAL_TERMS_V9 = [
    "trial",
    "sentence",
    "sentenced",
    "court",
    "case",
    "law",
    "lawsuit",
    "judge",
    "judges",
    "prosecutor",
    "prosecution",
    "government",
    "president",
    "official",
    "officials",
    "minister",
    "parliament",
]

# ------------------------------------------------------------
# 42. V9 — STRONG PRIMARY RIGHTS
# ------------------------------------------------------------

STRONG_PRIMARY_RIGHTS_V9 = [
    "torture",
    "forced disappearance",
    "enforced disappearance",
    "extrajudicial killing",
    "death in custody",
    "forced labor",
    "forced labour",
    "political prisoner",
    "political prisoners",
    "prisoner of conscience",
    "arbitrary detention",
    "arbitrary arrest",
    "gender-based violence",
    "domestic violence",
    "domestic abuse",
    "sexual violence",
    "sexual abuse",
    "forced marriage",
    "child marriage",
    "LGBT persecution",
    "religious persecution",
    "ethnic persecution",
    "journalist detained",
    "journalist arrested",
    "journalist imprisoned",
    "media outlet blocked",
    "internet shutdown",
]

# ------------------------------------------------------------
# 43. V9 — STRONG POLITICAL CONTEXT
# ------------------------------------------------------------

STRONG_POLITICAL_CONTEXT_V9 = [
    "political repression",
    "state repression",
    "government repression",
    "political persecution",
    "political prosecution",
    "politically motivated prosecution",
    "politically motivated charges",
    "political prisoner",
    "political prisoners",
    "prisoner of conscience",
    "arbitrary detention",
    "arbitrary arrest",
    "judicial independence",
    "political control of courts",
    "concentration of power",
    "abuse of presidential power",
    "lifetime immunity",
    "immunity from prosecution",
    "transnational repression",
    "foreign interference",
]

# ------------------------------------------------------------
# 44. V9 — DEMOCRACY / CIVIC SPACE
# ------------------------------------------------------------

DEMOCRACY_CIVIC_SPACE_TERMS_V9 = [
    "democratic decline",
    "democratic backsliding",
    "democracy score",
    "declining democracy",
    "shrinking civic space",
    "civic space",
    "civil society restrictions",
    "restrictions on civil society",
    "political pluralism",
    "political participation",
    "electoral freedom",
    "free and fair elections",
    "election repression",
    "election interference",
    "voter intimidation",
    "opposition crackdown",

    # Russian
    "демократический спад",
    "демократическое отступление",
    "рейтинг демократии",
    "сокращение гражданского пространства",
    "ограничение гражданского общества",
    "политический плюрализм",
    "политическое участие",
    "свободные и честные выборы",
    "давление на оппозицию",
    "преследование оппозиции",
]

# ------------------------------------------------------------
# 45. V9 — CONTEXTUAL VICTIM / TARGET COMBINATIONS
# ------------------------------------------------------------

TARGET_TERMS_V9 = [
    "activist",
    "activists",
    "human rights defender",
    "human rights defenders",
    "journalist",
    "journalists",
    "reporter",
    "reporters",
    "dissident",
    "dissidents",
    "opposition",
    "opposition figure",
    "opposition figures",
    "civil society",
    "ngo",
    "ngo worker",
    "lawyer",
    "lawyers",
    "blogger",
    "bloggers",
    "political opponent",
    "political opponents",

    # Russian
    "активист",
    "активисты",
    "правозащитник",
    "правозащитники",
    "журналист",
    "журналисты",
    "репортер",
    "диссидент",
    "оппозиция",
    "оппозиционер",
    "гражданское общество",
    "правозащитная организация",
    "юрист",
    "юристы",
    "блогер",
    "блогеры",
]

# ------------------------------------------------------------
# 46. V9 — COMBINED SIGNAL WEIGHTS
# ------------------------------------------------------------

REPRESSION_COMBINATION_WEIGHTS_V9 = {
    "target_plus_repression": 15,
    "journalist_plus_repression": 20,
    "activist_plus_repression": 18,
    "political_prisoner": 22,
    "torture_plus_detention": 22,
    "disappearance_plus_state_actor": 25,
    "forced_labor_plus_state_actor": 22,
    "gender_violence_plus_women": 12,
    "event_plus_repression": 18,
    "event_plus_target": 14,
    "rule_of_law_plus_political_power": 10,
    "transnational_plus_dissident": 18,
}

# ------------------------------------------------------------
# 47. V9 — BODY CONFIRMATION TERMS
#     These are deliberately weaker than primary signals.
# ------------------------------------------------------------

BODY_CONFIRMATION_TERMS_V9 = [
    "arrested",
    "detained",
    "imprisoned",
    "jailed",
    "sentenced",
    "convicted",
    "charged",
    "prosecuted",
    "tortured",
    "beaten",
    "threatened",
    "harassed",
    "blocked",
    "banned",
    "censored",
    "disappeared",
    "kidnapped",
    "deported",
    "extradited",
    "forced",
    "coerced",

    # Russian morphology
    "задерж",
    "арест",
    "осужден",
    "приговор",
    "обвин",
    "заключ",
    "преслед",
    "пыт",
    "угрож",
    "запрет",
    "заблок",
    "исчез",
    "похищ",
    "депорт",
    "экстрад",
    "принуд",
    "насили",
]

# ------------------------------------------------------------
# 48. V9 — EXPLICIT HR ACTIONS
# ------------------------------------------------------------

EXPLICIT_HR_ACTION_TERMS_V9 = [
    "arrested",
    "detained",
    "imprisoned",
    "jailed",
    "tortured",
    "beaten",
    "disappeared",
    "killed",
    "threatened",
    "harassed",
    "prosecuted",
    "convicted",
    "sentenced",
    "blocked",
    "banned",
    "censored",
    "forced",
    "coerced",
    "persecuted",
    "repressed",

    # Russian
    "задержан",
    "арестован",
    "заключен",
    "осужден",
    "приговорен",
    "пытали",
    "избит",
    "исчез",
    "убит",
    "угрожали",
    "преследуется",
    "запрещен",
    "заблокирован",
    "принужден",
    "репрессирован",

    # Farsi
    "بازداشت",
    "دستگیر",
    "زندانی",
    "شکنجه",
    "کشته",
    "ناپدید",
    "تهدید",
    "محکوم",
    "ممنوع",
    "مسدود",
    "سرکوب",
]

# ------------------------------------------------------------
# END keywords.py V9
# ------------------------------------------------------------
