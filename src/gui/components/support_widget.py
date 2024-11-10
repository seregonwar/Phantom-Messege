from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTextEdit, QComboBox, QLineEdit,
                           QTabWidget, QListWidget, QDialog, QMessageBox,
                           QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from datetime import datetime
import json

class TicketDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Nuovo Ticket")
        layout = QVBoxLayout(self)
        
        # Oggetto
        self.subject = QLineEdit()
        self.subject.setPlaceholderText("Oggetto del ticket...")
        layout.addWidget(self.subject)
        
        # Categoria
        self.category = QComboBox()
        self.category.addItems([
            "Problema Tecnico",
            "Licenza",
            "Fatturazione",
            "Altro"
        ])
        layout.addWidget(self.category)
        
        # Priorità
        self.priority = QComboBox()
        self.priority.addItems([
            "Bassa",
            "Media",
            "Alta",
            "Urgente"
        ])
        layout.addWidget(self.priority)
        
        # Descrizione
        self.description = QTextEdit()
        self.description.setPlaceholderText("Descrivi il tuo problema...")
        layout.addWidget(self.description)
        
        # Pulsanti
        buttons = QHBoxLayout()
        
        submit = QPushButton("Invia")
        submit.clicked.connect(self.accept)
        cancel = QPushButton("Annulla")
        cancel.clicked.connect(self.reject)
        
        buttons.addWidget(submit)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)

