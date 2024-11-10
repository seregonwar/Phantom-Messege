from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QPushButton, QComboBox)
from datetime import datetime

class TicketCloseDialog(QDialog):
    def __init__(self, ticket: dict, db_manager, parent=None):
        super().__init__(parent)
        self.ticket = ticket
        self.db_manager = db_manager
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"Chiudi Ticket #{self.ticket['id']}")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Resolution type
        layout.addWidget(QLabel("Tipo di Risoluzione:"))
        self.resolution_type = QComboBox()
        self.resolution_type.addItems([
            "Risolto",
            "Non Riproducibile",
            "Duplicato",
            "Non Risolvibile",
            "Chiuso dall'Utente"
        ])
        layout.addWidget(self.resolution_type)
        
        # Resolution notes
        layout.addWidget(QLabel("Note di Chiusura:"))
        self.resolution_notes = QTextEdit()
        layout.addWidget(self.resolution_notes)
        
        # Buttons
        buttons = QHBoxLayout()
        
        close_button = QPushButton("Chiudi Ticket")
        close_button.clicked.connect(self._close_ticket)
        buttons.addWidget(close_button)
        
        cancel_button = QPushButton("Annulla")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(cancel_button)
        
        layout.addLayout(buttons)
        
    def _close_ticket(self):
        """Close the ticket"""
        resolution = {
            'type': self.resolution_type.currentText(),
            'notes': self.resolution_notes.toPlainText().strip(),
            'closed_at': datetime.now().isoformat()
        }
        
        # Update ticket status
        self.db_manager.close_ticket(self.ticket['id'], resolution)
        
        self.accept() 