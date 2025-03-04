import os


class Config:    
    # OpenAI API credentials
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Feed URLs configuration
    FEEDS = {
        # AI Companies & Research Labs
        # 'OpenAI': {
        #     'url': 'https://openai.com/blog/rss.xml',
        #     'category': 'ai_companies',
        # }, # can't get the feed
            'Google AI': {
                'url': 'https://blog.google/technology/ai/rss/',
                'category': 'ai_companies',
            },
            'Google Developers': {
                'url': 'https://blog.google/technology/developers/rss/',
                'category': 'ai_companies',
            },
            'Google Research': {
                'url': 'https://blog.google/technology/research/rss/',
                'category': 'ai_companies',
            },
            'Google Research': {
                'url': 'https://research.google/blog/rss/',
                'category': 'ai_companies',
            },
            'DeepMind': {
                'url': 'https://deepmind.google/blog/rss.xml',
                'category': 'ai_companies',
            },
            'LangChain': {
                'url': 'https://blog.langchain.dev/rss/',
                'category': 'ai_companies',
            },
            'Microsoft AI': {
                'url': 'https://deepmind.com/blog/feed/basic/',
                'category': 'ai_companies',
            },    
            # AI Tools & Platforms
            'Hugging Face': {
                'url': 'https://huggingface.co/blog/feed.xml',
                'category': 'ai_tools',
            },

        # # News & Updates
        # 'The Verge': {
        #     'url': 'https://www.theverge.com/rss/index.xml',
        #     'category': 'news',
        # },
        # 'TechCrunch': {
        #     'url': 'https://techcrunch.com/feed/',
        #     'category': 'news',
        # },
        # 'VentureBeat AI': {
        #     'url': 'https://venturebeat.com/category/ai/feed/',
        #     'category': 'news',
        # },
    }
    
    # AI-related keywords for filtering articles
    AI_KEYWORDS = [
        'ai', 'artificial intelligence', 'machine learning', 'deep learning',
        'neural network', 'gpt', 'llm', 'large language model', 'chatgpt',
        'generative ai', 'openai', 'anthropic', 'claude', 'gemini',
        'transformer', 'foundation model', 'diffusion model', 'stable diffusion',
        'midjourney', 'dall-e', 'embedding', 'fine-tuning', 'prompt engineering'
    ]
    
    # Output directory for feed files
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'feeds')
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories for the application"""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)