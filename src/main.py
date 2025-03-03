import os
import argparse
import logging
from datetime import datetime
import pytz
import json
import re
from pathlib import Path
from dateutil import parser

from src.config import Config
from src.scrapers.rss_scraper import RSSFeedScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_index_html(feeds_dir, articles_data=None):
    """Generate an index.html file that displays the actual articles"""
    
    # Load articles from JSON if no data is provided directly
    if articles_data is None:
        all_json_path = os.path.join(feeds_dir, 'all.json')
        if os.path.exists(all_json_path):
            with open(all_json_path, 'r', encoding='utf-8') as f:
                feed_data = json.load(f)
                articles_data = feed_data.get('items', [])
        else:
            articles_data = []
    
    # Create index.html
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Daily Digest</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2 {{
            color: #2c3e50;
        }}
        h1 {{
            border-bottom: 2px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        .updated {{
            font-size: 14px;
            color: #6a737d;
            margin-top: 5px;
            margin-bottom: 30px;
        }}
        .feed-links {{
            margin-bottom: 30px;
        }}
        .feed-link {{
            display: inline-block;
            padding: 5px 10px;
            background-color: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 3px;
            color: #0366d6;
            text-decoration: none;
            font-size: 14px;
            margin-right: 10px;
        }}
        .feed-link:hover {{
            background-color: #0366d6;
            color: white;
        }}
        .article {{
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }}
        .article:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0,0,0,0.1);
        }}
        .article-title {{
            font-size: 22px;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 10px;
        }}
        .article-title a {{
            color: #0366d6;
            text-decoration: none;
        }}
        .article-title a:hover {{
            text-decoration: underline;
        }}
        .article-meta {{
            font-size: 14px;
            color: #6a737d;
            margin-bottom: 15px;
        }}
        .article-source {{
            font-weight: 600;
        }}
        .article-summary {{
            margin-bottom: 15px;
        }}
        .article-link {{
            display: inline-block;
            padding: 8px 16px;
            background-color: #0366d6;
            color: white;
            border-radius: 3px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
        }}
        .article-link:hover {{
            background-color: #035cc1;
        }}
        .filters {{
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f6f8fa;
            border-radius: 6px;
        }}
        .no-articles {{
            padding: 40px;
            text-align: center;
            background-color: #f6f8fa;
            border-radius: 6px;
            color: #6a737d;
        }}
    </style>
</head>
<body>
    <h1>AI News Daily Digest</h1>
    <p>A curated collection of AI-related news, updated regularly.</p>
    
    <div class="updated">Last updated: {datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
    
    <div class="feed-links">
        <span>Subscribe to feeds: </span>
        <a href="all.xml" class="feed-link">RSS</a>
        <a href="all.atom" class="feed-link">ATOM</a>
        <a href="all.json" class="feed-link">JSON</a>
    </div>
    
    <h2>Latest Articles</h2>
"""
    
    if not articles_data:
        html_content += """
    <div class="no-articles">
        <h3>No articles found</h3>
        <p>The feed scraper hasn't collected any articles yet or no articles match your criteria.</p>
    </div>
"""
    else:
        # Sort articles by date (newest first)
        articles_data = sorted(
            articles_data, 
            key=lambda x: parser.parse(x.get('date_published', '1970-01-01T00:00:00Z')), 
            reverse=True
        )
        
        # Display each article
        for article in articles_data:
            published_date = parser.parse(article.get('date_published', ''))
            formatted_date = published_date.strftime('%Y-%m-%d %H:%M UTC')
            
            author = article.get('author', {})
            author_name = author.get('name', '') if author else ''
            
            html_content += f"""
    <div class="article">
        <h3 class="article-title"><a href="{article.get('url', '#')}">{article.get('title', 'Untitled')}</a></h3>
        <div class="article-meta">
            <span class="article-source">{article.get('source', '')}</span>
            {f' • {author_name}' if author_name else ''}
            • {formatted_date}
        </div>
        <div class="article-summary">
            {article.get('summary', '')}
        </div>
        <a href="{article.get('url', '#')}" class="article-link" target="_blank">Read More</a>
    </div>"""
    
    html_content += """
</body>
</html>
"""
    
    # Write to file
    index_path = os.path.join(feeds_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Generated index.html with {len(articles_data)} articles")
    return index_path

def main():
    """Main function to run the RSS Feed Scraper"""
    parser = argparse.ArgumentParser(description='RSS Feed Scraper for AI topics')
    parser.add_argument('--output-dir', type=str, help='Output directory for feed files')
    parser.add_argument('--ai-only', action='store_true', help='Only include AI-related articles')
    
    args = parser.parse_args()
    
    # Use command line arguments if provided, otherwise use config
    output_dir = args.output_dir if args.output_dir else Config.OUTPUT_DIR
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Starting RSS Feed Scraper. Output directory: {output_dir}")
    
    # Initialize and run the scraper
    scraper = RSSFeedScraper(
        feed_urls=Config.FEEDS,
        output_dir=output_dir,
        ai_keywords=Config.AI_KEYWORDS if args.ai_only else []
    )
    
    try:
        # Fetch and process all feeds
        all_articles = scraper.scrape()
        
        # Prepare articles for the index
        flattened_articles = []
        for category, articles in all_articles.items():
            for article in articles:
                flattened_articles.append({
                    'id': article['url'],
                    'url': article['url'],
                    'title': article['title'],
                    'summary': article['description'] or article['content'][:150] + '...',
                    'date_published': article['published_at'],
                    'author': {'name': article['author']} if article['author'] else None,
                    'source': article['source']
                })
        
        # Generate index.html with the actual articles
        generate_index_html(output_dir, flattened_articles)
        
        logger.info("RSS Feed Scraper completed successfully")
    except Exception as e:
        logger.error(f"Error running RSS Feed Scraper: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())