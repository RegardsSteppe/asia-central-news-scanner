#!/usr/bin/env python3
"""
Asia Central News Scanner - Daily email digest at 8am Paris time
Scans top 5 Asian Central news websites and sends synthetic summary via email
"""

import os
import smtplib
import schedule
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import pytz
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
TOP_NEWS_SOURCES = [
    {
        'name': 'Eurasianet',
        'url': 'https://eurasianet.org/',
        'description': 'News and analysis from the Caucasus and Central Asia'
    },
    {
        'name': 'Cabar.asia',
        'url': 'https://cabar.asia/',
        'description': 'Central Asia news portal'
    },
    {
        'name': 'Stanradar',
        'url': 'https://stanradar.com/',
        'description': 'Central Asian news agency'
    },
    {
        'name': 'Azernews',
        'url': 'https://www.azernews.az/',
        'description': 'Azerbaijan news source'
    },
    {
        'name': 'The Diplomat',
        'url': 'https://thediplomat.com/regions/asia/',
        'description': 'Asia-Pacific news and analysis'
    }
]

EMAIL_CONFIG = {
    'sender_email': os.getenv('SENDER_EMAIL', 'your_email@gmail.com'),
    'sender_password': os.getenv('SENDER_PASSWORD', 'your_app_password'),
    'recipient_email': os.getenv('RECIPIENT_EMAIL', 'recipient@example.com'),
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587))
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def fetch_news_from_source(source):
    """
    Fetch news headlines from a single source
    Returns a dict with source info and articles
    """
    try:
        logger.info(f"Fetching news from {source['name']}...")
        response = requests.get(source['url'], headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract article headlines (adapts to common HTML patterns)
        articles = []
        
        # Look for common headline selectors
        selectors = ['h1', 'h2', 'h3', 'article h2', '[class*="headline"]', '[class*="title"]']
        
        for selector in selectors:
            for element in soup.select(selector)[:3]:  # Get top 3
                text = element.get_text(strip=True)
                if len(text) > 20:  # Filter out too-short texts
                    link = element.find_parent('a')
                    if link and link.get('href'):
                        articles.append({
                            'title': text[:150],
                            'link': link.get('href')
                        })
            
            if articles:
                break
        
        return {
            'source': source['name'],
            'description': source['description'],
            'articles': articles[:3],  # Top 3 articles per source
            'status': 'success'
        }
    
    except Exception as e:
        logger.warning(f"Error fetching from {source['name']}: {str(e)}")
        return {
            'source': source['name'],
            'description': source['description'],
            'articles': [],
            'status': f'error: {str(e)}'
        }


def fetch_all_news():
    """
    Fetch news from all configured sources
    """
    all_news = []
    
    for source in TOP_NEWS_SOURCES:
        news_data = fetch_news_from_source(source)
        all_news.append(news_data)
        time.sleep(2)  # Rate limiting
    
    return all_news


def create_email_body(news_data):
    """
    Create a synthetic HTML email body with news summary
    """
    paris_tz = pytz.timezone('Europe/Paris')
    paris_time = datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S %Z')
    
    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1a5490; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 5px 0 0 0; font-size: 14px; }}
                .source-section {{ margin-bottom: 30px; border-left: 4px solid #1a5490; padding-left: 20px; }}
                .source-title {{ font-size: 20px; font-weight: bold; color: #1a5490; margin-bottom: 10px; }}
                .source-description {{ font-size: 12px; color: #666; margin-bottom: 15px; font-style: italic; }}
                .article {{ margin-bottom: 15px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }}
                .article-title {{ font-weight: bold; color: #1a5490; margin-bottom: 5px; }}
                .article-link {{ color: #0066cc; text-decoration: none; font-size: 12px; word-break: break-all; }}
                .article-link:hover {{ text-decoration: underline; }}
                .status {{ padding: 10px; background-color: #fff3cd; border-radius: 3px; margin-top: 5px; font-size: 12px; color: #856404; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📰 Asia Central News Digest</h1>
                    <p>Daily Summary • {paris_time}</p>
                </div>
    """
    
    for source_news in news_data:
        source_name = source_news['source']
        description = source_news['description']
        articles = source_news['articles']
        status = source_news['status']
        
        html_content += f"""
                <div class="source-section">
                    <div class="source-title">🔗 {source_name}</div>
                    <div class="source-description">{description}</div>
        """
        
        if status == 'success' and articles:
            for i, article in enumerate(articles, 1):
                html_content += f"""
                    <div class="article">
                        <div class="article-title">{i}. {article['title']}</div>
                        <div class="article-link">→ <a href="{article['link']}">{article['link'][:80]}...</a></div>
                    </div>
                """
        else:
            html_content += f"""
                    <div class="status">
                        ⚠️ Status: {status}
                    </div>
            """
        
        html_content += """
                </div>
        """
    
    html_content += """
                <div class="footer">
                    <p>This is an automated daily news digest sent at 8:00 AM Paris Time</p>
                    <p>To modify this service, please update your configuration</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    return html_content


def send_email(news_data):
    """
    Send the news summary via email
    """
    try:
        logger.info("Preparing email...")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Asia Central News Digest - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        
        # Create email body
        html_body = create_email_body(news_data)
        
        # Attach HTML content
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        logger.info("Sending email...")
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {EMAIL_CONFIG['recipient_email']}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def job():
    """
    Main job to run at scheduled time
    """
    logger.info("=" * 50)
    logger.info("Starting news scan...")
    
    # Fetch news
    news_data = fetch_all_news()
    
    # Send email
    send_email(news_data)
    
    logger.info("News scan completed")
    logger.info("=" * 50)


def schedule_daily_job():
    """
    Schedule the job to run every day at 8:00 AM Paris time
    """
    # Schedule the job
    schedule.every().day.at("08:00").do(job)
    
    logger.info("News scanner scheduled to run daily at 08:00 AM (Paris Time)")
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    try:
        # Run in scheduling mode
        schedule_daily_job()
    except KeyboardInterrupt:
        logger.info("News scanner stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
