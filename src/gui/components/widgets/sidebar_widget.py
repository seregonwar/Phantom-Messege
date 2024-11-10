from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, 
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QIcon, QFont, QPainter, QColor, QPixmap, QDesktopServices
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray
from ...icons import ICONS

class NavButton(QPushButton):
    """Custom navigation button"""
    def __init__(self, text: str, icon_path: str, is_active: bool = False):
        super().__init__()
        self.setText(text)
        self.icon_path = icon_path
        self.setIconSize(QSize(24, 24))
        self.setCheckable(True)
        self.setChecked(is_active)
        self.setMinimumHeight(45)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("navButton")
        self._update_colors("#ffffff")  # Default color for dark theme

    def _update_colors(self, color: str):
        """Update the icon and text color"""
        if not self.icon_path:
            return
            
        try:
            with open(self.icon_path, 'r') as f:
                svg_content = f.read()
                
            # Replace the color in the SVG
            svg_content = svg_content.replace('stroke="currentColor"', f'stroke="{color}"')
            
            # Convert the SVG content to QByteArray
            svg_bytes = QByteArray(svg_content.encode('utf-8'))
            
            # Create an SVG renderer
            renderer = QSvgRenderer(svg_bytes)
            
            # Create an image to render the SVG
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            # Render the SVG on the pixmap
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            # Set the icon
            self.setIcon(QIcon(pixmap))
            
            # Set the text color
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 12px 20px;
                    border: none;
                    border-radius: 8px;
                    margin: 2px 0;
                    font-size: 14px;
                    background-color: transparent;
                    color: {color};
                }}
                
                QPushButton:hover {{
                    background-color: #333333;
                }}
                
                QPushButton:checked {{
                    background-color: #007acc;
                    color: #ffffff;
                }}
            """)
            
        except Exception as e:
            print(f"Error updating the icon: {e}")

    def update_theme(self, is_dark: bool):
        """Update the colors based on the theme"""
        color = "#ffffff" if is_dark else "#000000"
        self._update_colors(color)

class SidebarWidget(QWidget):
    pageChanged = pyqtSignal(str)
    click_count = 0  # Counter for avatar clicks

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = "messages"
        self.nav_buttons = {}
        self.setup_ui()
        self.setObjectName("sidebar")

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Logo and title
        title_frame = QFrame()
        title_frame.setObjectName("titleFrame")
        title_layout = QVBoxLayout(title_frame)
        
        # App title
        app_title = QLabel("Phantom\nMessenger")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        app_title.setFont(font)
        app_title.setObjectName("appTitle")
        title_layout.addWidget(app_title)
        
        layout.addWidget(title_frame)

        # Separator
        layout.addWidget(self._create_separator())

        # Navigation buttons
        nav_buttons = [
            ("messages", "Messages", ICONS['messages']),
            ("stats", "Statistics", ICONS['stats']),
            ("settings", "Settings", ICONS['settings']),
            ("help", "Help", ICONS['help'])
        ]

        for id, text, icon in nav_buttons:
            btn = NavButton(text, icon, is_active=(id == self.current_page))
            btn.clicked.connect(lambda checked, x=id: self._handle_nav_click(x))
            self.nav_buttons[id] = btn
            layout.addWidget(btn)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(spacer)

        # Status info
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.setStyleSheet(self._get_stylesheet())

    def _handle_avatar_click(self, event):
        """Handle avatar clicks"""
        self.click_count += 1
        if self.click_count >= 5:
            self.click_count = 0
            self._show_easter_egg()

    def _show_easter_egg(self):
        """Show the easter egg"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Terminal")
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # Remove the title bar
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
                border: 2px solid #00ff00;
                border-radius: 10px;
            }
        """)
        layout.addWidget(terminal)
        
        # Add a button to close
        close_button = QPushButton("CLOSE TERMINAL")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: #00ff00;
                border: 2px solid #00ff00;
                padding: 10px;
                font-family: monospace;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #003300;
            }
        """)
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.setStyleSheet("background-color: #000000;")
        dialog.exec()

    def update_theme(self, is_dark: bool):
        """Update the colors of all buttons when the theme changes"""
        for btn in self.nav_buttons.values():
            btn.update_theme(is_dark)

    def _create_separator(self) -> QFrame:
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("separator")
        return separator

    def _handle_nav_click(self, page_id: str):
        # Deselect all buttons except the clicked one
        for id, btn in self.nav_buttons.items():
            btn.setChecked(id == page_id)
        
        self.current_page = page_id
        self.pageChanged.emit(page_id)

    def update_status(self, text: str):
        self.status_label.setText(text)

    def _get_stylesheet(self) -> str:
        return """
            #sidebar {
                background-color: #1e1e1e;
                min-width: 200px;
                max-width: 200px;
                padding: 10px;
                border-right: 1px solid #333333;
            }
            
            #titleFrame {
                padding: 20px;
                margin-bottom: 10px;
            }
            
            #appTitle {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
            }
            
            #navButton {
                text-align: left;
                padding: 12px 20px;
                border: none;
                border-radius: 8px;
                margin: 2px 0;
                font-size: 14px;
                background-color: transparent;
                color: #ffffff;
            }
            
            #navButton:hover {
                background-color: #333333;
            }
            
            #navButton:checked {
                background-color: #007acc;
                color: #ffffff;
            }
            
            #separator {
                color: #333333;
                margin: 10px 0;
            }
            
            #statusLabel {
                color: #888888;
                padding: 10px;
                font-size: 12px;
                border-top: 1px solid #333333;
                margin-top: 10px;
            }
        """