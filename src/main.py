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

def update_archive(feeds_dir, new_articles):
    """
    Update the archive with new articles.
    The archive maintains all articles ever scraped, preserving history.
    """
    archive_path = os.path.join(feeds_dir, 'archive.json')
    archive = {}
    
    # Load existing archive if it exists
    if os.path.exists(archive_path):
        try:
            with open(archive_path, 'r', encoding='utf-8') as f:
                archive = json.load(f)
        except Exception as e:
            logger.error(f"Error loading archive: {e}")
            # Create a new archive if the existing one is corrupted
            archive = {"version": "1.0", "updated": "", "items": {}}
    else:
        # Initialize new archive
        archive = {"version": "1.0", "updated": "", "items": {}}
    
    # Get existing article IDs for quick lookup
    existing_ids = set(archive.get("items", {}).keys())
    
    # Add new articles to archive if they don't exist already
    added_count = 0
    for article in new_articles:
        article_id = article['id']
        
        if article_id not in existing_ids:
            # Add to archive with original datetime as key
            archive["items"][article_id] = article
            added_count += 1
    
    # Update archive metadata
    archive["updated"] = datetime.now(pytz.UTC).isoformat()
    archive["total_articles"] = len(archive["items"])
    
    # Save updated archive
    with open(archive_path, 'w', encoding='utf-8') as f:
        json.dump(archive, f, indent=2)
    
    logger.info(f"Archive updated with {added_count} new articles. Total: {archive['total_articles']}")
    return archive

def generate_archive_html(feeds_dir, archive_data):
    """Generate an archive.html file that displays all historical articles in a compact list view"""
    
    # Create archive.html
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Archive</title>
    <style>
        :root {{
            --primary-color: #2563eb;
            --primary-hover: #1d4ed8;
            --background: #f8fafc;
            --card-bg: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --border-light: #f1f5f9;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.5;
            color: var(--text-primary);
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: var(--background);
        }}
        
        h1, h2, h3 {{
            color: var(--text-primary);
            font-weight: 600;
        }}
        
        h1 {{
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 1.5rem;
        }}
        
        .description {{
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }}
        
        .updated {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
        }}
        
        .nav-links {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        
        .nav-link {{
            display: inline-block;
            padding: 0.5rem 1rem;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            color: var(--primary-color);
            text-decoration: none;
            font-size: 0.75rem;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .nav-link:hover {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        .total-count {{
            text-align: center;
            margin-bottom: 1rem;
            font-weight: 500;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
        
        .month-header {{
            margin-top: 1.5rem;
            padding: 0.5rem 0.75rem;
            background-color: var(--card-bg);
            border-radius: 0.25rem;
            font-size: 1rem;
            font-weight: 600;
            border-bottom: 2px solid var(--primary-color);
            box-shadow: var(--shadow-sm);
        }}
        
        .archive-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.5rem;
            font-size: 0.875rem;
            background-color: var(--card-bg);
            border-radius: 0.25rem;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }}
        
        .archive-table th {{
            text-align: left;
            padding: 0.625rem 0.75rem;
            background-color: var(--border-light);
            color: var(--text-secondary);
            font-weight: 500;
            cursor: pointer;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .archive-table th:hover {{
            background-color: #e2e8f0;
        }}
        
        .archive-table tr {{
            border-bottom: 1px solid var(--border-color);
        }}
        
        .archive-table tr:last-child {{
            border-bottom: none;
        }}
        
        .archive-table tr:hover {{
            background-color: #f8fafc;
        }}
        
        .archive-table td {{
            padding: 0.5rem 0.75rem;
            vertical-align: middle;
        }}
        
        .article-title-cell {{
            max-width: 40%;
        }}
        
        .article-title-cell a {{
            color: var(--text-primary);
            text-decoration: none;
            display: block;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .article-title-cell a:hover {{
            color: var(--primary-color);
            text-decoration: underline;
        }}
        
        .article-source {{
            font-weight: 500;
            color: var(--primary-color);
        }}
        
        .article-date {{
            white-space: nowrap;
            color: var(--text-secondary);
        }}
        
        .no-articles {{
            padding: 2rem;
            text-align: center;
            background-color: var(--card-bg);
            border-radius: 0.25rem;
            color: var(--text-secondary);
            box-shadow: var(--shadow-sm);
        }}
        
        @media (max-width: 768px) {{
            .archive-table {{
                font-size: 0.75rem;
            }}
            
            .archive-table th, 
            .archive-table td {{
                padding: 0.5rem;
            }}
            
            .article-category {{
                display: none;
            }}
        }}
        
        @media (max-width: 480px) {{
            .article-date {{
                display: none;
            }}
            
            .article-title-cell {{
                max-width: 60%;
            }}
        }}
        
        /* Sorting indicators */
        .sort-icon::after {{
            content: '⇵';
            margin-left: 0.25rem;
            font-size: 0.75rem;
        }}
        
        .sort-asc::after {{
            content: '↑';
            margin-left: 0.25rem;
            font-size: 0.75rem;
        }}
        
        .sort-desc::after {{
            content: '↓';
            margin-left: 0.25rem;
            font-size: 0.75rem;
        }}
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            // Sorting functionality
            const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
            
            const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
                v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
            )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));
            
            document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {{
                const table = th.closest('table');
                const tbody = table.querySelector('tbody');
                
                // Reset all headers
                Array.from(th.parentNode.children)
                    .forEach(el => {{
                        el.classList.remove('sort-asc', 'sort-desc');
                        el.classList.add('sort-icon');
                    }});
                
                // Determine sort direction
                const asc = !th.classList.contains('sort-asc');
                if (asc) {{
                    th.classList.remove('sort-icon', 'sort-desc');
                    th.classList.add('sort-asc');
                }} else {{
                    th.classList.remove('sort-icon', 'sort-asc');
                    th.classList.add('sort-desc');
                }}
                
                // Sort the table
                Array.from(tbody.querySelectorAll('tr'))
                    .sort(comparer(Array.from(th.parentNode.children).indexOf(th), asc))
                    .forEach(tr => tbody.appendChild(tr));
            }})));
        }});
    </script>
