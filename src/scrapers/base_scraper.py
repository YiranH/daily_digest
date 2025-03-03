from abc import ABC, abstractmethod
import logging

logging.basicConfig(level=logging.INFO)

class BaseScraper(ABC):
    def __init__(self, db_session):
        self.db_session = db_session
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    def scrape(self):
        pass
