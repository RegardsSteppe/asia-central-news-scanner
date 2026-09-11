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

        "max_articles": 400,
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

        "max_articles": 300,
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

        "max_articles": 300,
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

        "max_articles": 300,
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

        "max_articles": 250,
    },

    # ========================================================
    # PRESSE INTERNATIONALE — PAR PAYS
    #
    # Aucun des trois (Guardian, AP, Al Jazeera) n'a de section "Asie
    # centrale" regroupée : le tag "/world/central-asia" supposé du
    # Guardian n'existe pas (404 confirmé sur un run réel) — seuls des
    # tags par pays existent chez les trois. Une entrée par pays plutôt
    # que le flux généraliste complet, pour éviter de diluer le scan
    # avec l'actualité mondiale hors-sujet.
    #
    # AP (les 5 entrées ci-dessous) renvoie 403 sur un run réel —
    # bloqué probablement par une protection anti-bot (comme HRW /
    # Crisis Group / IPHR ailleurs dans ce fichier). Conservé quand
    # même comme les autres sources bloquées : la géo-restriction ou
    # le blocage peut changer sans que l'URL change.
    #
    # URLs non vérifiables depuis cet environnement (accès réseau
    # sortant bloqué) : à valider via les logs du premier run réel.
    # ========================================================

    {
        "name": "The Guardian — Kazakhstan",
        "short_name": "Guardian Kazakhstan",
        "profile": "international_analysis",
        "label": "International · Kazakhstan",
        "type": "html",
        "language": "en",

        "url": "https://www.theguardian.com/world/kazakhstan",

        "max_articles": 100,
    },

    {
        "name": "The Guardian — Uzbekistan",
        "short_name": "Guardian Uzbekistan",
        "profile": "international_analysis",
        "label": "International · Ouzbékistan",
        "type": "html",
        "language": "en",

        "url": "https://www.theguardian.com/world/uzbekistan",

        "max_articles": 100,
    },

    {
        "name": "The Guardian — Kyrgyzstan",
        "short_name": "Guardian Kyrgyzstan",
        "profile": "international_analysis",
        "label": "International · Kirghizistan",
        "type": "html",
        "language": "en",

        "url": "https://www.theguardian.com/world/kyrgyzstan",

        "max_articles": 100,
    },

    {
        "name": "The Guardian — Tajikistan",
        "short_name": "Guardian Tajikistan",
        "profile": "international_analysis",
        "label": "International · Tadjikistan",
        "type": "html",
        "language": "en",

        "url": "https://www.theguardian.com/world/tajikistan",

        "max_articles": 100,
    },

    {
        "name": "The Guardian — Turkmenistan",
        "short_name": "Guardian Turkmenistan",
        "profile": "international_analysis",
        "label": "International · Turkménistan",
        "type": "html",
        "language": "en",

        "url": "https://www.theguardian.com/world/turkmenistan",

        "max_articles": 100,
    },

    {
        "name": "AP News — Kazakhstan",
        "short_name": "AP Kazakhstan",
        "profile": "international_independent",
        "label": "International · Kazakhstan",
        "type": "html",
        "language": "en",

        "url": "https://apnews.com/hub/kazakhstan",

        "max_articles": 100,
    },

    {
        "name": "AP News — Uzbekistan",
        "short_name": "AP Uzbekistan",
        "profile": "international_independent",
        "label": "International · Ouzbékistan",
        "type": "html",
        "language": "en",

        "url": "https://apnews.com/hub/uzbekistan",

        "max_articles": 100,
    },

    {
        "name": "AP News — Kyrgyzstan",
        "short_name": "AP Kyrgyzstan",
        "profile": "international_independent",
        "label": "International · Kirghizistan",
        "type": "html",
        "language": "en",

        "url": "https://apnews.com/hub/kyrgyzstan",

        "max_articles": 100,
    },

    {
        "name": "AP News — Tajikistan",
        "short_name": "AP Tajikistan",
        "profile": "international_independent",
        "label": "International · Tadjikistan",
        "type": "html",
        "language": "en",

        "url": "https://apnews.com/hub/tajikistan",

        "max_articles": 100,
    },

    {
        "name": "AP News — Turkmenistan",
        "short_name": "AP Turkmenistan",
        "profile": "international_independent",
        "label": "International · Turkménistan",
        "type": "html",
        "language": "en",

        "url": "https://apnews.com/hub/turkmenistan",

        "max_articles": 100,
    },

    {
        "name": "Al Jazeera — Kazakhstan",
        "short_name": "AJ Kazakhstan",
        "profile": "international_independent",
        "label": "International · Kazakhstan",
        "type": "html",
        "language": "en",

        "url": "https://www.aljazeera.com/where/kazakhstan/",

        "max_articles": 100,
    },

    {
        "name": "Al Jazeera — Uzbekistan",
        "short_name": "AJ Uzbekistan",
        "profile": "international_independent",
        "label": "International · Ouzbékistan",
        "type": "html",
        "language": "en",

        "url": "https://www.aljazeera.com/where/uzbekistan/",

        "max_articles": 100,
    },

    {
        "name": "Al Jazeera — Kyrgyzstan",
        "short_name": "AJ Kyrgyzstan",
        "profile": "international_independent",
        "label": "International · Kirghizistan",
        "type": "html",
        "language": "en",

        "url": "https://www.aljazeera.com/where/kyrgyzstan/",

        "max_articles": 100,
    },

    {
        "name": "Al Jazeera — Tajikistan",
        "short_name": "AJ Tajikistan",
        "profile": "international_independent",
        "label": "International · Tadjikistan",
        "type": "html",
        "language": "en",

        "url": "https://www.aljazeera.com/where/tajikistan/",

        "max_articles": 100,
    },

    {
        "name": "Al Jazeera — Turkmenistan",
        "short_name": "AJ Turkmenistan",
        "profile": "international_independent",
        "label": "International · Turkménistan",
        "type": "html",
        "language": "en",

        "url": "https://www.aljazeera.com/where/turkmenistan/",

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
        "language": "en",

        "url": "https://www.occrp.org/en/",

        "max_articles": 250,
    },

    {
        # Trouvé via find_candidate_sources.py : cité par un article
        # Novastan de niveau A sur les manifestations de Noukous.
        "name": "The New Humanitarian",
        "short_name": "New Humanitarian",
        "profile": "investigative",
        "label": "International · journalisme humanitaire",
        "type": "html",
        "language": "en",

        "url": "https://www.thenewhumanitarian.org/",

        "max_articles": 200,
    },

    # ========================================================
    # DROITS HUMAINS
    # ========================================================

    {
        # hrw.org/asia/ (comme /fr/, /ru/) est bloqué en 403 depuis le
        # tout début du projet — blocage anti-bot côté serveur. HRW a
        # cependant un flux RSS public (hrw.org/rss/news), souvent
        # exempté de ce type de protection (pas de défi JS pour un
        # lecteur RSS) : testé à la demande de l'utilisateur après
        # qu'un article HRW manquant lui ait été signalé. Fallback sur
        # l'ancienne page HTML si le flux échoue aussi — non vérifié
        # depuis cet environnement, à valider via les logs du run réel.
        # hrw.org bloque en 403 TOUTES les URLs testées depuis cet
        # environnement — page HTML et flux RSS propre inclus — signe
        # d'un blocage au niveau du domaine/IP (probablement les
        # plages d'IP des runners GitHub Actions), pas d'un chemin en
        # particulier. Contournement : Google News agrège hrw.org sur
        # son propre domaine (news.google.com), jamais bloqué par HRW.
        # Google ajoute systématiquement " - Human Rights Watch" à la
        # fin de chaque titre : nettoyé automatiquement dans
        # parse_rss() pour les flux news.google.com uniquement.
        # Non vérifié depuis cet environnement (accès réseau sortant
        # bloqué) : à valider via les logs du run réel.
        "name": "Human Rights Watch",
        "short_name": "HRW",
        "profile": "human_rights",
        "label": "International · droits humains",
        "type": "rss",
        "language": "en",

        "url": "https://www.hrw.org/asia/",

        "feeds": [
            "https://www.hrw.org/rss/news",
            "https://news.google.com/rss/search?q=site:hrw.org&hl=en-US&gl=US&ceid=US:en",
            # Le flux Google News générique (ci-dessus) est classé par
            # pertinence mondiale et laisse passer à la trappe les
            # articles spécifiques à l'Asie centrale/Caucase (ex :
            # l'article sur Anar Mammadli en Azerbaïdjan, absent des
            # 100 premiers résultats "site:hrw.org"). Requête
            # supplémentaire ciblée sur les pays de la région.
            "https://news.google.com/rss/search?q=site%3Ahrw.org%20%28Azerbaijan%20OR%20Armenia%20OR%20Georgia%20OR%20Kazakhstan%20OR%20Kyrgyzstan%20OR%20Tajikistan%20OR%20Turkmenistan%20OR%20Uzbekistan%29&hl=en-US&gl=US&ceid=US:en",
        ],

        "fallbacks": [
            "https://www.hrw.org/asia",
        ],

        "max_articles": 200,
    },

    {
        "name": "Human Rights Watch — français",
        "short_name": "HRW FR",
        "profile": "human_rights",
        "label": "International · droits humains · français",
        "type": "rss",
        "language": "fr",

        "url": "https://www.hrw.org/fr/",

        "feeds": [
            "https://www.hrw.org/fr/rss/news",
            "https://news.google.com/rss/search?q=site:hrw.org/fr&hl=fr&gl=FR&ceid=FR:fr",
            "https://news.google.com/rss/search?q=site%3Ahrw.org%2Ffr%20%28Azerba%C3%AFdjan%20OR%20Arm%C3%A9nie%20OR%20G%C3%A9orgie%20OR%20Kazakhstan%20OR%20Kirghizistan%20OR%20Tadjikistan%20OR%20Turkm%C3%A9nistan%20OR%20Ouzb%C3%A9kistan%29&hl=fr&gl=FR&ceid=FR:fr",
        ],

        "fallbacks": [
            "https://www.hrw.org/fr/",
        ],

        "max_articles": 200,
    },

    {
        "name": "Human Rights Watch — russe",
        "short_name": "HRW RU",
        "profile": "human_rights",
        "label": "International · droits humains · russe",
        "type": "rss",
        "language": "ru",

        "url": "https://www.hrw.org/ru/",

        "feeds": [
            "https://www.hrw.org/ru/rss/news",
            "https://news.google.com/rss/search?q=site:hrw.org/ru&hl=ru&gl=RU&ceid=RU:ru",
            "https://news.google.com/rss/search?q=site%3Ahrw.org%2Fru%20%28%D0%90%D0%B7%D0%B5%D1%80%D0%B1%D0%B0%D0%B9%D0%B4%D0%B6%D0%B0%D0%BD%20OR%20%D0%90%D1%80%D0%BC%D0%B5%D0%BD%D0%B8%D1%8F%20OR%20%D0%93%D1%80%D1%83%D0%B7%D0%B8%D1%8F%20OR%20%D0%9A%D0%B0%D0%B7%D0%B0%D1%85%D1%81%D1%82%D0%B0%D0%BD%20OR%20%D0%9A%D0%B8%D1%80%D0%B3%D0%B8%D0%B7%D0%B8%D1%8F%20OR%20%D0%A2%D0%B0%D0%B4%D0%B6%D0%B8%D0%BA%D0%B8%D1%81%D1%82%D0%B0%D0%BD%20OR%20%D0%A2%D1%83%D1%80%D0%BA%D0%BC%D0%B5%D0%BD%D0%B8%D1%81%D1%82%D0%B0%D0%BD%20OR%20%D0%A3%D0%B7%D0%B1%D0%B5%D0%BA%D0%B8%D1%81%D1%82%D0%B0%D0%BD%29&hl=ru&gl=RU&ceid=RU:ru",
        ],

        "fallbacks": [
            "https://www.hrw.org/ru/",
        ],

        "max_articles": 200,
    },

    {
        "name": "Amnesty International",
        "short_name": "Amnesty",
        "profile": "human_rights",
        "label": "International · droits humains",
        "type": "html",
        "language": "en",

        "url": "https://www.amnesty.org/",

        "max_articles": 200,
    },

    {
        "name": "Amnesty International — français",
        "short_name": "Amnesty FR",
        "profile": "human_rights",
        "label": "International · droits humains · français",
        "type": "html",
        "language": "fr",

        "url": "https://www.amnesty.org/fr/",

        "max_articles": 200,
    },

    {
        "name": "Amnesty International — russe",
        "short_name": "Amnesty RU",
        "profile": "human_rights",
        "label": "International · droits humains · russe",
        "type": "html",
        "language": "ru",

        "url": "https://www.amnesty.org/ru/",

        "max_articles": 200,
    },

    {
        "name": "Committee to Protect Journalists",
        "short_name": "CPJ",
        "profile": "press_freedom",
        "label": "International · liberté de la presse",
        "type": "html",
        "language": "en",

        "url": "https://cpj.org/",

        "max_articles": 200,
    },

    {
        "name": "Committee to Protect Journalists — russe",
        "short_name": "CPJ RU",
        "profile": "press_freedom",
        "label": "International · liberté de la presse · russe",
        "type": "html",
        "language": "ru",

        "url": "https://cpj.org/ru/",

        "max_articles": 200,
    },

    {
        "name": "Reporters Without Borders",
        "short_name": "RSF",
        "profile": "press_freedom",
        "label": "International · liberté de la presse",
        "type": "html",
        "language": "fr",

        "url": "https://rsf.org/fr/",

        "max_articles": 200,
    },

    {
        # Trouvé par recherche web : ONG liberté d'expression, publie
        # régulièrement des rapports pays sur l'Asie centrale
        # (numérique, médias, assemblée).
        # "/resources/" 404 sur un run réel — remplacé par la racine
        # (même pattern que Hudson/Jamestown/etc. et la leçon FIDH
        # ci-dessus : partir d'une page-liste profonde risque des
        # liens relatifs mal résolus).
        "name": "ARTICLE 19",
        "short_name": "ARTICLE 19",
        "profile": "press_freedom",
        "label": "International · liberté d'expression",
        "type": "html",
        "language": "en",

        "url": "https://www.article19.org/",

        "max_articles": 150,
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

        # "/en/press-releases" 404 sur un run réel — remplacé par la
        # racine du site (même pattern que Hudson/Jamestown/etc. :
        # découverte générique des liens d'articles).
        "url": "https://www.ohchr.org/en",

        "max_articles": 200,
    },

    {
        # Trouvé via find_candidate_sources.py : cité par un article
        # RFE/RL de niveau A sur un procès secret au Xinjiang. Sous-
        # domaine distinct d'ohchr.org (qui, lui, est bloqué en 403) —
        # à voir s'il répond différemment.
        "name": "OHCHR — Rapporteurs spéciaux",
        "short_name": "OHCHR Special Procedures",
        "profile": "human_rights",
        "label": "International · ONU · droits humains",
        "type": "html",
        "language": "en",

        "url": "https://spcommreports.ohchr.org/",

        "max_articles": 150,
    },

    {
        # Trouvé via find_candidate_sources.py : cité par un article
        # Novastan de niveau A sur les violences conjugales en Ouzbékistan.
        "name": "UN Women — Europe & Asie centrale",
        "short_name": "UN Women ECA",
        "profile": "human_rights",
        "label": "International · ONU · droits des femmes",
        "type": "html",
        "language": "en",

        "url": "https://eca.unwomen.org/en",

        "max_articles": 150,
    },

    {
        # Trouvé via find_candidate_sources.py : cité par un article
        # RFE/RL de niveau A sur le Xinjiang.
        "name": "Parlement européen",
        "short_name": "Europarl",
        "profile": "human_rights",
        "label": "International · UE · droits humains",
        "type": "html",
        "language": "en",

        "url": "https://www.europarl.europa.eu/news/en",

        "max_articles": 150,
    },

    {
        "name": "OSCE",
        "short_name": "OSCE",
        "profile": "human_rights",
        "label": "International · sécurité & droits humains",
        "type": "html",
        "language": "en",

        "url": "https://www.osce.org/news",

        "max_articles": 200,
    },

    {
        "name": "CIVICUS Monitor",
        "short_name": "CIVICUS",
        "profile": "human_rights",
        "label": "International · espace civique",
        "type": "html",
        "language": "en",

        "url": "https://monitor.civicus.org/",

        "max_articles": 150,
    },

    {
        "name": "International Partnership for Human Rights",
        "short_name": "IPHR",
        "profile": "human_rights",
        "label": "International · droits humains",
        "type": "html",
        "language": "en",

        "url": "https://www.iphronline.org/",

        "max_articles": 150,
    },

    {
        # Trouvé par recherche web (à la demande de l'utilisateur) :
        # fédération internationale de ligues de droits humains,
        # publie régulièrement sur l'Asie centrale et le Caucase.
        #
        # URL volontairement à la racine du site, pas sur la page
        # "/en/region/europe-central-asia/" : un run réel a montré que
        # cette page-liste génère des liens relatifs sans "/" en tête
        # (ex. href="en/region/europe-central-asia/azerbaijan/...") —
        # combinés à une URL de base qui a déjà ce même chemin, ça
        # produit une URL dupliquée et cassée
        # (.../europe-central-asia/en/region/europe-central-asia/...,
        # 403 à l'enrichissement). Partir de la racine évite la
        # collision ; la pertinence géographique reste jugée sur le
        # contenu de chaque article, pas sur cette page de filtre.
        "name": "FIDH",
        "short_name": "FIDH",
        "profile": "human_rights",
        "label": "International · droits humains",
        "type": "html",
        "language": "en",

        "url": "https://www.fidh.org/en/",

        "max_articles": 150,
    },

    {
        # Trouvé par recherche web. Organisation historique de défense
        # des droits humains et des libertés civiles.
        "name": "Freedom House",
        "short_name": "Freedom House",
        "profile": "human_rights",
        "label": "International · droits humains & démocratie",
        "type": "html",
        "language": "en",

        "url": "https://freedomhouse.org/",

        "max_articles": 150,
    },

    {
        # Trouvé par recherche web : ONG spécialisée sur les droits des
        # minorités et personnes LGBT en Asie centrale/ex-URSS —
        # exactement le type de signal faible qu'un thème générique
        # "LGBT rights" ne suffit pas à faire remonter.
        "name": "ADC Memorial",
        "short_name": "ADC Memorial",
        "profile": "human_rights",
        "label": "International · minorités & LGBT",
        "type": "html",
        "language": "en",

        "url": "https://adcmemorial.org/en/",

        "max_articles": 100,
    },

    {
        # Trouvé par recherche web : commission gouvernementale
        # américaine indépendante, source régulière sur les prisonniers
        # religieux/politiques en Ouzbékistan et au Turkménistan.
        "name": "USCIRF",
        "short_name": "USCIRF",
        "profile": "human_rights",
        "label": "International · liberté religieuse",
        "type": "html",
        "language": "en",

        "url": "https://www.uscirf.gov/news-room",

        "max_articles": 100,
    },

    {
        # Ajouté à la demande de l'utilisateur : ONG internationale
        # (fondée par Thor Halvorssen) documentant les prisonniers
        # politiques et la répression sous les régimes autoritaires.
        "name": "Human Rights Foundation",
        "short_name": "HRF",
        "profile": "human_rights",
        "label": "International · droits humains",
        "type": "html",
        "language": "en",

        "url": "https://hrf.org/latest/",

        "max_articles": 150,
    },

    {
        # Ajouté après coup : le flux général ci-dessus ne remonte que
        # les 8 derniers articles tous sujets confondus (Chine, Zambie,
        # Venezuela...), jamais assez ciblé pour faire remonter du
        # contenu Caucase/Asie centrale précis — ex. un activiste
        # syndical condamné en Azerbaïdjan, repéré par l'utilisateur
        # sur le vrai site de HRF mais absent du scanner. HRF a sa
        # propre catégorie régionale, on l'utilise directement.
        "name": "Human Rights Foundation — Europe & Asie centrale",
        "short_name": "HRF Europe/CA",
        "profile": "human_rights",
        "label": "International · Europe & Asie centrale",
        "type": "html",
        "language": "en",

        "url": "https://hrf.org/latest-category/europe-and-central-asia/",

        "max_articles": 150,
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

        "max_articles": 250,
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

        "max_articles": 250,
    },

    {
        "name": "Novastan — anglais",
        "short_name": "Novastan EN",
        "profile": "regional_independent",
        "label": "Régional · indépendant · anglais",
        "type": "html",
        "language": "en",

        "url": "https://novastan.org/en/",

        "max_articles": 250,
    },

    {
        "name": "Novastan — allemand",
        "short_name": "Novastan DE",
        "profile": "regional_independent",
        "label": "Régional · indépendant · allemand",
        "type": "html",
        "language": "de",

        "url": "https://novastan.org/de/",

        "max_articles": 250,
    },

    {
        "name": "UzNews24",
        "short_name": "UzNews24",
        "profile": "regional_media",
        "label": "Régional · Ouzbékistan",
        "type": "html",
        "language": "en",

        "url": "https://uznews.uz/en",

        "max_articles": 250,
    },

    {
        "name": "Sarpa Media",
        "short_name": "Sarpa",
        "profile": "regional_independent",
        "label": "Régional · indépendant",
        "type": "html",
        "language": "multi",

        "url": "https://sarpa.media/",

        "max_articles": 250,
    },

    {
        "name": "Kursiv Media",
        "short_name": "Kursiv",
        "profile": "regional_media",
        "label": "Régional · business & politique",
        "type": "html",
        "language": "en",

        "url": "https://kz.kursiv.media/en/",

        "max_articles": 250,
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

        "max_articles": 250,
    },

    {
        "name": "Vlast — anglais",
        "short_name": "Vlast EN",
        "profile": "regional_independent",
        "label": "Régional · Kazakhstan · anglais",
        "type": "html",
        "language": "en",

        "url": "https://vlast.kz/english/",

        "max_articles": 250,
    },

    {
        "name": "Radio Azattyq",
        "short_name": "Azattyq",
        "profile": "international_independent",
        "label": "International · Kazakhstan",
        "type": "html",
        "language": "kk",

        "url": "https://www.azattyq.org/",

        "max_articles": 250,
    },

    {
        "name": "Orda.kz — russe",
        "short_name": "Orda RU",
        "profile": "regional_independent",
        "label": "Indépendant · Kazakhstan · russe",
        "type": "html",
        "language": "ru",

        "url": "https://orda.kz/",

        "max_articles": 250,
    },

    {
        "name": "Orda.kz — anglais",
        "short_name": "Orda EN",
        "profile": "regional_independent",
        "label": "Indépendant · Kazakhstan · anglais",
        "type": "html",
        "language": "en",

        "url": "https://en.orda.kz/",

        "max_articles": 250,
    },

    {
        "name": "Tengrinews",
        "short_name": "Tengrinews",
        "profile": "regional_media",
        "label": "Média régional · Kazakhstan",
        "type": "html",
        "language": "en",

        "url": "https://en.tengrinews.kz/",

        "max_articles": 250,
    },

    {
        "name": "Centre1",
        "short_name": "Centre1",
        "profile": "regional_media",
        "label": "Média régional · Kazakhstan · russe",
        "type": "html",
        "language": "ru",

        "url": "https://centre1.com/kazakhstan/",

        "fallbacks": [
            "https://centre1.com/",
        ],

        "max_articles": 250,
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

        "max_articles": 250,
    },

    {
        "name": "24.kg — russe",
        "short_name": "24kg RU",
        "profile": "regional_media",
        "label": "Régional · Kirghizistan · russe",
        "type": "html",
        "language": "ru",

        "url": "https://24.kg/",

        "max_articles": 250,
    },

    {
        "name": "24.kg — anglais",
        "short_name": "24kg EN",
        "profile": "regional_media",
        "label": "Régional · Kirghizistan · anglais",
        "type": "html",
        "language": "en",

        "url": "https://24.kg/english/",

        "max_articles": 250,
    },

    {
        "name": "Kaktus Media",
        "short_name": "Kaktus",
        "profile": "regional_independent",
        "label": "Indépendant · Kirghizistan",
        "type": "html",
        "language": "ru",

        "url": "https://kaktus.media/",

        "max_articles": 250,
    },

    {
        "name": "Kabar",
        "short_name": "Kabar",
        "profile": "state_media",
        "label": "Agence officielle · Kirghizistan",
        "type": "html",
        "language": "en",

        "url": "https://en.kabar.kg/",

        "max_articles": 200,
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

        "max_articles": 250,
    },

    {
        "name": "Radio Ozodi",
        "short_name": "Ozodi",
        "profile": "international_independent",
        "label": "International · Tadjikistan",
        "type": "html",
        "language": "tg",

        "url": "https://www.ozodi.org/",

        "max_articles": 250,
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

        "max_articles": 250,
    },

    {
        "name": "Kun.uz",
        "short_name": "Kun.uz",
        "profile": "regional_media",
        "label": "Régional · Ouzbékistan",
        "type": "html",
        "language": "en",

        "url": "https://kun.uz/en",

        "max_articles": 250,
    },

    {
        "name": "Spot.uz",
        "short_name": "Spot.uz",
        "profile": "economic_media",
        "label": "Économie · Ouzbékistan",
        "type": "html",
        "language": "en",

        "url": "https://www.spot.uz/en/",

        "max_articles": 200,
    },

    {
        # Trouvé via find_candidate_sources.py : cité par un article
        # Novastan de niveau A sur l'Ouzbékistan.
        "name": "Daryo.uz",
        "short_name": "Daryo",
        "profile": "regional_media",
        "label": "Régional · Ouzbékistan",
        "type": "html",
        "language": "en",

        "url": "https://daryo.uz/en",

        "max_articles": 200,
    },

    {
        # Trouvé via find_candidate_sources.py, même article que Daryo.uz.
        # Pas de version anglaise connue.
        "name": "Qalampir.uz",
        "short_name": "Qalampir",
        "profile": "regional_media",
        "label": "Régional · Ouzbékistan",
        "type": "html",
        "language": "uz",

        "url": "https://qalampir.uz/",

        "max_articles": 200,
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

        "max_articles": 250,
    },

    {
        "name": "Chronicles of Turkmenistan",
        "short_name": "Chronicles",
        "profile": "human_rights",
        "label": "Indépendant · Turkménistan",
        "type": "html",
        "language": "ru",

        "url": "https://hronikatm.com/",

        "max_articles": 250,
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

        "max_articles": 250,
    },

    {
        "name": "Central Asia-Caucasus Analyst",
        "short_name": "CAC Analyst",
        "profile": "regional_analysis",
        "label": "Régional · analyse",
        "type": "html",
        "language": "en",

        "url": "https://www.cacianalyst.org/",

        "max_articles": 200,
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

        "max_articles": 200,
    },

    {
        "name": "Trend News Agency",
        "short_name": "Trend",
        "profile": "regional_media",
        "label": "Régional · Caucase",
        "type": "html",
        "language": "en",

        "url": "https://en.trend.az/",

        "max_articles": 200,
    },

    {
        # Trouvé par recherche web : agrégateur quotidien de médias
        # locaux pour les trois pays du Caucase du Sud — exactement le
        # pendant Caucase de ce que Novastan fait pour l'Asie centrale.
        "name": "JAMnews",
        "short_name": "JAMnews",
        "profile": "regional_independent",
        "label": "Régional · Caucase",
        "type": "html",
        "language": "en",

        "url": "https://jam-news.net/",

        "max_articles": 200,
    },

    {
        # Trouvé par recherche web : analyse dédiée Caucase du Sud.
        "name": "Caucasus Watch",
        "short_name": "Caucasus Watch",
        "profile": "regional_analysis",
        "label": "Régional · analyse · Caucase",
        "type": "html",
        "language": "en",

        "url": "https://caucasuswatch.de/en/",

        "max_articles": 150,
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

        "max_articles": 200,
    },

    {
        "name": "Jamestown Foundation",
        "short_name": "Jamestown",
        "profile": "security_analysis",
        "label": "International · sécurité · Eurasie",
        "type": "html",
        "language": "en",

        "url": "https://jamestown.org/",

        "max_articles": 200,
    },

    {
        "name": "International Crisis Group",
        "short_name": "Crisis Group",
        "profile": "security_analysis",
        "label": "International · prévention des conflits",
        "type": "html",
        "language": "en",

        "url": "https://www.crisisgroup.org/",

        "max_articles": 200,
    },

    {
        "name": "Carnegie Endowment for International Peace",
        "short_name": "Carnegie",
        "profile": "security_analysis",
        "label": "International · analyse géopolitique",
        "type": "html",
        "language": "en",

        "url": "https://carnegieendowment.org/",

        "max_articles": 200,
    },

    {
        "name": "Chatham House",
        "short_name": "Chatham House",
        "profile": "security_analysis",
        "label": "International · Russie & Eurasie",
        "type": "html",
        "language": "en",

        "url": "https://www.chathamhouse.org/",

        "max_articles": 200,
    },

    {
        "name": "RAND Corporation",
        "short_name": "RAND",
        "profile": "security_analysis",
        "label": "International · recherche sécurité",
        "type": "html",
        "language": "en",

        "url": "https://www.rand.org/",

        "max_articles": 200,
    },

    {
        "name": "Atlantic Council",
        "short_name": "Atlantic Council",
        "profile": "security_analysis",
        "label": "International · Eurasie",
        "type": "html",
        "language": "en",

        "url": "https://www.atlanticcouncil.org/",

        "max_articles": 200,
    },

    {
        "name": "CSIS",
        "short_name": "CSIS",
        "profile": "security_analysis",
        "label": "International · sécurité & stratégie",
        "type": "html",
        "language": "en",

        "url": "https://www.csis.org/",

        "max_articles": 200,
    },

    {
        "name": "Foreign Policy Research Institute",
        "short_name": "FPRI",
        "profile": "security_analysis",
        "label": "International · Eurasie",
        "type": "html",
        "language": "en",

        "url": "https://www.fpri.org/",

        "max_articles": 200,
    },

    {
        "name": "Stimson Center",
        "short_name": "Stimson",
        "profile": "security_analysis",
        "label": "International · sécurité",
        "type": "html",
        "language": "en",

        "url": "https://www.stimson.org/",

        "max_articles": 200,
    },

    {
        "name": "George C. Marshall European Center for Security Studies",
        "short_name": "Marshall Center",
        "profile": "security_analysis",
        "label": "International · études de sécurité",
        "type": "html",
        "language": "en",

        "url": "https://www.marshallcenter.org/",

        "max_articles": 200,
    },

    {
        "name": "PONARS Eurasia",
        "short_name": "PONARS",
        "profile": "security_analysis",
        "label": "International · post-soviétique",
        "type": "html",
        "language": "en",

        "url": "https://www.ponarseurasia.org/",

        "max_articles": 200,
    },

    {
        "name": "SpecialEurasia",
        "short_name": "SpecialEurasia",
        "profile": "security_analysis",
        "label": "International · Asie centrale & Caucase",
        "type": "html",
        "language": "en",

        "url": "https://www.specialeurasia.com/",

        "max_articles": 150,
    },

    {
        "name": "Caspian Policy Center",
        "short_name": "CPC",
        "profile": "security_analysis",
        "label": "International · Caspienne",
        "type": "html",
        "language": "en",

        "url": "https://www.caspianpolicy.org/",

        "max_articles": 150,
    },

    {
        # Trouvé via find_candidate_sources.py.
        "name": "Institute for European Politics",
        "short_name": "IEP Berlin",
        "profile": "security_analysis",
        "label": "International · analyse européenne",
        "type": "html",
        "language": "de",

        "url": "https://iep-berlin.de/",

        "max_articles": 100,
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

        "max_articles": 200,
    },

    {
        # Trouvé via find_candidate_sources.py : cité (en tant que
        # source russe) par un article Al Jazeera de niveau B. Version
        # russe du TASS ci-dessus — même agence, entrée séparée pour
        # rester cohérent avec le reste du fichier (Novastan, Amnesty,
        # HRW... une entrée par langue).
        "name": "TASS — russe",
        "short_name": "TASS RU",
        "profile": "state_media",
        "label": "Média officiel · agence de presse russe · russe",
        "type": "html",
        "language": "ru",

        "url": "https://tass.ru/",

        "max_articles": 200,
    },

    {
        # Trouvé via find_candidate_sources.py : cité par un article
        # Al Jazeera de niveau B.
        "name": "Izvestia",
        "short_name": "Izvestia",
        "profile": "state_media",
        "label": "Média proche du pouvoir · russe",
        "type": "html",
        "language": "ru",

        "url": "https://iz.ru/",

        "max_articles": 200,
    },

    {
        "name": "RIA Novosti",
        "short_name": "RIA Novosti",
        "profile": "state_media",
        "label": "Média officiel · agence de presse russe",
        "type": "html",
        "language": "ru",

        "url": "https://ria.ru/",

        "max_articles": 200,
    },

    {
        "name": "Sputnik",
        "short_name": "Sputnik",
        "profile": "state_media",
        "label": "Média officiel · propagande internationale russe",
        "type": "html",
        "language": "en",

        "url": "https://sputniknews.com/",

        "max_articles": 200,
    },

    {
        "name": "Regnum",
        "short_name": "Regnum",
        "profile": "state_media",
        "label": "Média officiel · espace post-soviétique",
        "type": "html",
        "language": "ru",

        "url": "https://regnum.ru/",

        "max_articles": 200,
    },

    {
        "name": "Rossiyskaya Gazeta Beyond (RBTH)",
        "short_name": "RBTH",
        "profile": "state_media",
        "label": "Média officiel · diplomatie publique russe",
        "type": "html",
        "language": "en",

        "url": "https://www.rbth.com/",

        "max_articles": 150,
    },

    {
        "name": "Nezavisimaya Gazeta",
        "short_name": "NG.ru",
        "profile": "state_media",
        "label": "Média proche du pouvoir · russe",
        "type": "html",
        "language": "ru",

        "url": "https://www.ng.ru/",

        "max_articles": 150,
    },

    {
        "name": "Kommersant",
        "short_name": "Kommersant",
        "profile": "state_media",
        "label": "Média proche du pouvoir · russe",
        "type": "html",
        "language": "ru",

        "url": "https://www.kommersant.ru/",

        "max_articles": 150,
    },

    {
        "name": "Vedomosti",
        "short_name": "Vedomosti",
        "profile": "state_media",
        "label": "Média proche du pouvoir · russe",
        "type": "html",
        "language": "ru",

        "url": "https://www.vedomosti.ru/",

        "max_articles": 150,
    },

    {
        "name": "Kremlin.ru",
        "short_name": "Kremlin",
        "profile": "state_media",
        "label": "Média officiel · présidence russe",
        "type": "html",
        "language": "ru",

        "url": "http://kremlin.ru/",

        "max_articles": 150,
    },

    {
        "name": "Gouvernement russe",
        "short_name": "Government.ru",
        "profile": "state_media",
        "label": "Média officiel · gouvernement russe",
        "type": "html",
        "language": "ru",

        "url": "http://government.ru/",

        "max_articles": 150,
    },

    {
        "name": "Ministère russe des Affaires étrangères",
        "short_name": "MID.ru",
        "profile": "state_media",
        "label": "Média officiel · diplomatie russe",
        "type": "html",
        "language": "ru",

        "url": "https://www.mid.ru/",

        "max_articles": 150,
    },

    {
        "name": "Mission russe à l'ONU",
        "short_name": "Russia UN",
        "profile": "state_media",
        "label": "Média officiel · diplomatie russe",
        "type": "html",
        "language": "en",

        "url": "https://russiaun.ru/",

        "max_articles": 100,
    },

    {
        "name": "Xinhua",
        "short_name": "Xinhua",
        "profile": "state_media",
        "label": "Média officiel · agence de presse chinoise",
        "type": "html",
        "language": "en",

        "url": "https://english.news.cn/",

        "max_articles": 200,
    },

    {
        "name": "China Daily",
        "short_name": "China Daily",
        "profile": "state_media",
        "label": "Média officiel · presse chinoise",
        "type": "html",
        "language": "en",

        "url": "https://www.chinadaily.com.cn/",

        "max_articles": 200,
    },

    {
        "name": "CGTN",
        "short_name": "CGTN",
        "profile": "state_media",
        "label": "Média officiel · diffuseur chinois international",
        "type": "html",
        "language": "en",

        # "news.cgtn.com" 404 sur un run réel — le sous-domaine "news."
        # n'existe pas, remplacé par le domaine principal.
        "url": "https://www.cgtn.com/",

        "max_articles": 200,
    },

    {
        "name": "Ministère chinois des Affaires étrangères",
        "short_name": "MFA Chine",
        "profile": "state_media",
        "label": "Média officiel · diplomatie chinoise",
        "type": "html",
        "language": "en",

        "url": "https://www.fmprc.gov.cn/eng/",

        "max_articles": 150,
    },

    {
        "name": "China Diplomacy",
        "short_name": "China Diplomacy",
        "profile": "state_media",
        "label": "Média officiel · diplomatie chinoise",
        "type": "html",
        "language": "en",

        "url": "https://www.chinadiplomacy.org.cn/",

        "max_articles": 150,
    },

    {
        "name": "NDRC (Chine)",
        "short_name": "NDRC",
        "profile": "state_media",
        "label": "Média officiel · politique économique chinoise",
        "type": "html",
        "language": "en",

        "url": "https://en.ndrc.gov.cn/",

        "max_articles": 100,
    },

    {
        "name": "CIDCA (Chine)",
        "short_name": "CIDCA",
        "profile": "state_media",
        "label": "Média officiel · aide au développement chinoise",
        "type": "html",
        "language": "en",

        "url": "https://en.cidca.gov.cn/",

        "max_articles": 100,
    },

    # ========================================================
    # IRAN
    #
    # Iran fait partie de la région élargie couverte par le scanner
    # (cf. MAJOR_GEOPOLITICAL_TERMS dans keywords.py). Trouvées via
    # find_candidate_sources.py, citées par un article RFE/RL de
    # niveau A sur les divisions internes iraniennes.
    # ========================================================

    {
        "name": "IRNA",
        "short_name": "IRNA",
        "profile": "state_media",
        "label": "Média officiel · agence de presse iranienne",
        "type": "html",
        "language": "en",

        "url": "https://en.irna.ir/",

        "max_articles": 150,
    },

    {
        "name": "Fararu",
        "short_name": "Fararu",
        "profile": "international_independent",
        "label": "International · Iran",
        "type": "html",
        "language": "fa",

        "url": "https://www.fararu.com/",

        "max_articles": 150,
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

        "max_articles": 150,
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


# ============================================================
# REGROUPEMENT D'AFFICHAGE (audit)
#
# Les 13 profils ci-dessus sont trop nombreux pour être lisibles dans
# la table d'audit (des milliers de lignes en niveau D). Regroupés en
# 8 catégories pour l'affichage uniquement — le scoring, lui, ignore
# totalement ce regroupement.
# ============================================================

PROFILE_GROUPS = {
    "human_rights": "Droits humains & presse",
    "press_freedom": "Droits humains & presse",

    "investigative": "Investigation",

    "independent": "Médias indépendants",
    "regional_independent": "Médias indépendants",
    "international_independent": "Médias indépendants",

    "regional_media": "Médias régionaux",
    "regional_analysis": "Médias régionaux",

    "international_analysis": "Analyse internationale",

    "security_analysis": "Sécurité & géopolitique (think tanks)",

    "state_media": "Médias officiels (contrepoint)",

    "economic_media": "Économie & recherche",
    "academic_research": "Économie & recherche",
}

# Ordre d'affichage : des sources les plus proches de la ligne
# éditoriale (droits humains, indépendant) vers les sources ajoutées
# comme contrepoint (médias officiels) ou hors-thème (économie).
PROFILE_GROUP_ORDER = [
    "Droits humains & presse",
    "Investigation",
    "Médias indépendants",
    "Médias régionaux",
    "Analyse internationale",
    "Sécurité & géopolitique (think tanks)",
    "Médias officiels (contrepoint)",
    "Économie & recherche",
]
