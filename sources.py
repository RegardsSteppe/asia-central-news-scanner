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
        "language": "multi",

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
        "language": "en",

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
        "language": "en",

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
        "name": "Cabar.asia — russe",
        "short_name": "CABAR RU",
        "profile": "independent",
        "label": "Indépendant · Asie centrale · russe",
        "type": "html",
        "language": "ru",

        "url": "https://cabar.asia/ru/",

        "fallbacks": [
            "https://cabar.asia/ru/category/ru",
        ],

        "max_articles": 120,
    },

    {
        "name": "The Diplomat",
        "short_name": "The Diplomat",
        "profile": "international_analysis",
        "label": "International · analyse",
        "type": "html",
        "language": "en",

        "url": "https://thediplomat.com/regions/central-asia/",

        "fallbacks": [
            "https://thediplomat.com/",
        ],

        "max_articles": 100,
    },

    {
        "name": "The Guardian — Asie centrale",
        "short_name": "Guardian",
        "profile": "international_analysis",
        "label": "International · analyse",
        "type": "rss",
        "language": "en",

        "url": "https://www.theguardian.com/world/central-asia",

        "feeds": [
            "https://www.theguardian.com/world/central-asia/rss",
        ],

        "max_articles": 60,
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
        "language": "en",

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
        "language": "en",

        "url": "https://www.hrw.org/asia/",

        "fallbacks": [
            "https://www.hrw.org/asia",
        ],

        "max_articles": 80,
    },

    {
        "name": "Human Rights Watch — français",
        "short_name": "HRW FR",
        "profile": "human_rights",
        "label": "International · droits humains · français",
        "type": "html",
        "language": "fr",

        "url": "https://www.hrw.org/fr/",

        "max_articles": 80,
    },

    {
        "name": "Human Rights Watch — russe",
        "short_name": "HRW RU",
        "profile": "human_rights",
        "label": "International · droits humains · russe",
        "type": "html",
        "language": "ru",

        "url": "https://www.hrw.org/ru/",

        "max_articles": 80,
    },

    {
        "name": "Amnesty International",
        "short_name": "Amnesty",
        "profile": "human_rights",
        "label": "International · droits humains",
        "type": "html",
        "language": "en",

        "url": "https://www.amnesty.org/",

        "max_articles": 80,
    },

    {
        "name": "Amnesty International — français",
        "short_name": "Amnesty FR",
        "profile": "human_rights",
        "label": "International · droits humains · français",
        "type": "html",
        "language": "fr",

        "url": "https://www.amnesty.org/fr/",

        "max_articles": 80,
    },

    {
        "name": "Amnesty International — russe",
        "short_name": "Amnesty RU",
        "profile": "human_rights",
        "label": "International · droits humains · russe",
        "type": "html",
        "language": "ru",

        "url": "https://www.amnesty.org/ru/",

        "max_articles": 80,
    },

    {
        "name": "Committee to Protect Journalists",
        "short_name": "CPJ",
        "profile": "press_freedom",
        "label": "International · liberté de la presse",
        "type": "html",
        "language": "en",

        "url": "https://cpj.org/",

        "max_articles": 80,
    },

    {
        "name": "Committee to Protect Journalists — russe",
        "short_name": "CPJ RU",
        "profile": "press_freedom",
        "label": "International · liberté de la presse · russe",
        "type": "html",
        "language": "ru",

        "url": "https://cpj.org/ru/",

        "max_articles": 80,
    },

    {
        "name": "Reporters Without Borders",
        "short_name": "RSF",
        "profile": "press_freedom",
        "label": "International · liberté de la presse",
        "type": "html",
        "language": "fr",

        "url": "https://rsf.org/fr/",

        "max_articles": 80,
    },

    # ========================================================
    # DROITS HUMAINS — ORGANISATIONS INTERGOUVERNEMENTALES
    #
    # URLs non vérifiables depuis cet environnement (accès réseau
    # sortant bloqué) : à valider via les logs du premier run réel.
    # ========================================================

    {
        "name": "OHCHR",
        "short_name": "OHCHR",
        "profile": "human_rights",
        "label": "International · ONU · droits humains",
        "type": "html",
        "language": "en",

        "url": "https://www.ohchr.org/en/press-releases",

        "max_articles": 80,
    },

    {
        "name": "OSCE",
        "short_name": "OSCE",
        "profile": "human_rights",
        "label": "International · sécurité & droits humains",
        "type": "html",
        "language": "en",

        "url": "https://www.osce.org/news",

        "max_articles": 80,
    },

    {
        "name": "CIVICUS Monitor",
        "short_name": "CIVICUS",
        "profile": "human_rights",
        "label": "International · espace civique",
        "type": "html",
        "language": "en",

        "url": "https://monitor.civicus.org/",

        "max_articles": 60,
    },

    {
        "name": "International Partnership for Human Rights",
        "short_name": "IPHR",
        "profile": "human_rights",
        "label": "International · droits humains",
        "type": "html",
        "language": "en",

        "url": "https://www.iphronline.org/",

        "max_articles": 60,
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
        "language": "en",

        "url": "https://timesca.com/",

        "max_articles": 100,
    },

    # ========================================================
    # NOVASTAN — MULTILINGUE
    # ========================================================

    {
        "name": "Novastan — français",
        "short_name": "Novastan FR",
        "profile": "regional_independent",
        "label": "Régional · indépendant · français",
        "type": "html",
        "language": "fr",

        "url": "https://novastan.org/fr/",

        "max_articles": 100,
    },

    {
        "name": "Novastan — anglais",
        "short_name": "Novastan EN",
        "profile": "regional_independent",
        "label": "Régional · indépendant · anglais",
        "type": "html",
        "language": "en",

        "url": "https://novastan.org/en/",

        "max_articles": 100,
    },

    {
        "name": "Novastan — allemand",
        "short_name": "Novastan DE",
        "profile": "regional_independent",
        "label": "Régional · indépendant · allemand",
        "type": "html",
        "language": "de",

        "url": "https://novastan.org/de/",

        "max_articles": 100,
    },

    {
        "name": "UzNews24",
        "short_name": "UzNews24",
        "profile": "regional_media",
        "label": "Régional · Ouzbékistan",
        "type": "html",
        "language": "en",

        "url": "https://uznews.uz/en",

        "max_articles": 100,
    },

    {
        "name": "Sarpa Media",
        "short_name": "Sarpa",
        "profile": "regional_independent",
        "label": "Régional · indépendant",
        "type": "html",
        "language": "multi",

        "url": "https://sarpa.media/",

        "max_articles": 100,
    },

    {
        "name": "Kursiv Media",
        "short_name": "Kursiv",
        "profile": "regional_media",
        "label": "Régional · business & politique",
        "type": "html",
        "language": "en",

        "url": "https://kz.kursiv.media/en/",

        "max_articles": 100,
    },

    # ========================================================
    # KAZAKHSTAN
    # ========================================================

    {
        "name": "Vlast — russe",
        "short_name": "Vlast RU",
        "profile": "regional_independent",
        "label": "Régional · Kazakhstan · russe",
        "type": "html",
        "language": "ru",

        "url": "https://vlast.kz/",

        "max_articles": 100,
    },

    {
        "name": "Vlast — anglais",
        "short_name": "Vlast EN",
        "profile": "regional_independent",
        "label": "Régional · Kazakhstan · anglais",
        "type": "html",
        "language": "en",

        "url": "https://vlast.kz/english/",

        "max_articles": 100,
    },

    {
        "name": "Radio Azattyq",
        "short_name": "Azattyq",
        "profile": "international_independent",
        "label": "International · Kazakhstan",
        "type": "html",
        "language": "kk",

        "url": "https://www.azattyq.org/",

        "max_articles": 100,
    },

    {
        "name": "Orda.kz — russe",
        "short_name": "Orda RU",
        "profile": "regional_independent",
        "label": "Indépendant · Kazakhstan · russe",
        "type": "html",
        "language": "ru",

        "url": "https://orda.kz/",

        "max_articles": 100,
    },

    {
        "name": "Orda.kz — anglais",
        "short_name": "Orda EN",
        "profile": "regional_independent",
        "label": "Indépendant · Kazakhstan · anglais",
        "type": "html",
        "language": "en",

        "url": "https://en.orda.kz/",

        "max_articles": 100,
    },

    {
        "name": "Tengrinews",
        "short_name": "Tengrinews",
        "profile": "regional_media",
        "label": "Média régional · Kazakhstan",
        "type": "html",
        "language": "en",

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
        "language": "ru",

        "url": "https://kloop.kg/",

        "max_articles": 100,
    },

    {
        "name": "24.kg — russe",
        "short_name": "24kg RU",
        "profile": "regional_media",
        "label": "Régional · Kirghizistan · russe",
        "type": "html",
        "language": "ru",

        "url": "https://24.kg/",

        "max_articles": 100,
    },

    {
        "name": "24.kg — anglais",
        "short_name": "24kg EN",
        "profile": "regional_media",
        "label": "Régional · Kirghizistan · anglais",
        "type": "html",
        "language": "en",

        "url": "https://24.kg/english/",

        "max_articles": 100,
    },

    {
        "name": "Kaktus Media",
        "short_name": "Kaktus",
        "profile": "regional_independent",
        "label": "Indépendant · Kirghizistan",
        "type": "html",
        "language": "ru",

        "url": "https://kaktus.media/",

        "max_articles": 100,
    },

    {
        "name": "Kabar",
        "short_name": "Kabar",
        "profile": "state_media",
        "label": "Agence officielle · Kirghizistan",
        "type": "html",
        "language": "en",

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
        "language": "en",

        "url": "https://asiaplustj.info/en",

        "max_articles": 100,
    },

    {
        "name": "Radio Ozodi",
        "short_name": "Ozodi",
        "profile": "international_independent",
        "label": "International · Tadjikistan",
        "type": "html",
        "language": "tg",

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
        "language": "en",

        "url": "https://www.gazeta.uz/en/",

        "max_articles": 100,
    },

    {
        "name": "Kun.uz",
        "short_name": "Kun.uz",
        "profile": "regional_media",
        "label": "Régional · Ouzbékistan",
        "type": "html",
        "language": "en",

        "url": "https://kun.uz/en",

        "max_articles": 100,
    },

    {
        "name": "Spot.uz",
        "short_name": "Spot.uz",
        "profile": "economic_media",
        "label": "Économie · Ouzbékistan",
        "type": "html",
        "language": "en",

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
        "language": "ru",

        "url": "https://turkmen.news/",

        "max_articles": 100,
    },

    {
        "name": "Chronicles of Turkmenistan",
        "short_name": "Chronicles",
        "profile": "human_rights",
        "label": "Indépendant · Turkménistan",
        "type": "html",
        "language": "ru",

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
        "language": "en",

        "url": "https://fergana.agency/",

        "max_articles": 100,
    },

    {
        "name": "Central Asia-Caucasus Analyst",
        "short_name": "CAC Analyst",
        "profile": "regional_analysis",
        "label": "Régional · analyse",
        "type": "html",
        "language": "en",

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
        "language": "en",

        "url": "https://www.azernews.az/latest/",

        "max_articles": 80,
    },

    {
        "name": "Trend News Agency",
        "short_name": "Trend",
        "profile": "regional_media",
        "label": "Régional · Caucase",
        "type": "html",
        "language": "en",

        "url": "https://en.trend.az/",

        "max_articles": 80,
    },

    # ========================================================
    # SÉCURITÉ RÉGIONALE
    #
    # Think tanks et centres de recherche généralistes (pas
    # spécifiques Asie centrale) : volontairement absents de
    # central_asia_source_terms dans scoring.py. Leur pertinence
    # géographique est jugée uniquement par les mots-clés détectés
    # dans le titre/corps de chaque article, jamais par la source —
    # pour éviter qu'un article sur un tout autre sujet/région
    # n'hérite d'un laissez-passer géographique juste parce qu'il
    # vient de ce think tank (cf. le cas RFE/RL).
    #
    # URLs non vérifiables depuis cet environnement (accès réseau
    # sortant bloqué) : à valider via les logs du premier run réel.
    # ========================================================

    {
        "name": "Hudson Institute",
        "short_name": "Hudson",
        "profile": "security_analysis",
        "label": "International · sécurité",
        "type": "html",
        "language": "en",

        "url": "https://www.hudson.org/",

        "max_articles": 80,
    },

    {
        "name": "Jamestown Foundation",
        "short_name": "Jamestown",
        "profile": "security_analysis",
        "label": "International · sécurité · Eurasie",
        "type": "html",
        "language": "en",

        "url": "https://jamestown.org/",

        "max_articles": 80,
    },

    {
        "name": "International Crisis Group",
        "short_name": "Crisis Group",
        "profile": "security_analysis",
        "label": "International · prévention des conflits",
        "type": "html",
        "language": "en",

        "url": "https://www.crisisgroup.org/",

        "max_articles": 80,
    },

    {
        "name": "Carnegie Endowment for International Peace",
        "short_name": "Carnegie",
        "profile": "security_analysis",
        "label": "International · analyse géopolitique",
        "type": "html",
        "language": "en",

        "url": "https://carnegieendowment.org/",

        "max_articles": 80,
    },

    {
        "name": "Chatham House",
        "short_name": "Chatham House",
        "profile": "security_analysis",
        "label": "International · Russie & Eurasie",
        "type": "html",
        "language": "en",

        "url": "https://www.chathamhouse.org/",

        "max_articles": 80,
    },

    {
        "name": "RAND Corporation",
        "short_name": "RAND",
        "profile": "security_analysis",
        "label": "International · recherche sécurité",
        "type": "html",
        "language": "en",

        "url": "https://www.rand.org/",

        "max_articles": 80,
    },

    {
        "name": "Atlantic Council",
        "short_name": "Atlantic Council",
        "profile": "security_analysis",
        "label": "International · Eurasie",
        "type": "html",
        "language": "en",

        "url": "https://www.atlanticcouncil.org/",

        "max_articles": 80,
    },

    {
        "name": "CSIS",
        "short_name": "CSIS",
        "profile": "security_analysis",
        "label": "International · sécurité & stratégie",
        "type": "html",
        "language": "en",

        "url": "https://www.csis.org/",

        "max_articles": 80,
    },

    {
        "name": "Foreign Policy Research Institute",
        "short_name": "FPRI",
        "profile": "security_analysis",
        "label": "International · Eurasie",
        "type": "html",
        "language": "en",

        "url": "https://www.fpri.org/",

        "max_articles": 80,
    },

    {
        "name": "Stimson Center",
        "short_name": "Stimson",
        "profile": "security_analysis",
        "label": "International · sécurité",
        "type": "html",
        "language": "en",

        "url": "https://www.stimson.org/",

        "max_articles": 80,
    },

    {
        "name": "George C. Marshall European Center for Security Studies",
        "short_name": "Marshall Center",
        "profile": "security_analysis",
        "label": "International · études de sécurité",
        "type": "html",
        "language": "en",

        "url": "https://www.marshallcenter.org/",

        "max_articles": 80,
    },

    {
        "name": "PONARS Eurasia",
        "short_name": "PONARS",
        "profile": "security_analysis",
        "label": "International · post-soviétique",
        "type": "html",
        "language": "en",

        "url": "https://www.ponarseurasia.org/",

        "max_articles": 80,
    },

    {
        "name": "SpecialEurasia",
        "short_name": "SpecialEurasia",
        "profile": "security_analysis",
        "label": "International · Asie centrale & Caucase",
        "type": "html",
        "language": "en",

        "url": "https://www.specialeurasia.com/",

        "max_articles": 60,
    },

    {
        "name": "Caspian Policy Center",
        "short_name": "CPC",
        "profile": "security_analysis",
        "label": "International · Caspienne",
        "type": "html",
        "language": "en",

        "url": "https://www.caspianpolicy.org/",

        "max_articles": 60,
    },

    # ========================================================
    # MÉDIAS OFFICIELS — RUSSIE & CHINE
    #
    # Ajoutés à la demande explicite : voir le narratif officiel russe
    # et chinois sur l'Asie centrale comme point de comparaison face
    # aux sources indépendantes/militantes du reste de la liste — pas
    # pour leur fiabilité factuelle. profile="state_media" (déjà
    # utilisé pour Kabar, l'agence officielle kirghize) : ni exclues
    # du scoring, ni boostées, jugées comme toute autre source
    # uniquement sur le contenu de chaque article.
    #
    # URLs non vérifiables depuis cet environnement (accès réseau
    # sortant bloqué) : à valider via les logs du premier run réel.
    # ========================================================

    {
        "name": "TASS",
        "short_name": "TASS",
        "profile": "state_media",
        "label": "Média officiel · agence de presse russe",
        "type": "html",
        "language": "en",

        "url": "https://tass.com/",

        "max_articles": 80,
    },

    {
        "name": "RIA Novosti",
        "short_name": "RIA Novosti",
        "profile": "state_media",
        "label": "Média officiel · agence de presse russe",
        "type": "html",
        "language": "ru",

        "url": "https://ria.ru/",

        "max_articles": 80,
    },

    {
        "name": "Sputnik",
        "short_name": "Sputnik",
        "profile": "state_media",
        "label": "Média officiel · propagande internationale russe",
        "type": "html",
        "language": "en",

        "url": "https://sputniknews.com/",

        "max_articles": 80,
    },

    {
        "name": "Regnum",
        "short_name": "Regnum",
        "profile": "state_media",
        "label": "Média officiel · espace post-soviétique",
        "type": "html",
        "language": "ru",

        "url": "https://regnum.ru/",

        "max_articles": 80,
    },

    {
        "name": "Rossiyskaya Gazeta Beyond (RBTH)",
        "short_name": "RBTH",
        "profile": "state_media",
        "label": "Média officiel · diplomatie publique russe",
        "type": "html",
        "language": "en",

        "url": "https://www.rbth.com/",

        "max_articles": 60,
    },

    {
        "name": "Nezavisimaya Gazeta",
        "short_name": "NG.ru",
        "profile": "state_media",
        "label": "Média proche du pouvoir · russe",
        "type": "html",
        "language": "ru",

        "url": "https://www.ng.ru/",

        "max_articles": 60,
    },

    {
        "name": "Kommersant",
        "short_name": "Kommersant",
        "profile": "state_media",
        "label": "Média proche du pouvoir · russe",
        "type": "html",
        "language": "ru",

        "url": "https://www.kommersant.ru/",

        "max_articles": 60,
    },

    {
        "name": "Vedomosti",
        "short_name": "Vedomosti",
        "profile": "state_media",
        "label": "Média proche du pouvoir · russe",
        "type": "html",
        "language": "ru",

        "url": "https://www.vedomosti.ru/",

        "max_articles": 60,
    },

    {
        "name": "Kremlin.ru",
        "short_name": "Kremlin",
        "profile": "state_media",
        "label": "Média officiel · présidence russe",
        "type": "html",
        "language": "ru",

        "url": "http://kremlin.ru/",

        "max_articles": 60,
    },

    {
        "name": "Gouvernement russe",
        "short_name": "Government.ru",
        "profile": "state_media",
        "label": "Média officiel · gouvernement russe",
        "type": "html",
        "language": "ru",

        "url": "http://government.ru/",

        "max_articles": 60,
    },

    {
        "name": "Ministère russe des Affaires étrangères",
        "short_name": "MID.ru",
        "profile": "state_media",
        "label": "Média officiel · diplomatie russe",
        "type": "html",
        "language": "ru",

        "url": "https://www.mid.ru/",

        "max_articles": 60,
    },

    {
        "name": "Mission russe à l'ONU",
        "short_name": "Russia UN",
        "profile": "state_media",
        "label": "Média officiel · diplomatie russe",
        "type": "html",
        "language": "en",

        "url": "https://russiaun.ru/",

        "max_articles": 40,
    },

    {
        "name": "Xinhua",
        "short_name": "Xinhua",
        "profile": "state_media",
        "label": "Média officiel · agence de presse chinoise",
        "type": "html",
        "language": "en",

        "url": "https://english.news.cn/",

        "max_articles": 80,
    },

    {
        "name": "China Daily",
        "short_name": "China Daily",
        "profile": "state_media",
        "label": "Média officiel · presse chinoise",
        "type": "html",
        "language": "en",

        "url": "https://www.chinadaily.com.cn/",

        "max_articles": 80,
    },

    {
        "name": "CGTN",
        "short_name": "CGTN",
        "profile": "state_media",
        "label": "Média officiel · diffuseur chinois international",
        "type": "html",
        "language": "en",

        "url": "https://news.cgtn.com/",

        "max_articles": 80,
    },

    {
        "name": "Ministère chinois des Affaires étrangères",
        "short_name": "MFA Chine",
        "profile": "state_media",
        "label": "Média officiel · diplomatie chinoise",
        "type": "html",
        "language": "en",

        "url": "https://www.fmprc.gov.cn/eng/",

        "max_articles": 60,
    },

    {
        "name": "China Diplomacy",
        "short_name": "China Diplomacy",
        "profile": "state_media",
        "label": "Média officiel · diplomatie chinoise",
        "type": "html",
        "language": "en",

        "url": "https://www.chinadiplomacy.org.cn/",

        "max_articles": 60,
    },

    {
        "name": "NDRC (Chine)",
        "short_name": "NDRC",
        "profile": "state_media",
        "label": "Média officiel · politique économique chinoise",
        "type": "html",
        "language": "en",

        "url": "https://en.ndrc.gov.cn/",

        "max_articles": 40,
    },

    {
        "name": "CIDCA (Chine)",
        "short_name": "CIDCA",
        "profile": "state_media",
        "label": "Média officiel · aide au développement chinoise",
        "type": "html",
        "language": "en",

        "url": "https://en.cidca.gov.cn/",

        "max_articles": 40,
    },

    # ========================================================
    # RECHERCHE ACADÉMIQUE
    #
    # Confiance plus faible que le reste de sources.py : URL non
    # vérifiée (déduite de l'ISSN de la revue), plateforme éditeur
    # (Wiley) potentiellement à rendu JS et articles majoritairement
    # payants (seuls titre/résumé seront visibles). À confirmer/
    # corriger via les logs du premier run réel.
    # ========================================================

    {
        "name": "Swiss Political Science Review",
        "short_name": "SPSR",
        "profile": "academic_research",
        "label": "Recherche académique · science politique",
        "type": "html",
        "language": "en",

        "url": "https://onlinelibrary.wiley.com/journal/16626370",

        "max_articles": 60,
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

    "security_analysis": {
        "name": "Sécurité · analyse",
        "description": (
            "Think tank ou centre de recherche généraliste sur la "
            "sécurité, la géopolitique et les conflits — non "
            "spécifique à l'Asie centrale. Sa pertinence géographique "
            "est jugée uniquement sur le contenu de chaque article."
        ),
    },

    "academic_research": {
        "name": "Recherche académique",
        "description": (
            "Revue scientifique publiant occasionnellement des "
            "articles de recherche sur l'Asie centrale (sociologie, "
            "science politique, surveillance numérique...). Contenu "
            "généraliste, pertinence jugée au cas par cas."
        ),
    },
}
