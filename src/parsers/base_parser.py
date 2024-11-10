from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup

class BaseSiteParser(ABC):
    def __init__(self, url: str):
        self.url = url
        self.soup = None
        self.data = {}
        self.site_name = "generic"

    def fetch_page(self) -> bool:
        """Fetches the web page"""
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            self.soup = BeautifulSoup(response.text, 'html.parser')
            return True
        except Exception as e:
            print(f"Error fetching the page: {str(e)}")
            return False

    @abstractmethod
    def extract_data(self) -> bool:
        """Extracts data from the page"""
        pass

    @abstractmethod
    def get_config(self) -> dict:
        """Returns the configuration for message sending"""
        pass

    @staticmethod
    def get_supported_domains() -> list:
        """Returns the list of supported domains"""
        return []

    @staticmethod
    def can_handle_url(url: str) -> bool:
        """Checks if the URL can be handled by this parser"""
        return any(domain in url for domain in BaseSiteParser.get_supported_domains()) 