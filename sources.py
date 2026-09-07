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


SOURCE_PROFILES = {

    "international_independent": {
        "name": "International · indépendant",
        "description": (
            "Média international à couverture "
            "indépendante."
        ),
    },

    "independent": {
        "name": "Indépendant",
        "description": (
            "Média indépendant spécialisé "
            "sur la région."
        ),
    },

    "international_analysis": {
        "name": "International · analyse",
        "description": (
            "Publication internationale orientée "
            "analyse et géopolitique."
        ),
    },

    "regional_independent": {
        "name": "Régional · indépendant",
        "description": (
            "Média régional indépendant."
        ),
    },

    "regional_media": {
        "name": "Média régional",
        "description": (
            "Média régional couvrant notamment "
            "la politique et l'actualité."
        ),
    },
}
