from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QPushButton, QScrollArea, QWidget)
from PyQt6.QtCore import Qt
from datetime import datetime

class TicketDetailsDialog(QDialog):
    def __init__(self, ticket: dict, db_manager, parent=None):
        super().__init__(parent)
        self.ticket = ticket
        self.db_manager = db_manager
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"Ticket #{self.ticket['id']}")
        self.resize(600, 800)
        
        layout = QVBoxLayout(self)
        
        # Ticket info
        info_layout = QHBoxLayout()
        
        # Left column
        left_info = QVBoxLayout()
        left_info.addWidget(QLabel(f"<b>Oggetto:</b> {self.ticket['subject']}"))
        left_info.addWidget(QLabel(f"<b>Categoria:</b> {self.ticket['category']}"))
        left_info.addWidget(QLabel(f"<b>Priorità:</b> {self.ticket['priority']}"))
        info_layout.addLayout(left_info)
        
        # Right column
        right_info = QVBoxLayout()
        right_info.addWidget(QLabel(f"<b>Stato:</b> {self.ticket['status']}"))
        right_info.addWidget(QLabel(f"<b>Creato:</b> {self._format_date(self.ticket['created_at'])}"))
        if self.ticket['closed_at']:
            right_info.addWidget(QLabel(f"<b>Chiuso:</b> {self._format_date(self.ticket['closed_at'])}"))
        info_layout.addLayout(right_info)
        
        layout.addLayout(info_layout)
        
        # Description
        layout.addWidget(QLabel("<b>Descrizione:</b>"))
        description = QTextEdit()
        description.setPlainText(self.ticket['description'])
        description.setReadOnly(True)
        description.setMaximumHeight(100)
        layout.addWidget(description)
        
        # Messages history
        layout.addWidget(QLabel("<b>Cronologia Messaggi:</b>"))
        
        messages_area = QScrollArea()
        messages_area.setWidgetResizable(True)
        messages_widget = QWidget()
        messages_layout = QVBoxLayout(messages_widget)
        
        # Load messages
        messages = self.db_manager.get_ticket_responses(self.ticket['id'])
        for message in messages:
            message_widget = QWidget()
            message_layout = QVBoxLayout(message_widget)
            
            header = QHBoxLayout()
            header.addWidget(QLabel(f"<b>{message['sender']}</b>"))
            header.addWidget(QLabel(self._format_date(message['timestamp'])))
            message_layout.addLayout(header)
            
            content = QTextEdit()
            content.setPlainText(message['message'])
            content.setReadOnly(True)
            content.setMaximumHeight(80)
            message_layout.addWidget(content)
            
            messages_layout.addWidget(message_widget)
            
        messages_area.setWidget(messages_widget)
        layout.addWidget(messages_area)
        
        # Buttons
        buttons = QHBoxLayout()
        
        close_button = QPushButton("Chiudi")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)
        
        layout.addLayout(buttons)
        
    def _format_date(self, date_str: str) -> str:
        """Format datetime string"""
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%d/%m/%Y %H:%M") 