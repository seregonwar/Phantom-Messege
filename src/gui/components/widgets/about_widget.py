from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QGroupBox, QHBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont

class AboutWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.click_count = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # App Info
        info_group = QGroupBox("Informazioni Applicazione")
        info_layout = QVBoxLayout()
        
        app_name = QLabel("Message Sender")
        app_name.setFont(QFont("", 16, QFont.Weight.Bold))
        info_layout.addWidget(app_name, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.version_label = QLabel("Versione 1.0.0")
        self.version_label.setObjectName("versionLabel")
        self.version_label.mousePressEvent = self._handle_version_click
        self.version_label.setCursor(Qt.CursorShape.PointingHandCursor)
        info_layout.addWidget(self.version_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Social Links
        links_group = QGroupBox("Collegamenti")
        links_layout = QVBoxLayout()
        
        social_links = [
            ("Ko-fi", "https://ko-fi.com/seregon", "☕"),
            ("GitHub", "https://github.com/seregonwar", "💻"),
            ("Twitter/X", "https://x.com/SeregonWar", "🐦"),
            ("Reddit", "https://www.reddit.com/user/S3R3GON/", "🤖")
        ]
        
        for name, url, icon in social_links:
            btn = QPushButton(f"{icon} {name}")
            btn.setObjectName("socialButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, u=url: QDesktopServices.openUrl(QUrl(u)))
            links_layout.addWidget(btn)
        
        links_group.setLayout(links_layout)
        layout.addWidget(links_group)

        # Credits
        credits_group = QGroupBox("Crediti")
        credits_layout = QVBoxLayout()
        
        credits_text = QLabel(
            "Sviluppato da Seregon\n"
            "Con ❤️ e tanto ☕\n\n"
            "© 2024 Seregon. Tutti i diritti riservati."
        )
        credits_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_layout.addWidget(credits_text)
        
        credits_group.setLayout(credits_layout)
        layout.addWidget(credits_group)

        # Easter Egg Dialog
        self.easter_egg_dialog = None

        self.setLayout(layout)
        self.setStyleSheet(self._get_stylesheet())

    def _handle_version_click(self, event):
        """Gestisce i click sulla versione per l'easter egg"""
        self.click_count += 1
        if self.click_count >= 5:
            self.click_count = 0
            self._show_easter_egg()

    def _show_easter_egg(self):
        """Mostra l'easter egg"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Terminal")
        layout = QVBoxLayout()
        
        ascii_art = """
    _________________________________________________
   /                                                 \\
  |    _________________________________________     |
  |   |                                         |    |
  |   |  C:\\> HACK THE PLANET                   |    |
  |   |                                         |    |
  |   |  SYSTEM COMPROMISED                     |    |
  |   |  ACCESSING MAINFRAME...                 |    |
  |   |  DOWNLOADING SECRET FILES...            |    |
  |   |                                         |    |
  |   |  CONGRATULATIONS! YOU FOUND THE         |    |
  |   |  SUPER SECRET EASTER EGG!               |    |
  |   |                                         |    |
  |   |  NOW GO FORTH AND CODE, YOUNG PADAWAN   |    |
  |   |_________________________________________|    |
  |                                                  |
   \\_________________________________________________/
          \\___________________________________/
       ___________________________________________
    _-'    .-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  --- `-_
 _-'.-.-. .---.-.-.-.-.-.-.-.-.-.-.-.-.-.-.--.  .-.-.`-_
:-------------------------------------------------------------------------:
`---._.-------------------------------------------------------------._.---'
        """
        
        terminal = QLabel(ascii_art)
        terminal.setStyleSheet("""
            QLabel {
                font-family: monospace;
                color: #00ff00;
                background-color: #000000;
                padding: 20px;
            }
        """)
        layout.addWidget(terminal)
        
        dialog.setLayout(layout)
        dialog.setFixedSize(600, 500)
        dialog.exec()

    def _get_stylesheet(self) -> str:
        return """
            QGroupBox {
                font-weight: bold;
                padding: 15px;
                margin-top: 10px;
            }
            
            #socialButton {
                text-align: left;
                padding: 12px 20px;
                border: none;
                border-radius: 8px;
                margin: 2px 0;
                font-size: 14px;
                background-color: transparent;
                color: #ffffff;
            }
            
            #socialButton:hover {
                background-color: #333333;
            }
            
            #versionLabel {
                color: #888888;
                text-decoration: none;
            }
            
            #versionLabel:hover {
                color: #007acc;
            }
        """ 