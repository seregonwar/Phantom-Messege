import random
from ..word_library import WordLibrary

class SlangGenerator:
    def __init__(self, word_library: WordLibrary):
        self.word_library = word_library
        self.last_used = {'slang': set()}
        self.max_history = 5

    def get_slang(self, position: str, language: str, style: str = None, dialect: str = None) -> str:
        """Get appropriate slang based on context"""
        if random.random() < 0.3:  # 30% chance di usare slang
            slang_dict = None
            
            # Regional slang (Italian only)
            if dialect and language == "it":
                regional_dict = self.word_library.words.get('regional_slang', {})
                if dialect in regional_dict:
                    slang_dict = regional_dict[dialect]
            
            # Youth slang (English only)
            elif style and language == "en":
                youth_dict = self.word_library.words.get('youth_slang', {})
                if style in youth_dict:
                    slang_dict = youth_dict[style]
            
            # Default slang
            if not slang_dict:
                slang_dict = self.word_library.words.get('slang', {})
            
            if position in slang_dict:
                available_slang = set(slang_dict[position]) - self.last_used['slang']
                if not available_slang:
                    available_slang = set(slang_dict[position])
                slang = random.choice(list(available_slang))
                
                self.last_used['slang'].add(slang)
                if len(self.last_used['slang']) > self.max_history:
                    self.last_used['slang'].pop()
                    
                return slang
        return "" 