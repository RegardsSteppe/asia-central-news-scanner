# ============================================================
# SOURCES
# ============================================================

SOURCES = [

    # ========================================================
    # INTERNATIONAL / INDÉPENDANT
    # ========================================================

    {
        "name": "Radio Free Europe / Radio Liberty",
        "short_name": "RFE/RL",
        "profile": "international_independent",
        "label": "International · indépendant",
        "type": "rss",

        "url": "https://www.rferl.org/",

        "feeds": [
            "https://www.rferl.org/api/zriiml-vomx-tpeogm_",
            "https://www.rferl.org/api/zqii_l-vomx-tpeigmy",
            "https://www.rferl.org/api/z_iiol-vomx-tpevgmi",
            "https://www.rferl.org/api/ztiiml-vomx-tpekgm_",
            "https://www.rferl.org/api/ztukmrl-vomx-tpeki-mo",
        ],

        "fallbacks": [
            "https://www.rferl.org/p/5549.html",
        ],

        "max_articles": 150,
    },

    {
        "name": "Eurasianet",
        "short_name": "Eurasianet",
        "profile": "independent",
        "label": "Indépendant · régional",
        "type": "html",

        "url": "https://eurasianet.org/latest",

        "fallbacks": [
            "https://eurasianet.org/",
        ],

        "max_articles": 120,
    },

    {
        "name": "Cabar.asia",
        "short_name": "CABAR",
        "profile": "independent",
        "label": "Indépendant · Asie centrale",
        "type": "rss",

        "url": "https://cabar.asia/en/",

        "feeds": [
            "https://cabar.asia/en/feed",
        ],

        "fallbacks": [
            "https://cabar.asia/en/",
        ],

        "max_articles": 120,
    },

    {
        "name": "The Diplomat",
        "short_name": "The Diplomat",
        "profile": "international_analysis",
        "label": "International · analyse",
        "type": "html",

        "url": "https://thediplomat.com/regions/central-asia/",

        "fallbacks": [
            "https://thediplomat.com/",
        ],

        "max_articles": 100,
    },

    # ========================================================
    # INVESTIGATION
    # ========================================================

    {
        "name": "OCCRP",
        "short_name": "OCCRP",
        "profile": "investigative",
        "label": "International · investigation",
        "type": "html",

        "url": "https://www.occrp.org/en/",

        "max_articles": 100,
    },

    # ========================================================
    # DROITS HUMAINS
    # ========================================================

    {
        "name": "Human Rights Watch",
        "short_name": "HRW",
        "profile": "human_rights",
        "label": "International · droits humains",
        "type": "html",

        "url": "https://www.hrw.org/asia/",

        "fallbacks": [
            "https://www.hrw.org/asia",
        ],

        "max_articles": 80,
    },

    {
        "name": "Amnesty International",
        "short_name": "Amnesty",
        "profile": "human_rights",
        "label": "International · droits humains",
        "type": "html",

        "url": "https://www.amnesty.org/",

        "max_articles": 80,
    },

    {
        "name": "Committee to Protect Journalists",
        "short_name": "CPJ",
        "profile": "press_freedom",
        "label": "International · liberté de la presse",
        "type": "html",

        "url": "https://cpj.org/",

        "max_articles": 80,
    },

    {
        "name": "Reporters Without Borders",
        "short_name": "RSF",
        "profile": "press_freedom",
        "label": "International · liberté de la presse",
        "type": "html",

        "url": "https://rsf.org/",

        "max_articles": 80,
    },

    # ========================================================
    # RÉGIONAL
    # ========================================================

    {
        "name": "The Times of Central Asia",
        "short_name": "TCA",
        "profile": "regional_independent",
        "label": "Régional · indépendant",
        "type": "html",

        "url": "https://timesca.com/",

        "max_articles": 100,
    },

    {
        "name": "Novastan",
        "short_name": "Novastan",
        "profile": "regional_independent",
        "label": "Régional · indépendant",
        "type": "html",

        "url": "https://novastan.org/en/",

        "max_articles": 100,
    },

    {
        "name": "UzNews24",
        "short_name": "UzNews24",
        "profile": "regional_media",
        "label": "Régional · Ouzbékistan",
        "type": "html",

        "url": "https://uznews.uz/en",

        "max_articles": 100,
    },

    {
        "name": "Sarpa Media",
        "short_name": "Sarpa",
        "profile": "regional_independent",
        "label": "Régional · indépendant",
        "type": "html",

        "url": "https://sarpa.media/",

        "max_articles": 100,
    },

    {
        "name": "Kursiv Media",
        "short_name": "Kursiv",
        "profile": "regional_media",
        "label": "Régional · business & politique",
        "type": "html",

        "url": "https://kz.kursiv.media/en/",

        "max_articles": 100,
    },

    # ========================================================
    # KAZAKHSTAN
    # ========================================================

    {
        "name": "Vlast",
        "short_name": "Vlast",
        "profile": "regional_independent",
        "label": "Régional · Kazakhstan",
        "type": "html",

        "url": "https://vlast.kz/",

        "max_articles": 100,
    },

    {
        "name": "Radio Azattyq",
        "short_name": "Azattyq",
        "profile": "international_independent",
        "label": "International · Kazakhstan",
        "type": "html",

        "url": "https://www.azattyq.org/",

        "max_articles": 100,
    },

    {
        "name": "Orda.kz",
        "short_name": "Orda",
        "profile": "regional_independent",
        "label": "Indépendant · Kazakhstan",
        "type": "html",

        "url": "https://orda.kz/",

        "max_articles": 100,
    },

    {
        "name": "Tengrinews",
        "short_name": "Tengrinews",
        "profile": "regional_media",
        "label": "Média régional · Kazakhstan",
        "type": "html",

        "url": "https://en.tengrinews.kz/",

        "max_articles": 100,
    },

    # ========================================================
    # KIRGHIZISTAN
    # ========================================================

    {
        "name": "Kloop",
        "short_name": "Kloop",
        "profile": "investigative",
        "label": "Investigation · Kirghizistan",
        "type": "html",

        "url": "https://kloop.kg/",

        "max_articles": 100,
    },

    {
        "name": "24.kg",
        "short_name": "24.kg",
        "profile": "regional_media",
        "label": "Régional · Kirghizistan",
        "type": "html",

        "url": "https://24.kg/",

        "max_articles": 100,
    },

    {
        "name": "Kaktus Media",
        "short_name": "Kaktus",
        "profile": "regional_independent",
        "label": "Indépendant · Kirghizistan",
        "type": "html",

        "url": "https://kaktus.media/",

        "max_articles": 100,
    },

    {
        "name": "Kabar",
        "short_name": "Kabar",
        "profile": "state_media",
        "label": "Agence officielle · Kirghizistan",
        "type": "html",

        "url": "https://en.kabar.kg/",

        "max_articles": 80,
    },

    # ========================================================
    # TADJIKISTAN
    # ========================================================

    {
        "name": "Asia-Plus",
        "short_name": "Asia-Plus",
        "profile": "regional_independent",
        "label": "Régional · Tadjikistan",
        "type": "html",

        "url": "https://asiaplustj.info/en",

        "max_articles": 100,
    },

    {
        "name": "Radio Ozodi",
        "short_name": "Ozodi",
        "profile": "international_independent",
        "label": "International · Tadjikistan",
        "type": "html",

        "url": "https://www.ozodi.org/",

        "max_articles": 100,
    },

    # ========================================================
    # OUZBÉKISTAN
    # ========================================================

    {
        "name": "Gazeta.uz",
        "short_name": "Gazeta.uz",
        "profile": "regional_media",
        "label": "Régional · Ouzbékistan",
        "type": "html",

        "url": "https://www.gazeta.uz/en/",

        "max_articles": 100,
    },

    {
        "name": "Kun.uz",
        "short_name": "Kun.uz",
        "profile": "regional_media",
        "label": "Régional · Ouzbékistan",
        "type": "html",

        "url": "https://kun.uz/en",

        "max_articles": 100,
    },

    {
        "name": "Spot.uz",
        "short_name": "Spot.uz",
        "profile": "economic_media",
        "label": "Économie · Ouzbékistan",
        "type": "html",

        "url": "https://www.spot.uz/en/",

        "max_articles": 80,
    },

    # ========================================================
    # TURKMÉNISTAN
    # ========================================================

    {
        "name": "Turkmen.News",
        "short_name": "Turkmen.News",
        "profile": "human_rights",
        "label": "Indépendant · Turkménistan",
        "type": "html",

        "url": "https://turkmen.news/",

        "max_articles": 100,
    },

    {
        "name": "Chronicles of Turkmenistan",
        "short_name": "Chronicles",
        "profile": "human_rights",
        "label": "Indépendant · Turkménistan",
        "type": "html",

        "url": "https://hronikatm.com/",

        "max_articles": 100,
    },

    # ========================================================
    # RÉGIONAL / TRANSFRONTALIER
    # ========================================================

    {
        "name": "Fergana Agency",
        "short_name": "Fergana",
        "profile": "regional_independent",
        "label": "Régional · transfrontalier",
        "type": "html",

        "url": "https://fergana.agency/",

        "max_articles": 100,
    },

    {
        "name": "Central Asia-Caucasus Analyst",
        "short_name": "CAC Analyst",
        "profile": "regional_analysis",
        "label": "Régional · analyse",
        "type": "html",

        "url": "https://www.cacianalyst.org/",

        "max_articles": 80,
    },

    # ========================================================
    # CAUCASE
    # ========================================================

    {
        "name": "Azernews",
        "short_name": "Azernews",
        "profile": "regional_media",
        "label": "Régional · Caucase",
        "type": "html",

        "url": "https://www.azernews.az/latest/",

        "max_articles": 80,
    },
]


