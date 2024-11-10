from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal

class PreviewWidget(QGroupBox):
    messageAccepted = pyqtSignal(str)  # Signal emitted when a message is accepted

    def __init__(self, text_generator, parent=None):
        super().__init__("Message Preview", parent)
        self.text_generator = text_generator
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Preview area
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Click 'Generate' to see a message preview...")
        layout.addWidget(self.preview_text)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        generate_button = QPushButton("Generate New")
        generate_button.clicked.connect(self.generate_preview)
        controls_layout.addWidget(generate_button)
        
        accept_button = QPushButton("Use This")
        accept_button.clicked.connect(self.accept_message)
        controls_layout.addWidget(accept_button)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)

    def generate_preview(self):
        """Generate a new sample message"""
        message = self.text_generator.generate_message()
        self.preview_text.setText(message)

    def accept_message(self):
        """Emit the signal with the current message"""
        if self.preview_text.toPlainText():
            self.messageAccepted.emit(self.preview_text.toPlainText()) 