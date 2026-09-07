def create_web_page(news_data):
    """
    Create a public HTML page from the news data.
    """
    paris_tz = pytz.timezone('Europe/Paris')
    paris_time = datetime.now(paris_tz).strftime('%d/%m/%Y à %H:%M:%S')

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Asia Central News Digest</title>

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                         Roboto, Arial, sans-serif;
            background: #f4f6f8;
            color: #222;
        }}

        .header {{
            background: linear-gradient(135deg, #174a7c, #2474b5);
            color: white;
            padding: 45px 20px;
            text-align: center;
        }}

        .header h1 {{
            margin: 0 0 10px;
            font-size: 36px;
        }}

        .header p {{
            margin: 0;
            opacity: 0.9;
        }}

        .container {{
            max-width: 1000px;
            margin: 35px auto;
            padding: 0 20px;
        }}

        .source {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
        }}

        .source h2 {{
            margin-top: 0;
            color: #174a7c;
            border-bottom: 2px solid #e8edf2;
            padding-bottom: 12px;
        }}

        .description {{
            color: #777;
            font-size: 14px;
            margin-bottom: 20px;
        }}

        .article {{
            padding: 16px;
            margin-bottom: 12px;
            background: #f7f9fb;
            border-radius: 8px;
            border-left: 4px solid #2474b5;
        }}

        .article a {{
            color: #174a7c;
            text-decoration: none;
            font-weight: 600;
            font-size: 17px;
        }}

        .article a:hover {{
            text-decoration: underline;
        }}

        .status {{
            color: #856404;
            background: #fff3cd;
            padding: 12px;
            border-radius: 6px;
        }}

        footer {{
            text-align: center;
            color: #777;
            padding: 35px 20px;
            font-size: 13px;
        }}

        @media (max-width: 600px) {{
            .header h1 {{
                font-size: 27px;
            }}

            .source {{
                padding: 18px;
            }}
        }}
    </style>
</head>

<body>

<header class="header">
    <h1>📰 Asia Central News Digest</h1>
    <p>Dernière mise à jour : {paris_time} (Paris)</p>
</header>

<main class="container">
"""

    for source_news in news_data:
        source_name = source_news['source']
        description = source_news['description']
        articles = source_news['articles']
        status = source_news['status']

        html += f"""
    <section class="source">
        <h2>🔗 {source_name}</h2>
        <div class="description">{description}</div>
"""

        if status == 'success' and articles:
            for i, article in enumerate(articles, 1):
                link = article['link']

                # Convert relative links to absolute URLs
                if link.startswith('/'):
                    source_config = next(
                        (
                            s for s in TOP_NEWS_SOURCES
                            if s['name'] == source_name
                        ),
                        None
                    )

                    if source_config:
                        link = source_config['url'].rstrip('/') + link

                html += f"""
        <div class="article">
            <a href="{link}" target="_blank" rel="noopener noreferrer">
                {i}. {article['title']}
            </a>
        </div>
"""

        else:
            html += f"""
        <div class="status">
            ⚠️ Impossible de récupérer cette source.<br>
            <small>{status}</small>
        </div>
"""

        html += """
    </section>
"""

    html += """
</main>

<footer>
    Asia Central News Scanner · Mise à jour automatique quotidienne
</footer>

</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as file:
        file.write(html)

    logger.info("Public HTML page generated: index.html")