class SupportWidget(QWidget):
    support_requested = pyqtSignal(dict)  # Emesso quando viene richiesto supporto
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()
        
        # Timer per aggiornare lo stato degli agenti
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_agent_status)
        self.update_timer.start(30000)  # Ogni 30 secondi
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs per ticket e chat live
        tabs = QTabWidget()
        
        # Tab Ticket
        ticket_tab = QWidget()
        ticket_layout = QVBoxLayout(ticket_tab)
        
        # Lista ticket
        self.ticket_list = QListWidget()
        self.ticket_list.itemDoubleClicked.connect(self.show_ticket_details)
        ticket_layout.addWidget(self.ticket_list)
        
        # Pulsanti ticket
        ticket_buttons = QHBoxLayout()
        
        new_ticket = QPushButton("Nuovo Ticket")
        new_ticket.clicked.connect(self.create_ticket)
        ticket_buttons.addWidget(new_ticket)
        
        refresh_tickets = QPushButton("Aggiorna")
        refresh_tickets.clicked.connect(self.load_tickets)
        ticket_buttons.addWidget(refresh_tickets)
        
        ticket_layout.addLayout(ticket_buttons)
        tabs.addTab(ticket_tab, "I Miei Ticket")
        
        # Tab Chat Live
        chat_tab = QWidget()
        chat_layout = QVBoxLayout(chat_tab)
        
        # Stato agenti
        status_layout = QHBoxLayout()
        self.agent_status = QLabel("Agenti disponibili: --")
        status_layout.addWidget(self.agent_status)
        
        self.connect_button = QPushButton("Connetti con Agente")
        self.connect_button.clicked.connect(self.request_live_support)
        status_layout.addWidget(self.connect_button)
        
        chat_layout.addLayout(status_layout)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        chat_layout.addWidget(self.chat_history)
        
        # Input messaggio
        input_layout = QHBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        input_layout.addWidget(self.message_input)
        
        send_button = QPushButton("Invia")
        send_button.clicked.connect(self.send_message)
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
        
        chat_layout.addLayout(input_layout)
        tabs.addTab(chat_tab, "Chat Live")
        
        layout.addWidget(tabs)
        
        # Carica i ticket esistenti
        self.load_tickets()
        
    def create_ticket(self):
        """Crea un nuovo ticket di supporto"""
        dialog = TicketDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            ticket_data = {
                'subject': dialog.subject.text(),
                'category': dialog.category.currentText(),
                'priority': dialog.priority.currentText(),
                'description': dialog.description.toPlainText(),
                'status': 'open',
                'created_at': datetime.now().isoformat()
            }
            
            # Salva il ticket
            if self.db_manager.add_support_ticket(ticket_data):
                self.load_tickets()
                QMessageBox.information(
                    self,
                    "Ticket Creato",
                    "Il tuo ticket è stato creato con successo.\n"
                    "Un agente ti risponderà il prima possibile."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Errore",
                    "Errore durante la creazione del ticket."
                )
                
    def load_tickets(self):
        """Carica tutti i ticket dell'utente"""
        self.ticket_list.clear()
        tickets = self.db_manager.get_user_tickets()
        
        for ticket in tickets:
            status_icon = "🟢" if ticket['status'] == 'open' else "🔴"
            self.ticket_list.addItem(
                f"{status_icon} [{ticket['priority']}] {ticket['subject']} "
                f"({ticket['created_at']})"
            )
            
    def show_ticket_details(self, item):
        """Mostra i dettagli di un ticket"""
        ticket_index = self.ticket_list.row(item)
        ticket = self.db_manager.get_user_tickets()[ticket_index]
        
        details = QDialog(self)
        details.setWindowTitle(f"Ticket: {ticket['subject']}")
        layout = QVBoxLayout(details)
        
        # Informazioni ticket
        info_text = f"""
            <h3>{ticket['subject']}</h3>
            <p><b>Categoria:</b> {ticket['category']}</p>
            <p><b>Priorità:</b> {ticket['priority']}</p>
            <p><b>Stato:</b> {ticket['status']}</p>
            <p><b>Creato il:</b> {ticket['created_at']}</p>
            <h4>Descrizione:</h4>
            <p>{ticket['description']}</p>
        """
        
        info = QLabel(info_text)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Cronologia risposte
        responses = self.db_manager.get_ticket_responses(ticket['id'])
        if responses:
            layout.addWidget(QLabel("<h4>Risposte:</h4>"))
            response_text = QTextEdit()
            response_text.setReadOnly(True)
            
            for response in responses:
                response_text.append(
                    f"Da: {response['sender']} - {response['timestamp']}\n"
                    f"{response['message']}\n"
                    f"{'-'*50}\n"
                )
            
            layout.addWidget(response_text)
        
        # Chiudi pulsante
        close = QPushButton("Chiudi")
        close.clicked.connect(details.accept)
        layout.addWidget(close)
        
        details.exec()
        
    def update_agent_status(self):
        """Aggiorna lo stato degli agenti disponibili"""
        available_agents = self.db_manager.get_available_agents()
        self.agent_status.setText(f"Agenti disponibili: {len(available_agents)}")
        self.connect_button.setEnabled(len(available_agents) > 0)
        
    def request_live_support(self):
        """Richiedi supporto live con un agente"""
        self.support_requested.emit({
            'type': 'live_support',
            'timestamp': datetime.now().isoformat()
        })
        
        QMessageBox.information(
            self,
            "Richiesta Inviata",
            "La tua richiesta è stata inviata.\n"
            "Un agente si connetterà con te a breve."
        )
        
    def send_message(self):
        """Invia un messaggio nella chat live"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return
            
        # Aggiungi il messaggio alla chat
        self._add_message_to_chat("Tu", message)
        self.message_input.clear()
        
        # Invia il messaggio
        self.db_manager.add_support_message({
            'sender': 'user',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
    def _add_message_to_chat(self, sender: str, message: str):
        """Aggiunge un messaggio alla chat history"""
        time_str = datetime.now().strftime("%H:%M:%S")
        
        if sender == "Tu":
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
        
class AgentChatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Chat con Agente")
        self.resize(600, 800)
        
        layout = QVBoxLayout(self)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.agent_status = QLabel("In attesa di un agente...")
        status_layout.addWidget(self.agent_status)
        
        self.connection_status = QLabel("●")
        self.connection_status.setStyleSheet("color: orange;")
        status_layout.addWidget(self.connection_status)
        
        layout.addLayout(status_layout)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)
        
        # Input area
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
        
        # Progress bar for queue position
        self.queue_progress = QProgressBar()
        self.queue_progress.setFormat("Posizione in coda: %v")
        self.queue_progress.setMaximum(10)
        self.queue_progress.setValue(0)
        self.queue_progress.hide()
        layout.addWidget(self.queue_progress)
        
        # Close button
        close_button = QPushButton("Chiudi")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
    def _send_message(self):
        message = self.message_input.toPlainText().strip()
        if not message:
            return
            
        self._add_message_to_chat("Tu", message)
        self.message_input.clear()
        
        # Qui invieremmo il messaggio al server
        
    def _add_message_to_chat(self, sender: str, message: str):
        time_str = datetime.now().strftime("%H:%M:%S")
        
        if sender == "Tu":
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
        
    def update_queue_position(self, position: int):
        """Aggiorna la posizione nella coda"""
        if position > 0:
            self.queue_progress.show()
            self.queue_progress.setValue(position)
            self.agent_status.setText(f"In coda ({position})")
        else:
            self.queue_progress.hide()
            
    def agent_connected(self, agent_name: str):
        """Chiamato quando un agente si connette"""
        self.connection_status.setStyleSheet("color: green;")
        self.agent_status.setText(f"Connesso con {agent_name}")
        self._add_message_to_chat(
            "Sistema", 
            f"L'agente {agent_name} si è unito alla chat"
        )