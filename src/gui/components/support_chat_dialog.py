from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QPushButton, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime

class SupportChatDialog(QDialog):
    def __init__(self, client_info: dict, db_manager, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.db_manager = db_manager
        self.setup_ui()
        
        # Avvia il polling per i messaggi
        self.message_timer = QTimer()
        self.message_timer.timeout.connect(self._check_new_messages)
        self.message_timer.start(2000)  # Controlla ogni 2 secondi
        
    def setup_ui(self):
        self.setWindowTitle("Chat Supporto")
        self.resize(600, 800)
        
        layout = QVBoxLayout(self)
        
        # Client info header
        info_layout = QHBoxLayout()
        
        client_label = QLabel(f"Cliente: {self.client_info.get('hardware_id', 'Unknown')}")
        info_layout.addWidget(client_label)
        
        self.status_label = QLabel("●")
        self.status_label.setStyleSheet("color: green;")
        info_layout.addWidget(self.status_label)
        
        layout.addLayout(info_layout)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("Scrivi un messaggio...")
        input_layout.addWidget(self.message_input)
        
        send_button = QPushButton("Invia")
        send_button.clicked.connect(self._send_message)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        input_layout.addWidget(send_button)
        
        layout.addLayout(input_layout)
        
        # Quick responses
        quick_layout = QHBoxLayout()
        
        quick_responses = [
            "Come posso aiutarti?",
            "Un momento per favore...",
            "Potresti fornire più dettagli?",
            "Il problema è stato risolto?"
        ]
        
        for response in quick_responses:
            btn = QPushButton(response)
            btn.clicked.connect(lambda checked, r=response: self._send_quick_response(r))
            quick_layout.addWidget(btn)
            
        layout.addLayout(quick_layout)
        
        # Load chat history
        self._load_chat_history()
        
    def _load_chat_history(self):
        """Carica la cronologia della chat"""
        messages = self.db_manager.get_chat_history(self.client_info['hardware_id'])
        for message in messages:
            self._add_message_to_chat(
                "Agente" if message['sender'] == 'agent' else "Cliente",
                message['message'],
                message['timestamp']
            )
            
    def _send_message(self):
        """Invia un messaggio"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return
            
        # Aggiungi alla chat locale
        self._add_message_to_chat("Agente", message)
        self.message_input.clear()
        
        # Salva nel database
        self.db_manager.add_chat_message(
            self.client_info['hardware_id'],
            'agent',
            message
        )
        
    def _send_quick_response(self, message: str):
        """Invia una risposta rapida"""
        self.message_input.setPlainText(message)
        self._send_message()
        
    def _check_new_messages(self):
        """Controlla nuovi messaggi"""
        messages = self.db_manager.get_chat_history(self.client_info['hardware_id'])
        current_count = self.chat_history.document().lineCount()
        
        if len(messages) > current_count:
            # Ci sono nuovi messaggi
            for message in messages[current_count:]:
                self._add_message_to_chat(
                    "Cliente" if message['sender'] == 'client' else "Agente",
                    message['message'],
                    message['timestamp']
                )
                
    def _add_message_to_chat(self, sender: str, message: str, timestamp: str = None):
        """Aggiunge un messaggio alla chat"""
        if not timestamp:
            timestamp = datetime.now().isoformat()
            
        time_str = datetime.fromisoformat(timestamp).strftime("%H:%M:%S")
        
        if sender == "Agente":
            color = "#4CAF50"
            align = "right"
        else:
            color = "#2196F3"
            align = "left"
            
        html = f"""
            <div style='text-align: {align}; margin: 5px;'>
                <span style='color: gray; font-size: 0.8em;'>{time_str} - {sender}</span><br>
                <span style='background-color: {color}; color: white; padding: 5px 10px; 
                      border-radius: 10px; display: inline-block;'>
                    {message}
                </span>
            </div>
        """
        
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertHtml(html)
        
        # Scroll to bottom
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def closeEvent(self, event):
        """Gestisce la chiusura della finestra"""
        self.message_timer.stop()
        super().closeEvent(event) 