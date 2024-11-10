from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel

class ProfileWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("NGL Profile", parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # URL input layout
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://ngl.link/username")
        url_layout.addWidget(self.url_input)
        
        self.load_profile_button = QPushButton("Load")
        url_layout.addWidget(self.load_profile_button)
        
        layout.addLayout(url_layout)
        
        # Profile info
        self.profile_info = QLabel("No profile loaded")
        layout.addWidget(self.profile_info)
        
        self.setLayout(layout) 