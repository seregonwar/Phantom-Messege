import random
from typing import Optional
from ..word_library import WordLibrary

class SentenceGenerator:
    def __init__(self, word_library: WordLibrary):
        self.word_library = word_library
        self.last_used = {
            'subjects': set(),
            'verbs': set(),
            'objects': set(),
            'structures': set()
        }
        self.max_history = 5

    def _get_verb(self, tense: Optional[str] = None) -> str:
        """Get a random verb in a specific tense"""
        if not tense:
            tense = random.choice(['present', 'past', 'future', 'continuous'])
        return self._get_unique_word('verbs', tense)

    def _get_unique_word(self, category: str, subcategory: str = None) -> str:
        """Get a word avoiding recent ones"""
        if subcategory:
            available_words = set(self.word_library.words[category][subcategory]) - self.last_used[category]
        else:
            available_words = set(self.word_library.words[category]) - self.last_used[category]
            
        if not available_words:
            available_words = set(self.word_library.words[category])
            
        word = random.choice(list(available_words))
        
        self.last_used[category].add(word)
        if len(self.last_used[category]) > self.max_history:
            self.last_used[category].pop()
            
        return word

    def generate_question(self, language: str) -> str:
        """Generate a question based on language"""
        templates = {
            "en": [
                "What do you think about {subject} that {verb} {object}?",
                "Have you noticed how {subject} {verb} {object}?",
                "Isn't it amazing when {subject} {verb} {object}?",
                "Don't you love how {subject} {verb} {object}?"
            ],
            "it": [
                "Cosa pensi di {subject} che {verb} {object}?",
                "Hai notato come {subject} {verb} {object}?",
                "Non è incredibile quando {subject} {verb} {object}?",
                "Non ti piace come {subject} {verb} {object}?"
            ]
        }
        
        template = random.choice(templates.get(language, templates["en"]))
        return template.format(
            subject=self._get_unique_word('subjects'),
            verb=self._get_verb(),
            object=self._get_unique_word('objects')
        )

    def generate_statement(self, language: str) -> str:
        """Generate a statement based on language"""
        templates = {
            "en": [
                "I believe {subject} {verb} {object}",
                "Sometimes {subject} just {verb} {object}",
                "The way {subject} {verb} {object} is incredible",
                "{subject} always {verb} {object}"
            ],
            "it": [
                "Credo che {subject} {verb} {object}",
                "A volte {subject} semplicemente {verb} {object}",
                "Il modo in cui {subject} {verb} {object} è incredibile",
                "{subject} sempre {verb} {object}"
            ]
        }
        
        template = random.choice(templates.get(language, templates["en"]))
        return template.format(
            subject=self._get_unique_word('subjects'),
            verb=self._get_verb(),
            object=self._get_unique_word('objects')
        ) 