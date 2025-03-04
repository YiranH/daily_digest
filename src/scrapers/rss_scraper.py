import os
import json
import logging
import feedparser
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
from feedgen.feed import FeedGenerator
from .base_scraper import BaseScraper

# Configure logging
logger = logging.getLogger(__name__)

# Define timezone information to resolve ambiguous timezone abbreviations
TZINFOS = {
    'EST': -18000,  # UTC-5:00 (Eastern Standard Time)
    'EDT': -14400,  # UTC-4:00 (Eastern Daylight Time)
    'CST': -21600,  # UTC-6:00 (Central Standard Time)
    'CDT': -18000,  # UTC-5:00 (Central Daylight Time)
    'MST': -25200,  # UTC-7:00 (Mountain Standard Time)
    'MDT': -21600,  # UTC-6:00 (Mountain Daylight Time)
    'PST': -28800,  # UTC-8:00 (Pacific Standard Time)
    'PDT': -25200,  # UTC-7:00 (Pacific Daylight Time)
}

class FeedParserDict:
    """A helper class to mimic feedparser's attribute/dictionary access pattern"""
    def __init__(self, data=None):
        self.data = data or {}
        
    def __getattr__(self, name):
        return self.data.get(name, FeedParserDict())
        
    def __getitem__(self, key):
        return self.data.get(key, FeedParserDict())
        
    def get(self, key, default=None):
        return self.data.get(key, default)