</head>
<body>
    <div class="header">
        <h1>AI News Archive</h1>
        <p class="description">A complete archive of all AI-related news scraped since the beginning.</p>
        <div class="updated">Last updated: {datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
    </div>
    
    <div class="nav-links">
        <a href="index.html" class="nav-link">Latest Articles</a>
        <a href="archive.json" class="nav-link">Download Archive (JSON)</a>
    </div>
    
    <div class="total-count">
        Total Articles: {len(archive_data.get("items", {}))}
    </div>
"""
    
    if not archive_data or not archive_data.get("items"):
        html_content += """
    <div class="no-articles">
        <h3>No articles found</h3>
        <p>The archive is empty. Articles will appear here once they've been scraped.</p>
    </div>
"""
    else:
        # Get all articles and convert to list
        all_articles = []
        for article_id, article in archive_data.get("items", {}).items():
            all_articles.append(article)
            
        # Sort articles by date (newest first)
        all_articles = sorted(
            all_articles, 
            key=lambda x: parser.parse(x.get('date_published', '1970-01-01T00:00:00Z')), 
            reverse=True
        )
        
        # Group articles by month for better organization
        articles_by_month = {}
        current_month = None
        
        for article in all_articles:
            published_date = parser.parse(article.get('date_published', ''))
            month_key = published_date.strftime('%Y-%m')
            month_name = published_date.strftime('%B %Y')
            
            if month_key not in articles_by_month:
                articles_by_month[month_key] = {
                    'name': month_name,
                    'articles': []
                }
            
            articles_by_month[month_key]['articles'].append(article)
        
        # Display articles grouped by month
        for month_key in sorted(articles_by_month.keys(), reverse=True):
            month_data = articles_by_month[month_key]
            html_content += f"""
    <h3 class="month-header">{month_data['name']}</h3>
    <table class="archive-table">
        <thead>
            <tr>
                <th class="sort-icon">Title</th>
                <th class="sort-icon">Source</th>
                <th class="sort-icon article-category">Category</th>
                <th class="sort-icon article-date">Date</th>
            </tr>
        </thead>
        <tbody>
"""
            # Display each article in this month
            for article in month_data['articles']:
                published_date = parser.parse(article.get('date_published', ''))
                formatted_date = published_date.strftime('%Y-%m-%d')
                
                category = article.get('category', 'Uncategorized')
                # Format category name for display
                display_category = category.replace('_', ' ').title()
                
                html_content += f"""
            <tr>
                <td class="article-title-cell"><a href="{article.get('url', '#')}" target="_blank" title="{article.get('title', 'Untitled')}">{article.get('title', 'Untitled')}</a></td>
                <td><span class="article-source">{article.get('source', '')}</span></td>
                <td class="article-category">{display_category}</td>
                <td class="article-date">{formatted_date}</td>
            </tr>"""
            
            html_content += """
        </tbody>
    </table>"""
    
    html_content += """
</body>
</html>
"""
    
    # Write to file
    archive_html_path = os.path.join(feeds_dir, 'archive.html')
    with open(archive_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Generated archive.html with {len(archive_data.get('items', {}))} total articles")
    return archive_html_path

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
        :root {{
            --primary-color: #2563eb;
            --primary-hover: #1d4ed8;
            --background: #f8fafc;
            --card-bg: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: var(--background);
        }}
        
        h1, h2, h3 {{
            color: var(--text-primary);
            font-weight: 600;
        }}
        
        h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        
        .description {{
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }}
        
        .updated {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }}
        
        .nav-links {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .nav-link {{
            display: inline-block;
            padding: 0.5rem 1rem;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            color: var(--primary-color);
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .nav-link:hover {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        .total-count {{
            text-align: center;
            margin-bottom: 2rem;
            font-weight: 500;
            color: var(--text-secondary);
        }}
        
        .category-header {{
            margin-top: 2rem;
            padding: 0.75rem 1rem;
            background-color: var(--card-bg);
            border-radius: 0.375rem;
            border-left: 4px solid var(--primary-color);
            box-shadow: var(--shadow);
            font-size: 1.25rem;
        }}
        
        .articles-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }}
        
        .article-card {{
            background-color: var(--card-bg);
            border-radius: 0.5rem;
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: transform 0.2s, box-shadow 0.2s;
            height: 100%;
            display: flex;
            flex-direction: column;
        }}
        
        .article-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }}
        
        .article-content {{
            padding: 1.25rem;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }}
        
        .article-title {{
            font-size: 1.125rem;
            font-weight: 600;
            margin: 0 0 0.75rem 0;
            line-height: 1.4;
        }}
        
        .article-title a {{
            color: var(--text-primary);
            text-decoration: none;
        }}
        
        .article-title a:hover {{
            color: var(--primary-color);
        }}
        
        .article-meta {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}
        
        .article-source {{
            font-weight: 600;
            color: var(--primary-color);
        }}
        
        .article-summary {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 1.25rem;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            flex-grow: 1;
        }}
        
        .article-link {{
            align-self: flex-start;
            padding: 0.5rem 1rem;
            background-color: var(--primary-color);
            color: white;
            border-radius: 0.375rem;
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            transition: background-color 0.2s;
            margin-top: auto;
        }}
        
        .article-link:hover {{
            background-color: var(--primary-hover);
        }}
        
        .no-articles {{
            padding: 3rem;
            text-align: center;
            background-color: var(--card-bg);
            border-radius: 0.5rem;
            color: var(--text-secondary);
            box-shadow: var(--shadow);
        }}
        
        @media (max-width: 768px) {{
            .articles-grid {{
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AI News Daily Digest</h1>
        <p class="description">Latest AI news and updates from across the web.</p>
        <div class="updated">Last updated: {datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
    </div>
    
    <div class="nav-links">
        <a href="all.rss" class="nav-link">RSS Feed</a>
        <a href="all.atom" class="nav-link">Atom Feed</a>
        <a href="all.json" class="nav-link">JSON Feed</a>
        <a href="archive.html" class="nav-link">View Archive</a>
    </div>
"""

    if not articles_data:
        html_content += """
    <div class="no-articles">
        <h3>No articles found</h3>
        <p>The feed is empty. Articles will appear once they've been scraped from sources.</p>
    </div>
"""
    else:
        # Group articles by category
        articles_by_category = {}
        
        for article in articles_data:
            category = article.get('category', 'Uncategorized')
            if category not in articles_by_category:
                articles_by_category[category] = []
            articles_by_category[category].append(article)
            
        # Sort categories
        sorted_categories = sorted(articles_by_category.keys())
        
        # Display article count
        total_articles = len(articles_data)
        html_content += f"""
    <div class="total-count">
        Showing {total_articles} Latest Articles
    </div>
"""
            
        # Display articles by category
        for category in sorted_categories:
            # Format category name for display
            display_category = category.replace('_', ' ').title()
            
            html_content += f"""
    <h3 class="category-header">{display_category}</h3>
    <div class="articles-grid">
"""
            
            # Display articles for this category
            for article in articles_by_category[category]:
                published_date = parser.parse(article.get('date_published', ''))
                formatted_date = published_date.strftime('%Y-%m-%d')
                
                author = article.get('author', {})
                author_name = author.get('name', '') if author else ''
                
                # Get a truncated summary (if available)
                summary = article.get('summary', '')
                
                html_content += f"""
        <div class="article-card">
            <div class="article-content">
                <h4 class="article-title"><a href="{article.get('url', '#')}" target="_blank">{article.get('title', 'Untitled')}</a></h4>
                <div class="article-meta">
                    <span class="article-source">{article.get('source', '')}</span>
                    {f'· {author_name}' if author_name else ''}
                    · {formatted_date}
                </div>
                <div class="article-summary">
                    {summary}
                </div>
                <a href="{article.get('url', '#')}" class="article-link" target="_blank">Read Article</a>
            </div>
        </div>"""
                
            html_content += """
    </div>"""
    
    html_content += """
</body>
</html>
"""
    
    # Write to file
    index_html_path = os.path.join(feeds_dir, 'index.html')
    with open(index_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Generated index.html with {len(articles_data)} articles")
    return index_html_path

def main():
    """Main function to run the RSS Feed Scraper"""
    parser = argparse.ArgumentParser(description='RSS Feed Scraper for AI topics')
    parser.add_argument('--output-dir', type=str, help='Output directory for feed files')
    parser.add_argument('--ai-only', action='store_true', help='Only include AI-related articles')
    parser.add_argument('--force-refresh', action='store_true', help='Ignore last scrape times and fetch all feeds again')
    
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
    
    # If force refresh is enabled, clear the last scrape times
    if args.force_refresh:
        logger.info("Force refresh enabled. Ignoring last scrape times.")
        scraper.last_scrape_times = {}
    
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
        
        # Update the archive with new articles
        archive = update_archive(output_dir, flattened_articles)
        
        # Generate archive.html with all historical articles
        generate_archive_html(output_dir, archive)
        
        # Generate index.html with the latest articles
        generate_index_html(output_dir, flattened_articles)
        
        logger.info("RSS Feed Scraper completed successfully")
    except Exception as e:
        logger.error(f"Error running RSS Feed Scraper: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())