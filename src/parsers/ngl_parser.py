from .base_parser import BaseSiteParser
import re

class NGLParser(BaseSiteParser):
    def __init__(self, url: str):
        super().__init__(url)
        self.site_name = "ngl"

    def extract_data(self) -> bool:
        if not self.soup:
            return False
            
        try:
            # Trova lo script che contiene le variabili
            scripts = self.soup.find_all('script')
            for script in scripts:
                if script.string and 'var username' in script.string:
                    # Estrai username
                    username_match = re.search(r'var username = "([^"]+)"', script.string)
                    if username_match:
                        self.data['username'] = username_match.group(1)
                    
            return bool(self.data.get('username'))
            
        except Exception as e:
            print(f"Errore nell'estrazione dei dati: {str(e)}")
            return False

    def get_config(self) -> dict:
        return {
            "BASE_URL": "https://ngl.link/api/submit",
            "USERNAME": self.data.get('username', ''),
            "HEADERS": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://ngl.link",
                "Referer": self.url
            }
        }

    @staticmethod
    def get_supported_domains() -> list:
        return ["ngl.link"] 