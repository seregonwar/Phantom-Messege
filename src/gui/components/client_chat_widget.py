from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                           QPushButton, QComboBox, QLabel, QListWidget,
                           QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from datetime import datetime
import json

class ClientChatWidget(QWidget):
    message_sent = pyqtSignal(str, str)  # hardware_id, message
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_client = None
        self.setup_ui()
        
        # Timer per aggiornare lo stato online
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_online_status)
        self.update_timer.start(30000)  # Aggiorna ogni 30 secondi
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Client status
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Stato: Nessun cliente selezionato")
        status_layout.addWidget(self.status_label)
        
        self.online_indicator = QLabel("●")
        self.online_indicator.setStyleSheet("color: gray;")
        status_layout.addWidget(self.online_indicator)
        
        layout.addLayout(status_layout)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)
        
        # Predefined messages
        predefined_layout = QHBoxLayout()
        self.predefined_combo = QComboBox()
        self.predefined_combo.addItems([
            "Seleziona messaggio predefinito...",
            "La tua licenza scadrà tra poco. Vuoi rinnovarla?",
            "Abbiamo rilevato un uso sospetto della licenza.",
            "È disponibile un aggiornamento importante.",
            "Il tuo account è stato temporaneamente sospeso.",
            "Per favore, aggiorna i tuoi dati di contatto."
        ])
        predefined_layout.addWidget(self.predefined_combo)
        
        insert_button = QPushButton("Inserisci")
        insert_button.clicked.connect(self._insert_predefined)
        predefined_layout.addWidget(insert_button)
        
        layout.addLayout(predefined_layout)
        
        # Message input
        input_layout = QHBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
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
        
    def set_client(self, hardware_id: str):
        """Imposta il cliente corrente e carica la cronologia"""
        self.current_client = hardware_id
        self.load_chat_history()
        self.update_online_status()
        
    def load_chat_history(self):
        """Carica la cronologia chat per il cliente corrente"""
        if not self.current_client:
            return
            
        # Ottieni la cronologia dal database
        history = self.db_manager.get_chat_history(self.current_client)
        
        self.chat_history.clear()
        for msg in history:
            self._add_message_to_history(
                msg['sender'],
                msg['message'],
                msg['timestamp']
            )
            
    def update_online_status(self):
        """Aggiorna lo stato online del cliente"""
        if not self.current_client:
            self.status_label.setText("Stato: Nessun cliente selezionato")
            self.online_indicator.setStyleSheet("color: gray;")
            return
            
        # Controlla l'ultimo heartbeat
        device = self.db_manager.get_device_info(self.current_client)
        if not device:
            return
            
        last_check = datetime.fromisoformat(device['last_check'])
        is_online = (datetime.now() - last_check).total_seconds() < 300  # 5 minuti
        
        self.status_label.setText(f"Stato: {device['hardware_id']}")
        self.online_indicator.setStyleSheet(
            "color: green;" if is_online else "color: red;"
        )
        
    def _insert_predefined(self):
        """Inserisce il messaggio predefinito selezionato"""
        message = self.predefined_combo.currentText()
        if message != "Seleziona messaggio predefinito...":
            self.message_input.setText(message)
            
    def _send_message(self):
        """Invia un messaggio al cliente"""
        if not self.current_client:
            return
            
        message = self.message_input.toPlainText().strip()
        if not message:
            return
            
        # Salva il messaggio nel database
        self.db_manager.add_chat_message(
            self.current_client,
            "admin",
            message
        )
        
        # Emetti il segnale per l'invio
        self.message_sent.emit(self.current_client, message)
        
        # Aggiorna la visualizzazione
        self._add_message_to_history("admin", message, datetime.now().isoformat())
        self.message_input.clear()
        
    def _add_message_to_history(self, sender: str, message: str, timestamp: str):
        """Aggiunge un messaggio alla cronologia"""
        dt = datetime.fromisoformat(timestamp)
        time_str = dt.strftime("%H:%M:%S")
        
        if sender == "admin":
            color = "#4CAF50"
            align = "right"
        else:
            color = "#2196F3"
            align = "left"
            
        html = f"""
            <div style='text-align: {align}; margin: 5px;'>
                <span style='color: gray; font-size: 0.8em;'>{time_str}</span><br>
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