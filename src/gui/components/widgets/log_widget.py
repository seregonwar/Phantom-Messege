from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtGui import QTextCursor

class LogWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Log", parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_log)
        controls_layout.addWidget(clear_button)
        
        save_button = QPushButton("Save Log")
        save_button.clicked.connect(self.save_log)
        controls_layout.addWidget(save_button)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)

    def add_log(self, message: str, success: bool = True):
        """Adds a line to the log"""
        status = "✓" if success else "✗"
        self.log_text.append(f"{status} {message}")
        # Scroll to bottom
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def clear_log(self):
        """Clears the log"""
        self.log_text.clear()

    def save_log(self):
        """Saves the log to a file"""
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Log",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText()) 