class RSSFeedScraper(BaseScraper):
    def __init__(self, db_session=None, feed_urls=None, output_dir='feeds', ai_keywords=[]):
        super().__init__(db_session or None)
        self.feed_urls = feed_urls or {}
        self.output_dir = output_dir
        self.ai_keywords = ai_keywords
        self.timezone = pytz.UTC
        self.last_scrape_times = self._load_last_scrape_times()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def set_ai_keywords(self, keywords):
        self.ai_keywords = [keyword.lower() for keyword in keywords]

    def is_ai_related(self, title, description, content):
        """Check if the content is AI-related based on keywords"""
        text = f"{title} {description} {content}".lower()
        return any(keyword in text for keyword in self.ai_keywords)
        
    def _load_last_scrape_times(self):
        """Load the last scrape times from a JSON file"""
        try:
            if os.path.exists(os.path.join(self.output_dir, 'last_scrape_times.json')):
                with open(os.path.join(self.output_dir, 'last_scrape_times.json'), 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading last scrape times: {str(e)}")
        return {}
        
    def _save_last_scrape_times(self):
        """Save the last scrape times to a JSON file"""
        try:
            with open(os.path.join(self.output_dir, 'last_scrape_times.json'), 'w') as f:
                json.dump(self.last_scrape_times, f)
        except Exception as e:
            logger.error(f"Error saving last scrape times: {str(e)}")
            
    def get_last_scrape_time(self, source):
        """Get the timestamp of the most recent article for a given source"""
        if source in self.last_scrape_times:
            try:
                return parser.parse(self.last_scrape_times[source], tzinfos=TZINFOS)
            except:
                pass
                
        default_time = datetime.now(self.timezone).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=2)
        return default_time

    def fetch_openai_feed(self, url):
        """
        Fetch OpenAI content using multiple fallback methods
        1. Try direct RSS feed access (likely to fail with 403)
        2. Try Google search for recent OpenAI blog posts
        """
        try:
            # First try: direct access
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return feedparser.parse(response.content)
        except Exception as e:
            logger.warning(f"Direct OpenAI feed access failed: {str(e)}")
        
        # Second try: Use Google search to find recent OpenAI blog posts
        try:
            search_url = "https://www.google.com/search?q=site:openai.com/blog"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=15)
            if response.status_code != 200:
                return None
                
            # Parse the search results using html5lib
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Create the feed structure
            feed = FeedParserDict({
                'feed': FeedParserDict({
                    'title': 'OpenAI Blog (via Google)',
                    'link': 'https://openai.com/blog',
                }),
                'entries': []
            })
            
            # Try to find blog links directly
            blog_links = soup.find_all('a', href=lambda href: href and 'openai.com/blog' in href)
            
            processed_links = set()
            for link in blog_links:
                try:
                    href = link.get('href', '')
                    
                    # Clean up the URL if it's a Google redirect
                    if href.startswith('/url?') or 'google.com' in href:
                        link_match = re.search(r'(?:url\?q=|&url=)(https?://[^&]+)', href)
                        if link_match:
                            href = urllib.parse.unquote(link_match.group(1))
                    
                    # Skip if not a blog post or already processed
                    if 'openai.com/blog' not in href or href in processed_links:
                        continue
                        
                    processed_links.add(href)
                    
                    # Get text or try to find a heading nearby
                    text = link.get_text().strip()
                    parent = link.parent
                    heading = parent.find_previous(['h2', 'h3']) or parent.find_next(['h2', 'h3'])
                    title = heading.get_text().strip() if heading else text or "OpenAI Blog Post"
                    
                    entry = FeedParserDict({
                        'title': title,
                        'link': href,
                        'description': f"OpenAI blog post: {title}",
                        'published': datetime.now(self.timezone).strftime('%a, %d %b %Y %H:%M:%S %z'),
                    })
                    
                    feed.data['entries'].append(entry.data)
                except Exception as e:
                    logger.warning(f"Error processing OpenAI blog link: {str(e)}")
            
            return feed
            
        except Exception as e:
            logger.error(f"OpenAI feed fallback failed: {str(e)}")
            return None

    def extract_openai_content(self, entry):
        """Extract content from OpenAI blog entries"""
        content = ''
        
        # Use description if available
        if hasattr(entry, 'description') and entry.description:
            content = entry.description
            
        # Try to get summary or content
        elif hasattr(entry, 'summary') and entry.summary:
            content = entry.summary
        elif hasattr(entry, 'content') and entry.content:
            if isinstance(entry.content, list):
                for content_item in entry.content:
                    if 'value' in content_item:
                        content += content_item['value'] + ' '
            else:
                content = str(entry.content)
                
        # If we have a link but no content, try to scrape the page
        if not content and hasattr(entry, 'link') and entry.link:
            try:
                response = requests.get(entry.link, timeout=10)
                if response.status_code == 200:
                    # Use html5lib instead of lxml
                    soup = BeautifulSoup(response.text, 'html5lib')
                    article = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
                    if article:
                        content = article.get_text(strip=True)
                    else:
                        # Try to get the first few paragraphs
                        paragraphs = soup.find_all('p', limit=5)
                        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            except Exception as e:
                logger.warning(f"Error scraping OpenAI content: {str(e)}")
                
        return content

    def extract_huggingface_content(self, entry):
        """Extract content from Hugging Face blog entries"""
        content = ''
        
        # Check for content in the entry
        if hasattr(entry, 'content') and entry.content:
            if isinstance(entry.content, list):
                for content_item in entry.content:
                    if 'value' in content_item:
                        content += content_item['value'] + ' '
            else:
                content = str(entry.content)
        elif hasattr(entry, 'summary') and entry.summary:
            content = entry.summary
        elif hasattr(entry, 'description') and entry.description:
            content = entry.description
            
        return content

    def extract_google_content(self, entry):
        """Extract content from Google blog entries"""
        content = ''
        
        if hasattr(entry, 'content') and entry.content:
            if isinstance(entry.content, list):
                for content_item in entry.content:
                    if 'value' in content_item:
                        content += content_item['value'] + ' '
            else:
                content = str(entry.content)
        elif hasattr(entry, 'summary') and entry.summary:
            content = entry.summary
        elif hasattr(entry, 'description') and entry.description:
            content = entry.description
            
        return content

    def extract_default_content(self, entry):
        """Default content extraction for generic RSS feeds"""
        content = ''
        
        # Try to get content
        if hasattr(entry, 'content') and entry.content:
            if isinstance(entry.content, list):
                for content_item in entry.content:
                    if 'value' in content_item:
                        content += content_item['value'] + ' '
            else:
                content = str(entry.content)
        # Try to get summary
        elif hasattr(entry, 'summary') and entry.summary:
            content = entry.summary
        # Fall back to description
        elif hasattr(entry, 'description') and entry.description:
            content = entry.description
            
        return content

    def scrape(self):
        """Scrape RSS feeds and generate feed files"""
        all_articles = {}
        current_time = datetime.now(self.timezone)
        
        for source, feed_info in self.feed_urls.items():
            category = feed_info.get('category', 'default')
            if category not in all_articles:
                all_articles[category] = []
                
            try:
                logger.info(f"Scraping RSS feed: {source}")
                last_scrape_time = self.get_last_scrape_time(source)
                
                # Special handling for OpenAI feed
                if source == 'OpenAI':
                    feed = self.fetch_openai_feed(feed_info['url'])
                    if feed is None:
                        logger.error(f"Skipping OpenAI feed due to fetch error")
                        continue
                else:
                    feed = feedparser.parse(feed_info['url'])
                
                latest_pub_time = None
                
                for entry in feed.entries:
                    try:
                        if hasattr(entry, 'published'):
                            published_at = parser.parse(entry.published, tzinfos=TZINFOS)
                        elif hasattr(entry, 'updated'):
                            published_at = parser.parse(entry.updated, tzinfos=TZINFOS)
                        else:
                            published_at = current_time
                        
                        # Keep track of latest publication time for this source
                        if latest_pub_time is None or published_at > latest_pub_time:
                            latest_pub_time = published_at
                        
                        # Skip if already processed
                        if last_scrape_time and published_at <= last_scrape_time:
                            continue

                        title = entry.get('title', '')
                        description = entry.get('description', '')
                        content = ''

                        if 'huggingface.co' in feed_info['url']:
                            content = self.extract_huggingface_content(entry)
                        elif 'blog.google' in feed_info['url']:
                            content = self.extract_google_content(entry)
                        elif source == 'OpenAI':
                            content = self.extract_openai_content(entry)
                        else:
                            content = self.extract_default_content(entry)

                        # Skip if not AI-related when we have keywords set
                        if self.ai_keywords and not self.is_ai_related(title, description, content):
                            continue
                            
                        # Create article structure
                        article = {
                            'title': title,
                            'content': content,
                            'url': entry.link,
                            'source': source,
                            'author': entry.get('author', ''),
                            'published_at': published_at.isoformat(),
                            'description': description
                        }
                        
                        all_articles[category].append(article)
                    except Exception as e:
                        logger.error(f"Error processing entry from {source}: {str(e)}")
                        continue
                
                # Update last scrape time for this source if we have new entries
                if latest_pub_time:
                    self.last_scrape_times[source] = latest_pub_time.isoformat()
                    
            except Exception as e:
                logger.error(f"Error scraping {source}: {str(e)}")
                continue
        
        # Save last scrape times
        self._save_last_scrape_times()
        
        # Generate individual feeds for each category
        for category, articles in all_articles.items():
            if not articles:
                continue
                
            # Sort articles by published date, most recent first
            sorted_articles = sorted(articles, key=lambda x: parser.parse(x['published_at'], tzinfos=TZINFOS), reverse=True)
            
            # Generate RSS feed
            self._generate_rss_feed(category, sorted_articles)
            
            # Generate Atom feed
            self._generate_atom_feed(category, sorted_articles)
            
            # Generate JSON feed
            self._generate_json_feed(category, sorted_articles)
        
        # Generate a combined feed with all articles
        all_entries = []
        for articles in all_articles.values():
            all_entries.extend(articles)
            
        if all_entries:
            self._generate_rss_feed('all', all_entries)
            self._generate_atom_feed('all', all_entries)
            self._generate_json_feed('all', all_entries)
            
        return all_articles
            
    def _generate_rss_feed(self, category, articles):
        """Generate RSS feed for a category"""
        fg = FeedGenerator()
        fg.title(f'AI Daily Digest - {category.replace("_", " ").title()}')
        fg.link(href=f'https://your-github-pages-url/{category}.xml', rel='self')
        fg.description(f'Latest AI news and updates from {category.replace("_", " ")} sources')
        fg.language('en')
        
        for article in sorted(articles, key=lambda x: parser.parse(x['published_at'], tzinfos=TZINFOS), reverse=True):
            fe = fg.add_entry()
            fe.title(article['title'])
            fe.link(href=article['url'])
            fe.description(article['description'] or article['content'][:150] + '...')
            fe.content(content=article['content'], type='html')
            if article['author']:
                fe.author(name=article['author'])
            fe.pubDate(parser.parse(article['published_at'], tzinfos=TZINFOS))
            fe.source(article['source'])
            
        fg.rss_file(os.path.join(self.output_dir, f'{category}.xml'))
        
    def _generate_atom_feed(self, category, articles):
        """Generate Atom feed for a category"""
        fg = FeedGenerator()
        fg.title(f'AI Daily Digest - {category.replace("_", " ").title()}')
        fg.link(href=f'https://your-github-pages-url/{category}.atom', rel='self')
        fg.subtitle(f'Latest AI news and updates from {category.replace("_", " ")} sources')
        fg.language('en')
        fg.id(f'https://your-github-pages-url/{category}')
        
        for article in sorted(articles, key=lambda x: parser.parse(x['published_at'], tzinfos=TZINFOS), reverse=True):
            fe = fg.add_entry()
            fe.title(article['title'])
            fe.link(href=article['url'])
            fe.summary(article['description'] or article['content'][:150] + '...')
            fe.content(content=article['content'], type='html')
            if article['author']:
                fe.author(name=article['author'])
            fe.published(parser.parse(article['published_at'], tzinfos=TZINFOS))
            fe.id(article['url'])
            
        fg.atom_file(os.path.join(self.output_dir, f'{category}.atom'))
        
    def _generate_json_feed(self, category, articles):
        """Generate JSON feed for a category"""
        json_feed = {
            "version": "https://jsonfeed.org/version/1.1",
            "title": f"AI Daily Digest - {category.replace('_', ' ').title()}",
            "home_page_url": "https://your-github-pages-url/",
            "feed_url": f"https://your-github-pages-url/{category}.json",
            "description": f"Latest AI news and updates from {category.replace('_', ' ')} sources",
            "items": []
        }
        
        for article in sorted(articles, key=lambda x: parser.parse(x['published_at'], tzinfos=TZINFOS), reverse=True):
            json_feed["items"].append({
                "id": article['url'],
                "url": article['url'],
                "title": article['title'],
                "content_html": article['content'],
                "summary": article['description'] or article['content'][:150] + '...',
                "date_published": parser.parse(article['published_at'], tzinfos=TZINFOS).isoformat(),
                "author": {"name": article['author']} if article['author'] else None
            })
            
        with open(os.path.join(self.output_dir, f'{category}.json'), 'w', encoding='utf-8') as f:
            json.dump(json_feed, f, ensure_ascii=False, indent=2)