# ============================================================
# VOCABULAIRE DES TITRES
# ============================================================

TITLE_STOPWORDS = {
    # English
    "the", "and", "of", "to", "in", "on", "for", "with",
    "from", "at", "by", "as", "is", "are", "was", "were",
    "a", "an", "this", "that", "these", "those", "after",
    "before", "into", "over", "under", "about", "amid",
    "new", "news",

    # Français
    "le", "la", "les", "un", "une", "des", "de", "du",
    "et", "ou", "à", "au", "aux", "en", "dans", "sur",
    "pour", "avec", "par", "ce", "cette", "ces", "après",
    "avant", "entre", "vers", "plus", "sans",

    # Russe / translittération fréquente
    "и", "в", "во", "на", "с", "со", "из", "по", "к",
    "ко", "для", "от", "до", "за", "что", "как", "не",
    "это", "а", "но",

    # Mots très fréquents dans les titres journalistiques
    "says", "said", "report", "reports", "according",
    "latest", "update", "officials", "official",
}


def extract_title_words(title):
    """
    Extrait les mots significatifs d'un titre.

    - minuscules
    - conserve les lettres Unicode
    - supprime les chiffres
    - supprime la ponctuation
    - ignore les stopwords
    - ignore les mots d'une seule lettre
    """

    if not title:
        return []

    text = normalize_text(title)

    # Remplace tout ce qui n'est pas une lettre Unicode
    # par un espace.
    words = re.findall(
        r"[^\W\d_]+",
        text,
        flags=re.UNICODE,
    )

    result = []

    for word in words:

        if len(word) < 2:
            continue

        if word in TITLE_STOPWORDS:
            continue

        result.append(word)

    return result


def build_title_word_list(
    articles,
    min_count=2,
    max_words=100,
):
    """
    Construit le vocabulaire des titres.

    Retourne une liste de dictionnaires :

    [
        {
            "word": "kazakhstan",
            "count": 42,
        },
        ...
    ]

    min_count permet d'éliminer les mots qui
    n'apparaissent qu'une seule fois.
    """

    counts = {}

    for article in articles:

        title = article.get(
            "title",
            "",
        )

        words = extract_title_words(
            title
        )

        for word in words:

            counts[word] = (
                counts.get(word, 0) + 1
            )

    vocabulary = [
        {
            "word": word,
            "count": count,
        }
        for word, count in counts.items()
        if count >= min_count
    ]

    vocabulary.sort(
        key=lambda item: (
            item["count"],
            item["word"],
        ),
        reverse=True,
    )

    return vocabulary[:max_words]
