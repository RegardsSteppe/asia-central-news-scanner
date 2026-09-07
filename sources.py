# sources.py

SOURCES = [

    # ========================================================
    # SOURCES INTERNATIONALES / INDÉPENDANTES
    # ========================================================

    {
        "name": "Radio Free Europe / Radio Liberty",
        "short_name": "RFE/RL",
        "profile": "international_independent",
        "label": "International · indépendant",
        "type": "rss",
        "feeds": [
            "https://www.rferl.org/api/zriiml-vomx-tpeogm_",
            "https://www.rferl.org/api/zqii_l-vomx-tpeigmy",
            "https://www.rferl.org/api/z_iiol-vomx-tpevgmi",
            "https://www.rferl.org/api/ztiiml-vomx-tpekgm_",
            "https://www.rferl.org/api/ztukmrl-vomx-tpeki-mo",
        ],
        "fallback": "https://www.rferl.org/p/5549.html",
        "max_articles": 150,
    },

    {
        "name": "Eurasianet",
        "short_name": "Eurasianet",
        "profile": "independent",
        "label": "Indépendant · régional",
        "type": "html",
        "url": "https://eurasianet.org/latest",
        "max_articles": 120,
    },

    {
        "name": "Cabar.asia",
        "short_name": "CABAR",
        "profile": "independent",
        "label": "Indépendant · Asie centrale",
        "type": "rss",
        "feeds": [
            "https://cabar.asia/en/feed",
        ],
        "fallback": "https://cabar.asia/en/",
        "max_articles": 120,
    },

    {
        "name": "The Diplomat",
        "short_name": "The Diplomat",
        "profile": "international_analysis",
        "label": "International · analyse",
        "type": "html",
        "url": "https://thediplomat.com/regions/central-asia/",
        "max_articles": 120,
    },

    # ========================================================
    # INVESTIGATION / DROITS HUMAINS
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

    {
        "name": "Human Rights Watch",
        "short_name": "HRW",
        "profile": "human_rights",
        "label": "International · droits humains",
        "type": "html",
        "url": "https://www.hrw.org/",
        "max_articles": 100,
    },

    {
        "name": "Amnesty International",
        "short_name": "Amnesty",
        "profile": "human_rights",
        "label": "International · droits humains",
        "type": "html",
        "url": "https://www.amnesty.org/",
        "max_articles": 100,
    },

    {
        "name": "Committee to Protect Journalists",
        "short_name": "CPJ",
        "profile": "human_rights",
        "label": "International · liberté de la presse",
        "type": "html",
        "url": "https://cpj.org/",
        "max_articles": 100,
    },

    {
        "name": "Reporters Without Borders",
        "short_name": "RSF",
        "profile": "human_rights",
        "label": "International · liberté de la presse",
        "type": "html",
        "url": "https://rsf.org/",
        "max_articles": 100,
    },

    # ========================================================
    # MÉDIAS RÉGIONAUX INDÉPENDANTS
    # ========================================================

    {
        "name": "The Times of Central Asia",
        "short_name": "TCA",
        "profile": "regional_independent",
        "label": "Régional · indépendant",
        "type": "html",
        "url": "https://timesca.com/",
        "max_articles": 120,
    },

    {
        "name": "Novastan",
        "short_name": "Novastan",
        "profile": "regional_independent",
        "label": "Régional · indépendant",
        "type": "html",
        "url": "https://novastan.org/en/",
        "max_articles": 120,
    },

    {
        "name": "UzNews24",
        "short_name": "UzNews24",
        "profile": "regional_media",
        "label": "Régional · Ouzbékistan",
        "type": "html",
        "url": "https://uznews.uz/en",
        "max_articles": 120,
    },

    {
        "name": "Sarpa Media",
        "short_name": "Sarpa",
        "profile": "regional_independent",
        "label": "Régional · indépendant",
        "type": "html",
        "url": "https://sarpa.media/",
        "max_articles": 120,
    },

    {
        "name": "Kursiv Media",
        "short_name": "Kursiv",
        "profile": "regional_media",
        "label": "Régional · business & politique",
        "type": "html",
        "url": "https://kz.kursiv.media/en/",
        "max_articles": 120,
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
        "max_articles": 120,
    },

    {
        "name": "Radio Azattyq",
        "short_name": "Azattyq",
        "profile": "international_independent",
        "label": "International · Kazakhstan",
        "type": "html",
        "url": "https://www.azattyq.org/",
        "max_articles": 120,
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
        "max_articles": 120,
    },

    {
        "name": "24.kg",
        "short_name": "24.kg",
        "profile": "regional_media",
        "label": "Régional · Kirghizistan",
        "type": "html",
        "url": "https://24.kg/",
        "max_articles": 120,
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
        "max_articles": 120,
    },

    {
        "name": "Radio Ozodi",
        "short_name": "Ozodi",
        "profile": "international_independent",
        "label": "International · Tadjikistan",
        "type": "html",
        "url": "https://www.ozodi.org/",
        "max_articles": 120,
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
        "max_articles": 120,
    },

    {
        "name": "Kun.uz",
        "short_name": "Kun.uz",
        "profile": "regional_media",
        "label": "Régional · Ouzbékistan",
        "type": "html",
        "url": "https://kun.uz/en",
        "max_articles": 120,
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
        "max_articles": 120,
    },

    {
        "name": "Chronicles of Turkmenistan",
        "short_name": "Chronicles",
        "profile": "human_rights",
        "label": "Indépendant · Turkménistan",
        "type": "html",
        "url": "https://en.hronikatm.com/",
        "max_articles": 120,
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
        "max_articles": 120,
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
            "les libertés fondamentales et/ou la liberté de la presse."
        ),
    },
}
