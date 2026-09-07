# sources.py

SOURCES = [

    {
        "name": "Eurasianet",
        "type": "html",
        "url": "https://eurasianet.org/latest",
        "max_articles": 100,
    },

    {
        "name": "Cabar.asia",
        "type": "rss",
        "feeds": [
            "https://cabar.asia/en/feed",
        ],
        "fallback": "https://cabar.asia/en/",
        "max_articles": 100,
    },

    {
        "name": "Radio Free Europe / Radio Liberty",
        "type": "rss",
        "feeds": [
            # Kazakhstan
            "https://www.rferl.org/api/zriiml-vomx-tpeogm_",

            # Kyrgyzstan
            "https://www.rferl.org/api/zqii_l-vomx-tpeigmy",

            # Tajikistan
            "https://www.rferl.org/api/z_iiol-vomx-tpevgmi",

            # Turkmenistan
            "https://www.rferl.org/api/ztiiml-vomx-tpekgm_",

            # Uzbekistan
            "https://www.rferl.org/api/ztukmrl-vomx-tpeki-mo",
        ],
        "fallback": "https://www.rferl.org/p/5549.html",
        "max_articles": 150,
    },

    {
        "name": "Azernews",
        "type": "html",
        "url": "https://www.azernews.az/latest/",
        "max_articles": 100,
    },

    {
        "name": "The Diplomat",
        "type": "html",
        "url": "https://thediplomat.com/regions/central-asia/",
        "max_articles": 100,
    },

    {
        "name": "Kursiv Media",
        "type": "html",
        "url": "https://kz.kursiv.media/en/",
        "max_articles": 100,
    },

    {
        "name": "The Times of Central Asia",
        "type": "html",
        "url": "https://timesca.com/",
        "max_articles": 100,
    },

    {
        "name": "Novastan",
        "type": "html",
        "url": "https://novastan.org/en/",
        "max_articles": 100,
    },

    {
        "name": "UzNews24",
        "type": "html",
        "url": "https://uznews.uz/en",
        "max_articles": 100,
    },

    {
        "name": "Sarpa Media",
        "type": "html",
        "url": "https://sarpa.media/",
        "max_articles": 100,
    },
]
