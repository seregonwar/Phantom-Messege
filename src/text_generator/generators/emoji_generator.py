import random
from ..word_library import WordLibrary

class EmojiGenerator:
    def __init__(self, word_library: WordLibrary):
        self.word_library = word_library
        self.last_used = {'emojis': set()}
        self.max_history = 5

    def get_emoji_set(self, count: int = 1, mood: str = None) -> str:
        """Generate a set of emojis based on mood"""
        categories = ['positive', 'neutral', 'emphasis', 'objects', 'nature']
        
        # Adjust category weights based on mood
        if mood == 'happy':
            weights = [0.4, 0.2, 0.2, 0.1, 0.1]  # More positive emojis
        elif mood == 'serious':
            weights = [0.1, 0.4, 0.2, 0.2, 0.1]  # More neutral emojis
        else:
            weights = [0.2, 0.2, 0.2, 0.2, 0.2]  # Equal distribution
            
        emojis = []
        for _ in range(count):
            category = random.choices(categories, weights=weights)[0]
            available_emojis = set(self.word_library.words['emojis'][category]) - self.last_used['emojis']
            
            if not available_emojis:
                available_emojis = set(self.word_library.words['emojis'][category])
            
            emoji = random.choice(list(available_emojis))
            emojis.append(emoji)
            
            self.last_used['emojis'].add(emoji)
            if len(self.last_used['emojis']) > self.max_history:
                self.last_used['emojis'].pop()
                
        return ' '.join(emojis) 