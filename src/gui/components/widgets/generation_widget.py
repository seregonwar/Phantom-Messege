from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QCheckBox, QSlider
from PyQt6.QtCore import Qt

class GenerationWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Generation", parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Message count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Number of messages:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 1000)
        self.count_spin.setValue(1)
        count_layout.addWidget(self.count_spin)
        layout.addLayout(count_layout)
        
        # Emoji options
        self.emoji_enabled = QCheckBox("Include emojis")
        self.emoji_enabled.setChecked(True)
        layout.addWidget(self.emoji_enabled)
        
        # Message length
        length_layout = QVBoxLayout()
        length_layout.addWidget(QLabel("Message length:"))
        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setRange(1, 3)  # 1=short, 2=medium, 3=long
        self.length_slider.setValue(2)
        length_layout.addWidget(self.length_slider)
        
        length_labels = QHBoxLayout()
        length_labels.addWidget(QLabel("Short"))
        length_labels.addStretch()
        length_labels.addWidget(QLabel("Medium"))
        length_labels.addStretch()
        length_labels.addWidget(QLabel("Long"))
        length_layout.addLayout(length_labels)
        
        layout.addLayout(length_layout)
        
        self.setLayout(layout) 