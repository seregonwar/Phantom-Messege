from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QSpinBox, QLabel, QComboBox
)
from PyQt6.QtCore import pyqtSignal

class EnhancedPreviewWidget(QGroupBox):
    messageAccepted = pyqtSignal(str)
    previewGenerated = pyqtSignal(str)

    def __init__(self, text_generator, parent=None):
        super().__init__("Message Preview", parent)
        self.text_generator = text_generator
        self.preview_history = []
        self.current_preview_index = -1
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Preview area
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Click 'Generate' to see a message preview...")
        layout.addWidget(self.preview_text)
        
        # Generation settings
        settings_layout = QHBoxLayout()
        
        # Number of sentences
        sentences_layout = QHBoxLayout()
        sentences_layout.addWidget(QLabel("Sentences:"))
        self.sentences_spin = QSpinBox()
        self.sentences_spin.setRange(1, 5)
        self.sentences_spin.setValue(2)
        sentences_layout.addWidget(self.sentences_spin)
        settings_layout.addLayout(sentences_layout)
        
        # Message style
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Style:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Random", "Formal", "Informal", "Question", "Statement"])
        style_layout.addWidget(self.style_combo)
        settings_layout.addLayout(style_layout)
        
        layout.addLayout(settings_layout)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Navigation buttons
        self.prev_button = QPushButton("◀ Previous")
        self.prev_button.clicked.connect(self.show_previous)
        self.prev_button.setEnabled(False)
        controls_layout.addWidget(self.prev_button)
        
        generate_button = QPushButton("🔄 Generate New")
        generate_button.clicked.connect(self.generate_preview)
        controls_layout.addWidget(generate_button)
        
        self.next_button = QPushButton("Next ▶")
        self.next_button.clicked.connect(self.show_next)
        self.next_button.setEnabled(False)
        controls_layout.addWidget(self.next_button)
        
        accept_button = QPushButton("✓ Use This")
        accept_button.clicked.connect(self.accept_message)
        controls_layout.addWidget(accept_button)
        
        layout.addLayout(controls_layout)
        
        # Suggestions
        self.suggestion_label = QLabel("")
        layout.addWidget(self.suggestion_label)
        
        self.setLayout(layout)

    def generate_preview(self):
        """Generates a new example message"""
        style = self.style_combo.currentText().lower()
        num_sentences = self.sentences_spin.value()
        
        if style == "random":
            message = self.text_generator.generate_message(
                min_sentences=num_sentences,
                max_sentences=num_sentences
            )
        else:
            message = self.text_generator.generate_message_with_style(
                style=style,
                num_sentences=num_sentences
            )
        
        # Add to history
        self.preview_history.append(message)
        self.current_preview_index = len(self.preview_history) - 1
        
        # Update UI
        self.preview_text.setText(message)
        self.update_navigation_buttons()
        self.analyze_message(message)
        
        self.previewGenerated.emit(message)

    def show_previous(self):
        """Shows the previous message in history"""
        if self.current_preview_index > 0:
            self.current_preview_index -= 1
            message = self.preview_history[self.current_preview_index]
            self.preview_text.setText(message)
            self.update_navigation_buttons()
            self.analyze_message(message)

    def show_next(self):
        """Shows the next message in history"""
        if self.current_preview_index < len(self.preview_history) - 1:
            self.current_preview_index += 1
            message = self.preview_history[self.current_preview_index]
            self.preview_text.setText(message)
            self.update_navigation_buttons()
            self.analyze_message(message)

    def update_navigation_buttons(self):
        """Updates the navigation buttons state"""
        self.prev_button.setEnabled(self.current_preview_index > 0)
        self.next_button.setEnabled(
            self.current_preview_index < len(self.preview_history) - 1
        )

    def analyze_message(self, message: str):
        """Analyzes the message and provides suggestions"""
        suggestions = []
        
        # Length
        length = len(message)
        if length < 50:
            suggestions.append("The message is a bit short")
        elif length > 200:
            suggestions.append("The message might be too long")
            
        # Emoji
        primary_lang = self.text_generator.languages[0]
        emoji_count = sum(
            1 for c in message 
            for emojis in self.text_generator.word_libraries[primary_lang].words.get('emojis', {}).values() 
            if c in emojis
        )
        
        if emoji_count == 0:
            suggestions.append("You might want to add some emojis")
        elif emoji_count > 5:
            suggestions.append("There are many emojis, consider reducing them")
            
        # Show suggestions
        if suggestions:
            self.suggestion_label.setText("Suggestions: " + " | ".join(suggestions))
        else:
            self.suggestion_label.setText("The message looks great! 👍")

    def accept_message(self):
        """Emits the signal with the current message"""
        if self.preview_text.toPlainText():
            self.messageAccepted.emit(self.preview_text.toPlainText())