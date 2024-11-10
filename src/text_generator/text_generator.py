import random
import os
from typing import List, Optional
from .word_library import WordLibrary
from .generators import SentenceGenerator, SlangGenerator, EmojiGenerator

class TextGenerator:
    def __init__(self, languages: List[str] = None, libraries_path: str = None):
        if libraries_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            libraries_path = os.path.join(current_dir, "libraries")
        
        self.libraries_path = libraries_path
        self.languages = languages or ["en"]
        self.word_libraries = {}
        
        # Carica prima la libreria base
        base_path = os.path.join(libraries_path, "base")
        self.base_library = WordLibrary(base_path)
        
        # Carica le librerie per ogni lingua
        for lang in self.languages:
            lang_path = os.path.join(libraries_path, lang)
            if os.path.exists(lang_path):
                self.word_libraries[lang] = WordLibrary(lang_path)
            else:
                # Usa la libreria base come fallback
                self.word_libraries[lang] = self.base_library
        
        # Inizializza i generatori specializzati con la libreria della prima lingua
        primary_lang = self.languages[0]
        self.sentence_generator = SentenceGenerator(self.word_libraries[primary_lang])
        self.slang_generator = SlangGenerator(self.word_libraries[primary_lang])
        self.emoji_generator = EmojiGenerator(self.word_libraries[primary_lang])
        
        self.current_language = None
        self.slang_style = None
        self.regional_dialect = None

    def set_languages(self, languages: List[str]):
        """Update available languages and reinitialize generators"""
        self.languages = languages
        self.word_libraries = {}
        for lang in self.languages:
            lang_path = os.path.join(self.libraries_path, lang)
            if not os.path.exists(lang_path):
                lang_path = self.libraries_path  # Fallback alla directory principale
            self.word_libraries[lang] = WordLibrary(lang_path)
            
        # Aggiorna i generatori con la nuova libreria
        primary_lang = self.languages[0]
        self.sentence_generator = SentenceGenerator(self.word_libraries[primary_lang])
        self.slang_generator = SlangGenerator(self.word_libraries[primary_lang])
        self.emoji_generator = EmojiGenerator(self.word_libraries[primary_lang])

    def _get_random_language(self) -> str:
        """Select a random language from available ones"""
        return random.choice(self.languages)

    def generate_sentence(self, style: str = None) -> str:
        """Generate a varied sentence with emojis and slang"""
        try:
            self.current_language = self._get_random_language()
            
            # Gestione speciale per stile regionale
            if style == "regionale" and self.regional_dialect:
                # Carica lo slang regionale specifico
                regional_dict = self.word_libraries[self.current_language].words.get('regional_slang', {})
                if self.regional_dialect.lower() in regional_dict:
                    dialect_data = regional_dict[self.regional_dialect.lower()]
                    
                    # Costruisci la frase con elementi dialettali
                    intro = random.choice(dialect_data.get('intros', []))
                    expression = random.choice(dialect_data.get('expressions', []))
                    ending = random.choice(dialect_data.get('endings', []))
                    
                    # Genera la frase base
                    base_sentence = self.sentence_generator.generate_statement(self.current_language)
                    
                    # Combina gli elementi
                    sentence = f"{intro}, {base_sentence} {expression} {ending}"
                    
                    # Aggiungi emoji casuali
                    if random.random() < 0.4:
                        sentence = f"{self.emoji_generator.get_emoji_set(1, 'happy')} {sentence}"
                    if random.random() < 0.6:
                        sentence = f"{sentence} {self.emoji_generator.get_emoji_set(2)}"
                    
                    return sentence
            
            # Comportamento normale per altri stili
            intro_slang = self.slang_generator.get_slang(
                'intros', 
                self.current_language, 
                self.slang_style, 
                self.regional_dialect
            )
            
            # Generate base sentence based on style
            if style == "question":
                base_sentence = self.sentence_generator.generate_question(self.current_language)
            else:
                base_sentence = self.sentence_generator.generate_statement(self.current_language)
            
            # Add slang expressions
            expression_slang = self.slang_generator.get_slang(
                'expressions', 
                self.current_language, 
                self.slang_style, 
                self.regional_dialect
            )
            ending_slang = self.slang_generator.get_slang(
                'endings', 
                self.current_language, 
                self.slang_style, 
                self.regional_dialect
            )
            
            # Construct final sentence
            parts = []
            if intro_slang:
                parts.append(f"{intro_slang},")
            parts.append(base_sentence)
            if expression_slang:
                parts.append(f", {expression_slang}")
            if ending_slang:
                parts.append(ending_slang)
                
            sentence = " ".join(parts)
            
            # Add emojis
            if random.random() < 0.4:  # 40% chance for starting emoji
                sentence = f"{self.emoji_generator.get_emoji_set(1, 'happy')} {sentence}"
            if random.random() < 0.6:  # 60% chance for ending emoji
                emoji_count = random.choices([1, 2, 3], weights=[0.5, 0.3, 0.2])[0]
                sentence = f"{sentence} {self.emoji_generator.get_emoji_set(emoji_count)}"
                
            return sentence
        except Exception as e:
            print(f"Errore nella generazione della frase: {e}")
            return "Mi dispiace, c'è stato un errore nella generazione del messaggio."

    def generate_message(self, min_sentences: int = 1, max_sentences: int = 3) -> str:
        """Generate a message with varied sentence count and structure"""
        try:
            weights = [0.5, 0.3, 0.2][:max_sentences-min_sentences+1]
            num_sentences = random.choices(
                range(min_sentences, max_sentences + 1),
                weights=weights
            )[0]
            
            sentences = []
            for _ in range(num_sentences):
                style = random.choice(["statement", "question"])
                sentences.append(self.generate_sentence(style))
                
            return ' '.join(sentences)
        except Exception as e:
            print(f"Errore nella generazione del messaggio: {e}")
            return "Mi dispiace, c'è stato un errore nella generazione del messaggio."

    def generate_message_with_style(self, style: str, num_sentences: int) -> str:
        """Generate a message with specific style"""
        try:
            return ' '.join(
                self.generate_sentence(style.lower()) 
                for _ in range(num_sentences)
            )
        except Exception as e:
            print(f"Errore nella generazione del messaggio con stile: {e}")
            return "Mi dispiace, c'è stato un errore nella generazione del messaggio."