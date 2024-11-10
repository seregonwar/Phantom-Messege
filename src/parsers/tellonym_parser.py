from .base_parser import BaseSiteParser
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import random
import time
from typing import Optional
from datetime import datetime, timedelta

class TellonymParser(BaseSiteParser):
    def __init__(self, url: str, proxy: Optional[dict] = None):
        super().__init__(url)
        self.site_name = "tellonym"
        self.proxy = proxy
        self.driver = None
        
        # Lista estesa di User-Agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
        ]
        
        self._setup_driver()

    def _setup_driver(self):
        """Configura il driver Selenium"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Esegui in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={random.choice(self.user_agents)}')
        
        if self.proxy:
            chrome_options.add_argument(f'--proxy-server={self.proxy}')
        
        self.driver = webdriver.Chrome(options=chrome_options)

    def fetch_page(self) -> bool:
        """Recupera la pagina usando Selenium"""
        try:
            self.driver.get(self.url)
            
            # Attendi che la pagina sia caricata
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Aggiungi un delay casuale per sembrare più umani
            time.sleep(random.uniform(2, 4))
            
            # Verifica se siamo stati bloccati
            if "Access denied" in self.driver.page_source or "Please verify you are human" in self.driver.page_source:
                print("Rilevato captcha o verifica anti-bot")
                return False
                
            self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            return True
            
        except Exception as e:
            print(f"Errore nel recupero della pagina: {str(e)}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

    def extract_data(self) -> bool:
        """Estrae i dati dalla pagina Tellonym"""
        if not self.soup:
            return False
            
        try:
            # Estrai username dall'URL
            username = self.url.split('/')[-1]
            if not username:
                return False
                
            # Cerca il div principale del profilo
            profile_div = self.soup.find('div', {'data-radium': 'true'})
            if not profile_div:
                return False
                
            # Estrai dati dal meta tag description
            meta_desc = self.soup.find('meta', {'name': 'description'})
            if meta_desc:
                self.data['description'] = meta_desc.get('content', '')
            
            # Estrai dati dal meta tag og:title
            og_title = self.soup.find('meta', {'property': 'og:title'})
            if og_title:
                title = og_title.get('content', '')
                # Pulisci il titolo dalle virgolette
                self.data['title'] = title.replace("'", "").replace("@", "")
            
            # Estrai statistiche
            stats_div = self.soup.find('div', {'class': 'css-1dbjc4n'})
            if stats_div:
                # Cerca i contatori (followers, tells, seguiti)
                counters = stats_div.find_all('div', {'stylekeepercontext': '[object Object]'})
                for counter in counters:
                    if counter.text.isdigit():
                        value = int(counter.text)
                        # Aggiungi alla struttura dati
                        if 'stats' not in self.data:
                            self.data['stats'] = {}
                        self.data['stats']['tells'] = value
                        break

            # Imposta i dati necessari
            self.data['username'] = username
            self.data['platform'] = 'tellonym'
            
            return bool(self.data.get('username'))
            
        except Exception as e:
            print(f"Errore nell'estrazione dei dati Tellonym: {str(e)}")
            return False

    def get_config(self) -> dict:
        """Restituisce la configurazione per l'invio dei messaggi"""
        return {
            "BASE_URL": "https://tellonym.me/api/tells/create",
            "USERNAME": self.data.get('username', ''),
            "HEADERS": {
                "User-Agent": random.choice(self.user_agents),
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": "https://tellonym.me",
                "Referer": self.url,
                "tellonym-client": "web:0.51.1",
                "X-Requested-With": "XMLHttpRequest"
            },
            "PAYLOAD": {
                "tell": "",  # Il messaggio verrà inserito qui
                "userId": "",  # L'ID utente verrà estratto dalla pagina
                "isInstagramInvite": False,
                "isTwitterInvite": False
            }
        }

    @staticmethod
    def get_supported_domains() -> list:
        return ["tellonym.me"]

    def __del__(self):
        """Cleanup del driver"""
        if self.driver:
            self.driver.quit()