# ============================================================
# PROFILS DES SOURCES
# ============================================================

SOURCE_PROFILES = {

    "international_independent": {
        "name": "International · indépendant",
        "description": (
            "Média international indépendant ou à forte "
            "autonomie éditoriale."
        ),
    },

    "independent": {
        "name": "Indépendant",
        "description": (
            "Média indépendant spécialisé sur l'Asie centrale."
        ),
    },

    "international_analysis": {
        "name": "International · analyse",
        "description": (
            "Publication internationale orientée analyse, "
            "géopolitique et politique régionale."
        ),
    },

    "regional_independent": {
        "name": "Régional · indépendant",
        "description": (
            "Média régional indépendant couvrant "
            "l'actualité politique et sociale."
        ),
    },

    "regional_media": {
        "name": "Média régional",
        "description": (
            "Média régional couvrant notamment la politique, "
            "l'économie et l'actualité."
        ),
    },

    "investigative": {
        "name": "Investigation",
        "description": (
            "Source spécialisée dans le journalisme "
            "d'investigation, la corruption ou les abus de pouvoir."
        ),
    },

    "human_rights": {
        "name": "Droits humains",
        "description": (
            "Source spécialisée dans les droits humains, "
            "les libertés fondamentales et/ou les abus."
        ),
    },

    "press_freedom": {
        "name": "Liberté de la presse",
        "description": (
            "Source spécialisée dans la liberté de la presse, "
            "les journalistes et les médias."
        ),
    },

    "economic_media": {
        "name": "Économie",
        "description": (
            "Source orientée économie, entreprises, marchés "
            "et politiques économiques."
        ),
    },

    "state_media": {
        "name": "Média officiel",
        "description": (
            "Agence ou média proche des institutions publiques. "
            "Utile comme source de comparaison et de contrepoint."
        ),
    },

    "regional_analysis": {
        "name": "Régional · analyse",
        "description": (
            "Publication spécialisée dans l'analyse politique "
            "et géopolitique de l'Asie centrale et du Caucase."
        ),
    },
}
