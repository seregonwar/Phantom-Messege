from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QCheckBox, QSlider
)
from PyQt6.QtCore import Qt

class LanguageStyleWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Language and Style", parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Language selection
        lang_layout = QVBoxLayout()
        lang_label = QLabel("Available Languages:")
        lang_layout.addWidget(lang_label)
        
        self.language_checkboxes = {}
        for lang_code, lang_name in {
            'it': 'Italian 🇮🇹',
            'en': 'English 🇬🇧'
        }.items():
            checkbox = QCheckBox(lang_name)
            self.language_checkboxes[lang_code] = checkbox
            lang_layout.addWidget(checkbox)
        
        layout.addLayout(lang_layout)
        
        # Style selection
        style_layout = QVBoxLayout()
        style_label = QLabel("Message Style:")
        style_layout.addWidget(style_label)
        
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "Standard",
            "Informal",
            "Internet/Gen-Z",
            "Regional"
        ])
        style_layout.addWidget(self.style_combo)
        
        # Dialect selection
        self.dialect_combo = QComboBox()
        self.dialect_combo.addItems([
            "Roman",
            "Milanese",
            "Neapolitan"
        ])
        self.dialect_combo.hide()
        style_layout.addWidget(self.dialect_combo)
        
        layout.addLayout(style_layout)
        
        # Slang frequency
        freq_layout = QVBoxLayout()
        freq_label = QLabel("Slang Frequency:")
        freq_layout.addWidget(freq_label)
        
        self.slang_frequency = QSlider(Qt.Orientation.Horizontal)
        self.slang_frequency.setRange(0, 100)
        self.slang_frequency.setValue(30)
        freq_layout.addWidget(self.slang_frequency)
        
        self.freq_value_label = QLabel("30%")
        freq_layout.addWidget(self.freq_value_label)
        
        layout.addLayout(freq_layout)
        
        self.setLayout(layout)

    def update_dialect_visibility(self, style):
        self.dialect_combo.setVisible(style == "Regional") 