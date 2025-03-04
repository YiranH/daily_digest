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
        # },
        'Google AI': {
            'url': 'https://blog.google/technology/ai/rss/',
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
        'Microsoft Research': {
            'url': 'https://www.microsoft.com/en-us/research/feed',
            'category': 'ai_companies',
        },
        'Berkeley AI Research': {
            'url': 'https://bair.berkeley.edu/blog/feed.xml',
            'category': 'ai_companies',
        },
        'MIT AI News': {
            'url': 'http://news.mit.edu/rss/topic/artificial-intelligence2',
            'category': 'ai_companies',
        },
        
        # AI Tools & Platforms
        'Hugging Face': {
            'url': 'https://huggingface.co/blog/feed.xml',
            'category': 'ai_tools',
        },
        'LangChain': {
            'url': 'https://blog.langchain.dev/rss/',
            'category': 'ai_tools',
        },
        'NVIDIA AI Blog': {
            'url': 'http://feeds.feedburner.com/nvidiablog',
            'category': 'ai_tools',
        },
        'AWS Machine Learning': {
            'url': 'https://aws.amazon.com/blogs/machine-learning/feed',
            'category': 'ai_tools',
        },
        
        # Research & Technical Resources
        # 'arXiv AI': {
        #     'url': 'http://arxiv.org/rss/cs.AI',
        #     'category': 'research',
        # },
        # 'arXiv Machine Learning': {
        #     'url': 'http://arxiv.org/rss/cs.LG',
        #     'category': 'research',
        # },
        # 'arXiv NLP': {
        #     'url': 'http://arxiv.org/rss/cs.CL',
        #     'category': 'research',
        # },
        'Andrej Karpathy': {
            'url': 'https://karpathy.ai/rss.xml',
            'category': 'research',
        },
        'Sebastian Raschka': {
            'url': 'https://sebastianraschka.com/rss_feed.xml',
            'category': 'research',
        },
        'Jay Alammar': {
            'url': 'https://jalammar.github.io/feed.xml',
            'category': 'research',
        },
        'Machine Learning Mastery': {
            'url': 'http://machinelearningmastery.com/blog/feed',
            'category': 'research',
        },
        
        # News & Updates
        'VentureBeat AI': {
            'url': 'https://venturebeat.com/category/ai/feed/',
            'category': 'news',
        },
        'Hacker News': {
            'url': 'https://news.ycombinator.com/rss',
            'category': 'news',
        },
        'Import AI': {
            'url': 'https://jack-clark.net/feed/',
            'category': 'news',
        },
        # 'Science Daily AI': {
        #     'url': 'https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml',
        #     'category': 'news',
        # },
        
        # Communities & Forums
        'Reddit ML': {
            'url': 'https://www.reddit.com/r/MachineLearning/.rss',
            'category': 'community',
        },
        'Reddit AI': {
            'url': 'https://www.reddit.com/r/artificial/.rss',
            'category': 'community',
        },
        # 'Reddit RL': {
        #     'url': 'https://www.reddit.com/r/reinforcementlearning/.rss',
        #     'category': 'community',
        # },
        'Reddit LLM': {
            'url': 'https://www.reddit.com/r/LLMDevs/.rss',
            'category': 'community',
        },
        'Lex Fridman Podcast': {
            'url': 'https://lexfridman.com/feed/podcast/',
            'category': 'community',
        },
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