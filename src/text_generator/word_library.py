import os
import random
import json
from typing import Dict, Any, Union

class WordLibrary:
    def __init__(self, libraries_path: str):
        self.libraries_path = libraries_path
        self.words: Dict[str, Union[Dict, list]] = {}
        self._load_libraries()
    
    def _load_libraries(self):
        """Load all word libraries from JSON files."""
        try:
            # Lista di file che ci aspettiamo di trovare
            expected_files = [
                'subjects.json',
                'verbs.json',
                'objects.json',
                'phrases.json',
                'emojis.json',
                'slang.json'
            ]
            
            for filename in expected_files:
                file_path = os.path.join(self.libraries_path, filename)
                category = filename[:-5]  # remove .json
                
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            self.words[category] = json.load(f)
                    else:
                        print(f"File non trovato: {file_path}")
                        self.words[category] = {} if category in ['verbs', 'phrases', 'emojis'] else []
                except Exception as e:
                    print(f"Errore nel caricamento del file {filename}: {str(e)}")
                    self.words[category] = {} if category in ['verbs', 'phrases', 'emojis'] else []
            
            # Verifica che tutte le categorie necessarie siano presenti
            required_categories = {
                'subjects': [],
                'verbs': {},
                'objects': [],
                'phrases': {},
                'emojis': {},
                'slang': {}
            }
            
            for category, default_value in required_categories.items():
                if category not in self.words:
                    print(f"Categoria mancante: {category}, usando valore di default")
                    self.words[category] = default_value
                    
        except Exception as e:
            print(f"Errore nell'accesso alla directory delle librerie: {str(e)}")
            # Inizializza con valori di default in caso di errore
            self.words = {
                'subjects': ["Someone"],
                'verbs': {
                    'present': ["says"],
                    'past': ["said"],
                    'future': ["will say"],
                    'continuous': ["is saying"]
                },
                'objects': ["something"],
                'phrases': {
                    'intros': ["Hello"],
                    'connectors': ["and"],
                    'endings': ["bye"]
                },
                'emojis': {
                    'positive': ["😊"],
                    'neutral': ["🤔"],
                    'emphasis': ["❗"],
                    'objects': ["📱"],
                    'nature': ["🌸"]
                },
                'slang': {
                    'intros': ["Hey"],
                    'expressions': ["cool"],
                    'endings': ["bye"]
                }
            }
    
    def get_random_word(self, category: str, subcategory: str = None) -> str:
        """Get a random word from a specific category and optional subcategory."""
        try:
            if subcategory:
                if category in self.words and subcategory in self.words[category]:
                    words = self.words[category][subcategory]
                    return random.choice(words) if words else "default"
            else:
                if category in self.words:
                    words = self.words[category]
                    return random.choice(words) if words else "default"
            return "default"
        except Exception as e:
            print(f"Errore nel recupero della parola: {str(e)}")
            return "default"