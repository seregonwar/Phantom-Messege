from bs4 import BeautifulSoup
import requests
import re
import json

class NGLPageParser:
    def __init__(self, url):
        self.url = url
        self.soup = None
        self.data = {}
    
    def fetch_page(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            self.soup = BeautifulSoup(response.text, 'html.parser')
            return True
        except Exception as e:
            print(f"Errore nel recupero della pagina: {str(e)}")
            return False
    
    def extract_data(self):
        if not self.soup:
            return False
            
        try:
            # Trova lo script che contiene le variabili
            scripts = self.soup.find_all('script')
            for script in scripts:
                if script.string and 'var username' in script.string:
                    # Estrai le variabili dallo script
                    script_text = script.string
                    
                    # Estrai username
                    username_match = re.search(r'var username = "([^"]+)"', script_text)
                    if username_match:
                        self.data['username'] = username_match.group(1)
                    
                    # Estrai uid
                    uid_match = re.search(r'var uid = "([^"]+)"', script_text)
                    if uid_match:
                        self.data['uid'] = uid_match.group(1)
                    
                    # Estrai altre variabili
                    self.data['gameSlug'] = ""  # Default value
                    self.data['gameId'] = "default"
                    
            # Estrai l'URL di riferimento
            self.data['referer'] = self.url
            
            return True
            
        except Exception as e:
            print(f"Errore nell'estrazione dei dati: {str(e)}")
            return False
    
    def get_config(self):
        return {
            "BASE_URL": "https://ngl.link/api/submit",
            "USERNAME": self.data.get('username', ''),
            "HEADERS": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://ngl.link",
                "Referer": self.data.get('referer', '')
            },
            "MIN_DELAY": 1.0,
            "MAX_DELAY": 3.0
        } 