from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QPushButton)
from datetime import datetime

class TicketReplyDialog(QDialog):
    def __init__(self, ticket: dict, db_manager, parent=None):
        super().__init__(parent)
        self.ticket = ticket
        self.db_manager = db_manager
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"Risposta Ticket #{self.ticket['id']}")
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Original message
        layout.addWidget(QLabel("<b>Ticket Originale:</b>"))
        original = QTextEdit()
        original.setPlainText(self.ticket['description'])
        original.setReadOnly(True)
        original.setMaximumHeight(100)
        layout.addWidget(original)
        
        # Reply
        layout.addWidget(QLabel("<b>La tua Risposta:</b>"))
        self.reply_text = QTextEdit()
        layout.addWidget(self.reply_text)
        
        # Buttons
        buttons = QHBoxLayout()
        
        send_button = QPushButton("Invia")
        send_button.clicked.connect(self._send_reply)
        buttons.addWidget(send_button)
        
        cancel_button = QPushButton("Annulla")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(cancel_button)
        
        layout.addLayout(buttons)
        
    def _send_reply(self):
        """Send the reply"""
        message = self.reply_text.toPlainText().strip()
        if not message:
            return
            
        # Add reply to database
        self.db_manager.add_message(self.ticket['id'], {
            'sender': 'Agente',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        self.accept() 