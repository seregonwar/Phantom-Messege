import os
import sys

# Aggiungi la directory root al Python path se non è già stato fatto
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QSpinBox, QComboBox, QFileDialog, QMessageBox,
    QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QTabWidget, QHeaderView, QMenu, QInputDialog,
    QDialog, QProgressDialog, QCheckBox, QDialogButtonBox,
    QTextEdit, QListWidget, QListWidgetItem, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime, timedelta
import json

# Import locali
from tools.license_generator import LicenseGenerator
from tools.db_manager import LicenseDBManager
from src.gui.components.device_map_widget import DeviceMapWidget
from src.gui.components.device_details_widget import DeviceDetailsWidget
from src.core.p2p_manager import P2PManager
from src.gui.components.client_chat_widget import ClientChatWidget
from src.gui.components.ticket_details_dialog import TicketDetailsDialog
from src.gui.components.ticket_reply_dialog import TicketReplyDialog
from src.gui.components.ticket_close_dialog import TicketCloseDialog
from src.gui.components.support_chat_dialog import SupportChatDialog

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class LicenseGeneratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.generator = LicenseGenerator()
        self.db_manager = LicenseDBManager()
        self.p2p_manager = P2PManager()
        self.setup_ui()
        
        # Avvia il server P2P
        if self.p2p_manager.start():
            logging.info("P2P server started successfully")
        else:
            logging.error("Failed to start P2P server")
            
        # Connetti i segnali P2P
        self.p2p_manager.device_connected.connect(self._on_device_connected)
        self.p2p_manager.device_disconnected.connect(self._on_device_disconnected)
        self.p2p_manager.device_updated.connect(self._on_device_updated)
        self.p2p_manager.message_received.connect(self._on_message_received)
        
    def setup_ui(self):
        self.setWindowTitle("Generatore Licenze")
        self.setMinimumSize(800, 600)
        
        # Widget centrale con tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_generator_tab(), "Genera Licenza")
        tabs.addTab(self._create_licenses_tab(), "Licenze Generate")
        tabs.addTab(self._create_devices_tab(), "Dispositivi Attivi")
        tabs.addTab(self._create_support_tab(), "Supporto")
        layout.addWidget(tabs)
        
        # Aggiungi pulsante refresh nella toolbar
        toolbar = self.addToolBar("Tools")
        refresh_action = toolbar.addAction("Aggiorna")
        refresh_action.triggered.connect(self.load_licenses)
        
    def _create_generator_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Gruppo informazioni licenza
        license_group = QGroupBox("Informazioni Licenza")
        license_layout = QFormLayout()
        
        # Hardware ID
        self.hardware_id_input = QLineEdit()
        self.hardware_id_input.setPlaceholderText("Lascia vuoto per licenza non vincolata")
        license_layout.addRow("Hardware ID:", self.hardware_id_input)
        
        # Tipo licenza
        self.license_type = QComboBox()
        self.license_type.addItems([
            "BASIC", "PROFESSIONAL", "ENTERPRISE", "TRIAL", "LIFETIME"
        ])
        self.license_type.currentTextChanged.connect(self._on_license_type_changed)
        license_layout.addRow("Tipo Licenza:", self.license_type)
        
        # Validità
        self.validity_container = QWidget()
        validity_layout = QHBoxLayout(self.validity_container)
        validity_layout.setContentsMargins(0, 0, 0, 0)
        
        self.validity_days = QSpinBox()
        self.validity_days.setRange(1, 3650)  # da 1 giorno a 10 anni
        self.validity_days.setValue(365)
        validity_layout.addWidget(self.validity_days)
        validity_layout.addWidget(QLabel("giorni"))
        license_layout.addRow("Validità:", self.validity_container)
        
        # Features
        self.features_button = QPushButton("Seleziona Funzionalità...")
        self.features_button.clicked.connect(self._select_features)
        license_layout.addRow("Funzionalità:", self.features_button)
        
        # Restrizioni
        self.restrictions_button = QPushButton("Configura Restrizioni...")
        self.restrictions_button.clicked.connect(self._configure_restrictions)
        license_layout.addRow("Restrizioni:", self.restrictions_button)
        
        # Customer Info
        self.customer_button = QPushButton("Informazioni Cliente...")
        self.customer_button.clicked.connect(self._add_customer_info)
        license_layout.addRow("Cliente:", self.customer_button)
        
        license_group.setLayout(license_layout)
        layout.addWidget(license_group)
        
        # Gruppo output
        output_group = QGroupBox("File di Output")
        output_layout = QVBoxLayout()
        
        # Path del file
        file_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setReadOnly(True)
        self.output_path.setPlaceholderText("Seleziona dove salvare il file di licenza...")
        file_layout.addWidget(self.output_path)
        
        browse_button = QPushButton("Sfoglia...")
        browse_button.clicked.connect(self.browse_output)
        file_layout.addWidget(browse_button)
        output_layout.addLayout(file_layout)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Gruppo risultati
        result_group = QGroupBox("Risultati")
        result_layout = QVBoxLayout()
        
        self.key_display = QLineEdit()
        self.key_display.setReadOnly(True)
        self.key_display.setPlaceholderText("La chiave di licenza apparirà qui...")
        result_layout.addWidget(self.key_display)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # Pulsanti
        buttons_layout = QHBoxLayout()
        
        generate_button = QPushButton("Genera Licenza")
        generate_button.clicked.connect(self.generate_license)
        generate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(generate_button)
        
        clear_button = QPushButton("Pulisci")
        clear_button.clicked.connect(self.clear_form)
        buttons_layout.addWidget(clear_button)
        
        layout.addLayout(buttons_layout)
        
        return tab

    def _on_license_type_changed(self, license_type: str):
        """Gestisce il cambio del tipo di licenza"""
        # Disabilita la validità per licenze LIFETIME
        self.validity_container.setEnabled(license_type != "LIFETIME")
        if license_type == "LIFETIME":
            self.validity_days.setValue(36500)  # 100 anni
            
        # Imposta le funzionalità predefinite per il tipo
        self.selected_features = self.get_features_for_type(license_type)
        
    def get_features_for_type(self, license_type: str):
        """Restituisce le funzionalità predefinite per un tipo di licenza"""
        features = {
            "BASIC": ["basic_features"],
            "PROFESSIONAL": ["basic_features", "advanced_features"],
            "ENTERPRISE": ["basic_features", "advanced_features", "priority_support"],
            "TRIAL": ["basic_features"],
            "LIFETIME": ["basic_features", "advanced_features", "priority_support", "custom_features"]
        }
        return features.get(license_type, ["basic_features"])
        
    def _select_features(self):
        """Dialog per selezionare le funzionalità"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleziona Funzionalità")
        layout = QVBoxLayout(dialog)
        
        # Lista di tutte le funzionalità possibili
        all_features = {
            'basic_features': 'Funzionalità Base',
            'advanced_features': 'Funzionalità Avanzate',
            'priority_support': 'Supporto Prioritario',
            'custom_features': 'Funzionalità Personalizzate',
            'api_access': 'Accesso API',
            'premium_support': 'Supporto Premium',
            'offline_mode': 'Modalità Offline',
            'multi_device': 'Multi-Dispositivo',
            'data_export': 'Esportazione Dati',
            'custom_branding': 'Branding Personalizzato'
        }
        
        checkboxes = {}
        for key, label in all_features.items():
            cb = QCheckBox(label)
            cb.setChecked(key in getattr(self, 'selected_features', []))
            checkboxes[key] = cb
            layout.addWidget(cb)
            
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_features = [
                key for key, cb in checkboxes.items() 
                if cb.isChecked()
            ]
            
    def _configure_restrictions(self):
        """Dialog per configurare le restrizioni"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configura Restrizioni")
        layout = QFormLayout(dialog)
        
        # Dispositivi massimi
        max_devices = QSpinBox()
        max_devices.setRange(1, 1000)
        max_devices.setValue(getattr(self, 'max_devices', 1))
        layout.addRow("Max Dispositivi:", max_devices)
        
        # Giorni offline
        offline_days = QSpinBox()
        offline_days.setRange(0, 365)
        offline_days.setValue(getattr(self, 'offline_days', 7))
        layout.addRow("Giorni Offline:", offline_days)
        
        # Restrizione geografica
        geo_restriction = QLineEdit()
        geo_restriction.setPlaceholderText("es. IT,US,DE")
        geo_restriction.setText(getattr(self, 'geo_restriction', ''))
        layout.addRow("Restrizione Geografica:", geo_restriction)
        
        # IP whitelist
        ip_whitelist = QLineEdit()
        ip_whitelist.setPlaceholderText("es. 192.168.1.0/24,10.0.0.0/8")
        ip_whitelist.setText(getattr(self, 'ip_whitelist', ''))
        layout.addRow("IP Whitelist:", ip_whitelist)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.max_devices = max_devices.value()
            self.offline_days = offline_days.value()
            self.geo_restriction = geo_restriction.text()
            self.ip_whitelist = ip_whitelist.text()
            
    def _add_customer_info(self):
        """Dialog per aggiungere informazioni cliente"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Informazioni Cliente")
        layout = QFormLayout(dialog)
        
        # Campi cliente
        name = QLineEdit()
        name.setText(getattr(self, 'customer_name', ''))
        layout.addRow("Nome:", name)
        
        company = QLineEdit()
        company.setText(getattr(self, 'customer_company', ''))
        layout.addRow("Azienda:", company)
        
        email = QLineEdit()
        email.setText(getattr(self, 'customer_email', ''))
        layout.addRow("Email:", email)
        
        phone = QLineEdit()
        phone.setText(getattr(self, 'customer_phone', ''))
        layout.addRow("Telefono:", phone)
        
        notes = QTextEdit()
        notes.setPlainText(getattr(self, 'customer_notes', ''))
        layout.addRow("Note:", notes)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.customer_name = name.text()
            self.customer_company = company.text()
            self.customer_email = email.text()
            self.customer_phone = phone.text()
            self.customer_notes = notes.toPlainText()
            
    def browse_output(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva file di licenza",
            "",
            "File di licenza (*.bin)"
        )
        if file_path:
            if not file_path.endswith('.bin'):
                file_path += '.bin'
            self.output_path.setText(file_path)

    def clear_form(self):
        self.hardware_id_input.clear()
        self.license_type.setCurrentIndex(0)
        self.validity_days.setValue(365)
        self.output_path.clear()
        self.key_display.clear()

    def _create_licenses_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tabella licenze
        self.licenses_table = QTableWidget()
        self.licenses_table.setColumnCount(7)
        self.licenses_table.setHorizontalHeaderLabels([
            "Chiave", "Hardware ID", "Tipo", "Validità",
            "Data Creazione", "Scadenza", "Stato"
        ])
        
        # Configura la tabella
        header = self.licenses_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.licenses_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.licenses_table.customContextMenuRequested.connect(self._show_license_context_menu)
        
        layout.addWidget(self.licenses_table)
        
        # Pulsanti
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Aggiorna")
        refresh_button.clicked.connect(self.load_licenses)
        button_layout.addWidget(refresh_button)
        
        sync_button = QPushButton("Sincronizza con Server")
        sync_button.clicked.connect(self.sync_with_server)
        sync_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(sync_button)
        
        export_button = QPushButton("Esporta")
        export_button.clicked.connect(self.export_licenses)
        button_layout.addWidget(export_button)
        
        layout.addLayout(button_layout)
        
        # Carica le licenze
        self.load_licenses()
        
        return tab
    
    def load_licenses(self):
        """Carica tutte le licenze nel database e da Dropbox"""
        try:
            # Carica le licenze dal database locale
            db_licenses = self.db_manager.get_all_licenses()
            
            # Carica le licenze da Dropbox
            dropbox_licenses = self.generator.dropbox.get_all_licenses()
            
            # Combina le licenze (preferendo i dati Dropbox se disponibili)
            licenses = {}
            
            # Prima aggiungi le licenze dal database locale
            for license in db_licenses:
                key = license['license_key']
                licenses[key] = license
            
            # Poi aggiorna/aggiungi le licenze da Dropbox
            for license in dropbox_licenses:
                key = license['license_key']
                if key in licenses:
                    # Aggiorna i dati esistenti con quelli di Dropbox
                    licenses[key].update({
                        'status': license['status'],
                        'dropbox_data': license['data']
                    })
                else:
                    # Aggiungi nuova licenza da Dropbox
                    licenses[key] = {
                        'license_key': key,
                        'hardware_id': license['hardware_id'],
                        'type': license['data'].get('type', 'UNKNOWN'),
                        'valid_days': license['data'].get('valid_days', 0),
                        'created_at': license['created_at'],
                        'status': license['status'],
                        'dropbox_data': license['data']
                    }
            
            # Aggiorna la tabella
            self.licenses_table.setRowCount(len(licenses))
            
            for row, (key, license) in enumerate(licenses.items()):
                self.licenses_table.setItem(row, 0, QTableWidgetItem(key))
                self.licenses_table.setItem(row, 1, QTableWidgetItem(license.get('hardware_id', 'N/A')))
                self.licenses_table.setItem(row, 2, QTableWidgetItem(license.get('type', 'UNKNOWN')))
                self.licenses_table.setItem(row, 3, QTableWidgetItem(f"{license.get('valid_days', 0)} giorni"))
                
                created_at = datetime.fromisoformat(license['created_at'])
                self.licenses_table.setItem(row, 4, QTableWidgetItem(
                    created_at.strftime("%d/%m/%Y %H:%M")
                ))
                
                # Calcola la data di scadenza
                expiration_date = created_at + timedelta(days=license.get('valid_days', 0))
                self.licenses_table.setItem(row, 5, QTableWidgetItem(
                    expiration_date.strftime("%d/%m/%Y %H:%M")
                ))
                
                # Aggiungi lo stato con colore
                status_item = QTableWidgetItem(license.get('status', 'unknown'))
                if license.get('status') == 'active':
                    status_item.setForeground(Qt.GlobalColor.green)
                elif license.get('status') == 'revoked':
                    status_item.setForeground(Qt.GlobalColor.red)
                self.licenses_table.setItem(row, 6, status_item)
            
            # Aggiorna le statistiche
            stats = self.generator.get_statistics()
            logging.info(f"Loaded {len(licenses)} licenses. Stats: {stats}")
            
        except Exception as e:
            logging.error(f"Error loading licenses: {e}")
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante il caricamento delle licenze:\n{str(e)}"
            )
    
    def _show_license_context_menu(self, position):
        """Mostra il menu contestuale per la gestione delle licenze"""
        menu = QMenu()
        
        row = self.licenses_table.currentRow()
        if row < 0:
            return
            
        key = self.licenses_table.item(row, 0).text()
        
        # Azioni base
        view_details = menu.addAction("Visualizza Dettagli")
        menu.addSeparator()
        
        # Azioni di modifica
        edit_menu = menu.addMenu("Modifica")
        edit_type = edit_menu.addAction("Tipo Licenza")
        edit_validity = edit_menu.addAction("Validità")
        edit_features = edit_menu.addAction("Funzionalità")
        edit_restrictions = edit_menu.addAction("Restrizioni")
        edit_customer = edit_menu.addAction("Info Cliente")
        
        menu.addSeparator()
        
        # Azioni di stato
        status_menu = menu.addMenu("Cambia Stato")
        activate = status_menu.addAction("Attiva")
        revoke = status_menu.addAction("Revoca")
        suspend = status_menu.addAction("Sospendi")
        
        menu.addSeparator()
        
        # Altre azioni
        copy_key = menu.addAction("Copia Chiave")
        export = menu.addAction("Esporta Dettagli")
        
        action = menu.exec(self.licenses_table.mapToGlobal(position))
        
        if not action:
            return
            
        if action == view_details:
            self._show_license_details(key)
        elif action == edit_type:
            self._edit_license_type(key)
        elif action == edit_validity:
            self._edit_license_validity(key)
        elif action == edit_features:
            self._edit_license_features(key)
        elif action == edit_restrictions:
            self._edit_license_restrictions(key)
        elif action == edit_customer:
            self._edit_customer_info(key)
        elif action == activate:
            self._change_license_status(key, 'active')
        elif action == revoke:
            self._revoke_license(key)
        elif action == suspend:
            self._change_license_status(key, 'suspended')
        elif action == copy_key:
            QApplication.clipboard().setText(key)
        elif action == export:
            self._export_license_details(key)

    def _edit_license_type(self, key: str):
        """Modifica il tipo di licenza"""
        license_data = self.db_manager.get_license_by_key(key)
        if not license_data:
            return
            
        types = ['BASIC', 'PROFESSIONAL', 'ENTERPRISE', 'TRIAL', 'LIFETIME']
        current_type = license_data.get('type', 'BASIC')
        
        new_type, ok = QInputDialog.getItem(
            self, "Modifica Tipo Licenza",
            "Seleziona il nuovo tipo:",
            types, types.index(current_type), False
        )
        
        if ok and new_type:
            self._update_license(key, {'type': new_type})

    def _edit_license_validity(self, key: str):
        """Modifica la validità della licenza"""
        license_data = self.db_manager.get_license_by_key(key)
        if not license_data:
            return
            
        current_days = license_data.get('valid_days', 365)
        
        new_days, ok = QInputDialog.getInt(
            self, "Modifica Validità",
            "Giorni di validità:",
            current_days, 1, 36500
        )
        
        if ok:
            self._update_license(key, {'valid_days': new_days})

    def _edit_license_features(self, key: str):
        """Modifica le funzionalità della licenza"""
        license_data = self.db_manager.get_license_by_key(key)
        if not license_data:
            return
            
        metadata = json.loads(license_data['metadata'])
        current_features = metadata.get('features', [])
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Modifica Funzionalità")
        layout = QVBoxLayout(dialog)
        
        # Lista di tutte le funzionalità possibili
        all_features = [
            'basic_features',
            'advanced_features',
            'priority_support',
            'custom_features',
            'api_access',
            'premium_support'
        ]
        
        checkboxes = {}
        for feature in all_features:
            cb = QCheckBox(feature)
            cb.setChecked(feature in current_features)
            checkboxes[feature] = cb
            layout.addWidget(cb)
            
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_features = [
                feature for feature, cb in checkboxes.items() 
                if cb.isChecked()
            ]
            self._update_license(key, {'features': new_features})

    def _edit_license_restrictions(self, key: str):
        """Modifica le restrizioni della licenza"""
        license_data = self.db_manager.get_license_by_key(key)
        if not license_data:
            return
            
        metadata = json.loads(license_data['metadata'])
        current_restrictions = metadata.get('restrictions', {})
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Modifica Restrizioni")
        layout = QFormLayout(dialog)
        
        # Campi per le restrizioni
        max_devices = QSpinBox()
        max_devices.setRange(1, 1000)
        max_devices.setValue(current_restrictions.get('max_devices', 1))
        layout.addRow("Max Dispositivi:", max_devices)
        
        offline_days = QSpinBox()
        offline_days.setRange(0, 365)
        offline_days.setValue(current_restrictions.get('offline_days', 7))
        layout.addRow("Giorni Offline:", offline_days)
        
        geo_restriction = QLineEdit()
        geo_restriction.setText(current_restrictions.get('geographic_restriction', ''))
        layout.addRow("Restrizione Geografica:", geo_restriction)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_restrictions = {
                'max_devices': max_devices.value(),
                'offline_days': offline_days.value(),
                'geographic_restriction': geo_restriction.text() or None
            }
            self._update_license(key, {'restrictions': new_restrictions})

    def _update_license(self, key: str, updates: dict):
        """Aggiorna una licenza e sincronizza con Dropbox"""
        try:
            # Aggiorna nel database locale
            if not self.db_manager.update_license_status(key, updates):
                raise Exception("Failed to update local database")
                
            # Aggiorna su Dropbox
            license_data = self.db_manager.get_license_by_key(key)
            if not self.generator.dropbox.upload_license(
                key,
                license_data['hardware_id'],
                json.loads(license_data['metadata'])
            ):
                raise Exception("Failed to update Dropbox")
                
            # Ricarica la vista
            self.load_licenses()
            
            QMessageBox.information(
                self,
                "Successo",
                "Licenza aggiornata correttamente"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante l'aggiornamento:\n{str(e)}"
            )

    def _revoke_license(self, key: str):
        """Revoca una licenza"""
        reply = QMessageBox.question(
            self,
            "Conferma Revoca",
            "Sei sicuro di voler revocare questa licenza?\n"
            "Questa azione non può essere annullata.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            reason, ok = QInputDialog.getText(
                self,
                "Motivo Revoca",
                "Inserisci il motivo della revoca:"
            )
            
            if ok:
                try:
                    # Revoca su Dropbox
                    if not self.generator.dropbox.revoke_license(key, reason):
                        raise Exception("Failed to revoke on Dropbox")
                        
                    # Revoca nel database locale
                    if not self.db_manager.update_license_status(key, 'revoked'):
                        raise Exception("Failed to revoke in local database")
                        
                    # Ricarica la vista
                    self.load_licenses()
                    
                    QMessageBox.information(
                        self,
                        "Successo",
                        "Licenza revocata correttamente"
                    )
                    
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Errore",
                        f"Errore durante la revoca:\n{str(e)}"
                    )
    
    def _show_license_details(self, key: str):
        """Mostra i dettagli completi della licenza"""
        license_data = self.db_manager.get_license_by_key(key)
        if not license_data:
            return
            
        metadata = json.loads(license_data['metadata'])
        
        details = "\n".join([
            f"Chiave: {key}",
            f"Hardware ID: {license_data['hardware_id'] or 'N/A'}",
            f"Tipo: {license_data['type']}",
            f"Validità: {license_data['valid_days']} giorni",
            f"Creata il: {license_data['created_at']}",
            f"Scade il: {license_data['expiration_date']}",
            f"Stato: {license_data['status']}",
            "\nMetadati aggiuntivi:",
            json.dumps(metadata, indent=2)
        ])
        
        QMessageBox.information(self, "Dettagli Licenza", details)
    
    def _change_license_status(self, key: str, status: str):
        """Cambia lo stato di una licenza"""
        if self.db_manager.update_license_status(key, {'status': status}):
            self.load_licenses()
    
    def export_licenses(self):
        """Esporta le licenze in formato CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Esporta Licenze",
            "",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
            
        if not file_path.endswith('.csv'):
            file_path += '.csv'
            
        try:
            licenses = self.db_manager.get_all_licenses()
            with open(file_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("Chiave,Hardware ID,Tipo,Validità,Data Creazione,Scadenza,Stato\n")
                
                # Data
                for license in licenses:
                    f.write(f"{license['license_key']},{license['hardware_id'] or 'N/A'},"
                           f"{license['type']},{license['valid_days']},"
                           f"{license['created_at']},{license['expiration_date']},"
                           f"{license['status']}\n")
                           
            QMessageBox.information(
                self,
                "Esportazione Completata",
                f"Le licenze sono state esportate in:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante l'esportazione:\n{str(e)}"
            )
    
    def generate_license(self):
        if not self.output_path.text():
            QMessageBox.warning(
                self,
                "Errore",
                "Seleziona dove salvare il file di licenza"
            )
            return
            
        try:
            # Genera la licenza
            hardware_id = self.hardware_id_input.text().strip() or None
            
            # Prepara i metadati completi
            self.generator.custom_metadata = {
                'type': self.license_type.currentText(),
                'valid_days': self.validity_days.value(),
                'features': getattr(self, 'selected_features', ['basic_features']),
                'restrictions': {
                    'max_devices': getattr(self, 'max_devices', 1),
                    'offline_days': getattr(self, 'offline_days', 7),
                    'geographic_restriction': getattr(self, 'geo_restriction', None),
                    'ip_whitelist': getattr(self, 'ip_whitelist', None)
                },
                'customer_info': {
                    'name': getattr(self, 'customer_name', ''),
                    'company': getattr(self, 'customer_company', ''),
                    'email': getattr(self, 'customer_email', ''),
                    'phone': getattr(self, 'customer_phone', ''),
                    'notes': getattr(self, 'customer_notes', '')
                }
            }
            
            key, metadata = self.generator.generate_license_file(
                self.output_path.text(),
                hardware_id
            )
            
            # Salva la licenza nel database
            self.db_manager.save_license(
                key, 
                metadata,
                self.output_path.text()
            )
            
            # Aggiorna la vista delle licenze
            self.load_licenses()
            
            # Mostra la chiave generata
            self.key_display.setText(key)
            
            QMessageBox.information(
                self,
                "Successo",
                f"Licenza generata con successo!\n\n"
                f"File salvato in: {self.output_path.text()}\n"
                f"Tipo: {metadata['type']}\n"
                f"Validità: {metadata['valid_days']} giorni"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante la generazione della licenza:\n{str(e)}"
            )
    
    def _create_devices_tab(self):
        """Crea la tab per la gestione dei dispositivi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Status bar per le connessioni
        status_layout = QHBoxLayout()
        self.connection_status = QLabel("Dispositivi connessi: 0")
        status_layout.addWidget(self.connection_status)
        
        self.online_status = QLabel("●")
        self.online_status.setStyleSheet("color: green;")
        status_layout.addWidget(self.online_status)
        
        layout.addLayout(status_layout)
        
        # Tabella dispositivi
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(8)
        self.devices_table.setHorizontalHeaderLabels([
            "Hardware ID", "Licenza", "Stato", "Ultimo Controllo",
            "Sistema", "Posizione", "IP", "Azioni"
        ])
        
        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.devices_table)
        
        # Pulsanti di controllo
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Aggiorna")
        refresh_button.clicked.connect(self.load_devices)
        button_layout.addWidget(refresh_button)
        
        export_button = QPushButton("Esporta Report")
        export_button.clicked.connect(self.export_devices_report)
        button_layout.addWidget(export_button)
        
        layout.addLayout(button_layout)
        
        # Carica i dispositivi
        self.load_devices()
        
        return tab
        
    def _on_device_connected(self, device_info: dict):
        """Gestisce la connessione di un nuovo dispositivo"""
        logging.info(f"Device connected: {device_info['hardware_id']}")
        self.load_devices()  # Ricarica la lista
        self._update_connection_status()
        
    def _on_device_disconnected(self, hardware_id: str):
        """Gestisce la disconnessione di un dispositivo"""
        logging.info(f"Device disconnected: {hardware_id}")
        self.load_devices()  # Ricarica la lista
        self._update_connection_status()
        
    def _on_device_updated(self, device_info: dict):
        """Gestisce l'aggiornamento delle informazioni di un dispositivo"""
        logging.info(f"Device updated: {device_info['hardware_id']}")
        self.load_devices()  # Ricarica la lista
        
    def _on_message_received(self, hardware_id: str, message: str):
        """Gestisce i messaggi ricevuti dai dispositivi"""
        logging.info(f"Message from {hardware_id}: {message}")
        # Qui puoi implementare la logica per gestire i messaggi
        
    def _update_connection_status(self):
        """Aggiorna lo stato delle connessioni"""
        connected_devices = len(self.p2p_manager.get_connected_devices())
        self.connection_status.setText(f"Dispositivi connessi: {connected_devices}")
        
    def _open_chat(self, device: dict):
        """Apre la chat con un dispositivo"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Chat - {device['hardware_id']}")
        dialog.resize(500, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Usa il ClientChatWidget con supporto P2P
        chat_widget = ClientChatWidget(self.db_manager)
        chat_widget.set_client(device['hardware_id'])
        
        # Connetti il widget alla comunicazione P2P
        chat_widget.message_sent.connect(
            lambda msg: self.p2p_manager.send_message(device['hardware_id'], msg)
        )
        
        layout.addWidget(chat_widget)
        dialog.exec()
        
    def closeEvent(self, event):
        """Gestisce la chiusura dell'applicazione"""
        # Ferma il server P2P
        self.p2p_manager.stop()
        super().closeEvent(event)
    
    def load_devices(self):
        """Carica tutti i dispositivi attivi"""
        try:
            # Sincronizza prima con Dropbox
            self.db_manager._sync_with_dropbox()
            
            # Ottieni i dispositivi
            devices = self.db_manager.get_all_devices()
            self.devices_table.setRowCount(len(devices))
            
            for row, device in enumerate(devices):
                try:
                    # Hardware ID
                    self.devices_table.setItem(row, 0, QTableWidgetItem(device['hardware_id']))
                    
                    # Licenza
                    self.devices_table.setItem(row, 1, QTableWidgetItem(device['license_key']))
                    
                    # Stato con colore
                    status_item = QTableWidgetItem(device['status'])
                    status_item.setForeground(
                        Qt.GlobalColor.green if device['status'] == 'active' 
                        else Qt.GlobalColor.red
                    )
                    self.devices_table.setItem(row, 2, status_item)
                    
                    # Ultimo controllo
                    last_check = datetime.fromisoformat(device['last_check'])
                    self.devices_table.setItem(row, 3, QTableWidgetItem(
                        last_check.strftime("%d/%m/%Y %H:%M")
                    ))
                    
                    # Sistema
                    system_info = json.loads(device.get('system_info', '{}'))
                    system = system_info.get('system', {})
                    system_text = f"{system.get('os', 'Unknown')} - {system.get('version', '')}"
                    self.devices_table.setItem(row, 4, QTableWidgetItem(system_text))
                    
                    # Posizione
                    location = json.loads(device.get('location', '{}'))
                    location_text = f"{location.get('city', 'Unknown')}, {location.get('country', '')}"
                    self.devices_table.setItem(row, 5, QTableWidgetItem(location_text))
                    
                    # IP
                    self.devices_table.setItem(row, 6, QTableWidgetItem(device.get('ip_address', 'N/A')))
                    
                    # Pulsanti azione
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(0, 0, 0, 0)
                    
                    # Pulsante dettagli
                    details_button = QPushButton("Dettagli")
                    details_button.clicked.connect(lambda checked, d=device: self.show_device_details(d))
                    actions_layout.addWidget(details_button)
                    
                    # Pulsante revoca
                    if device['status'] == 'active':
                        revoke_button = QPushButton("Revoca")
                        revoke_button.setStyleSheet("background-color: #ff4444; color: white;")
                        revoke_button.clicked.connect(lambda checked, d=device: self.revoke_device(d))
                        actions_layout.addWidget(revoke_button)
                    
                    # Pulsante chat
                    chat_button = QPushButton("Chat")
                    chat_button.clicked.connect(lambda checked, d=device: self._open_chat(d))
                    actions_layout.addWidget(chat_button)
                    
                    self.devices_table.setCellWidget(row, 7, actions_widget)
                    
                except Exception as e:
                    logging.error(f"Error loading device row: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error loading devices: {e}")
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante il caricamento dei dispositivi:\n{str(e)}"
            )
            
    def revoke_device(self, device):
        """Revoca l'accesso a un dispositivo"""
        reply = QMessageBox.question(
            self,
            "Conferma Revoca",
            f"Sei sicuro di voler revocare l'accesso al dispositivo?\n"
            f"Hardware ID: {device['hardware_id']}\n"
            f"Licenza: {device['license_key']}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.db_manager.revoke_device(device['hardware_id'], device['license_key']):
                    QMessageBox.information(
                        self,
                        "Successo",
                        "Accesso revocato con successo"
                    )
                    self.load_devices()  # Ricarica la lista
                else:
                    QMessageBox.warning(
                        self,
                        "Errore",
                        "Impossibile revocare l'accesso"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Errore",
                    f"Errore durante la revoca: {str(e)}"
                )
                
    def show_device_details(self, device):
        """Mostra i dettagli completi di un dispositivo"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Device Details - {device['hardware_id']}")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Details tab
        details_widget = DeviceDetailsWidget()
        details_widget.update_device_info(device)
        tabs.addTab(details_widget, "Device Details")
        
        # Map tab
        map_widget = DeviceMapWidget()
        map_widget.update_devices([device])  # Show only this device
        tabs.addTab(map_widget, "Location Map")
        
        layout.addWidget(tabs)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec()
    
    def _export_device_details(self, device, details_text):
        """Esporta i dettagli del dispositivo in un file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Esporta Dettagli Dispositivo",
            f"device_details_{device['hardware_id'][:8]}.txt",
            "File di testo (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(details_text)
                QMessageBox.information(
                    self,
                    "Esportazione Completata",
                    f"Dettagli salvati in:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Errore",
                    f"Errore durante l'esportazione:\n{str(e)}"
                )
    
    def export_devices_report(self):
        """Esporta un report dettagliato dei dispositivi"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Esporta Report Dispositivi",
            "",
            "CSV Files (*.csv);;PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
            
        try:
            devices = self.db_manager.get_all_devices()
            
            if file_path.endswith('.csv'):
                self._export_devices_csv(file_path, devices)
            else:
                self._export_devices_pdf(file_path, devices)  # Implementare se necessario
                
            QMessageBox.information(
                self,
                "Esportazione Completata",
                f"Report salvato in:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante l'esportazione:\n{str(e)}"
            )
            
    def _export_devices_csv(self, file_path: str, devices: list):
        """Esporta i dispositivi in formato CSV"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("Hardware ID,Licenza,Data Attivazione,Ultimo Controllo,Stato\n")
            for device in devices:
                f.write(
                    f"{device['hardware_id']},{device['license_key']},"
                    f"{device['activation_date']},{device['last_check']},"
                    f"{device['status']}\n"
                )

    def sync_with_server(self):
        """Sincronizza le modifiche con il server"""
        try:
            # Mostra dialogo di progresso
            progress = QProgressDialog("Sincronizzazione con il server in corso...", None, 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Sincronizzazione")
            progress.setAutoClose(True)
            progress.setValue(0)
            
            # Ottieni le licenze locali
            progress.setValue(20)
            local_licenses = self.db_manager.get_all_licenses()
            
            # Ottieni le licenze da Dropbox
            progress.setValue(40)
            dropbox_licenses = self.generator.dropbox.get_all_licenses()
            
            # Sincronizza le modifiche locali su Dropbox
            progress.setValue(60)
            for local_license in local_licenses:
                dropbox_license = next(
                    (l for l in dropbox_licenses if l['license_key'] == local_license['license_key']), 
                    None
                )
                
                if dropbox_license:
                    # Se la versione locale è più recente, aggiorna Dropbox
                    local_date = datetime.fromisoformat(local_license.get('created_at', '2000-01-01T00:00:00'))
                    dropbox_date = datetime.fromisoformat(dropbox_license.get('created_at', '2000-01-01T00:00:00'))
                    
                    if local_date > dropbox_date:
                        self.generator.dropbox.upload_license(
                            local_license['license_key'],
                            local_license.get('hardware_id'),
                            json.loads(local_license.get('metadata', '{}'))
                        )
                else:
                    # Nuova licenza locale, carica su Dropbox
                    self.generator.dropbox.upload_license(
                        local_license['license_key'],
                        local_license.get('hardware_id'),
                        json.loads(local_license.get('metadata', '{}'))
                    )
            
            # Aggiorna il database locale con le modifiche da Dropbox
            progress.setValue(80)
            self.db_manager._sync_with_dropbox()
            
            # Ricarica la vista
            progress.setValue(90)
            self.load_licenses()
            
            progress.setValue(100)
            
            QMessageBox.information(
                self,
                "Sincronizzazione Completata",
                f"Sincronizzate {len(local_licenses)} licenze locali e {len(dropbox_licenses)} licenze remote"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante la sincronizzazione:\n{str(e)}"
            )

    def _create_support_tab(self) -> QWidget:
        """Crea la tab per il supporto"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Statistiche supporto
        stats_group = QGroupBox("Statistiche Supporto")
        stats_layout = QGridLayout()
        
        self.total_tickets = QLabel("Ticket Totali: 0")
        self.active_tickets = QLabel("Ticket Attivi: 0")
        self.resolved_tickets = QLabel("Ticket Risolti: 0")
        self.avg_response_time = QLabel("Tempo Medio Risposta: --")
        
        stats_layout.addWidget(self.total_tickets, 0, 0)
        stats_layout.addWidget(self.active_tickets, 0, 1)
        stats_layout.addWidget(self.resolved_tickets, 1, 0)
        stats_layout.addWidget(self.avg_response_time, 1, 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Tabella ticket
        tickets_group = QGroupBox("Ticket Recenti")
        tickets_layout = QVBoxLayout()
        
        self.tickets_table = QTableWidget()
        self.tickets_table.setColumnCount(7)
        self.tickets_table.setHorizontalHeaderLabels([
            "ID", "Cliente", "Oggetto", "Priorità", "Stato", "Data", "Azioni"
        ])
        
        header = self.tickets_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        tickets_layout.addWidget(self.tickets_table)
        tickets_group.setLayout(tickets_layout)
        layout.addWidget(tickets_group)
        
        # Chat attive
        chats_group = QGroupBox("Chat Attive")
        chats_layout = QVBoxLayout()
        
        self.active_chats_list = QListWidget()
        self.active_chats_list.itemDoubleClicked.connect(self._open_chat)
        chats_layout.addWidget(self.active_chats_list)
        
        chats_group.setLayout(chats_layout)
        layout.addWidget(chats_group)
        
        # Pulsanti azioni
        actions_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Aggiorna")
        refresh_button.clicked.connect(self._refresh_support_data)
        actions_layout.addWidget(refresh_button)
        
        export_button = QPushButton("Esporta Report")
        export_button.clicked.connect(self._export_support_report)
        actions_layout.addWidget(export_button)
        
        layout.addLayout(actions_layout)
        
        # Carica i dati iniziali
        self._refresh_support_data()
        
        # Timer per aggiornamenti automatici
        self.support_timer = QTimer()
        self.support_timer.timeout.connect(self._refresh_support_data)
        self.support_timer.start(30000)  # Aggiorna ogni 30 secondi
        
        return tab
        
    def _refresh_support_data(self):
        """Aggiorna i dati del supporto"""
        try:
            # Aggiorna statistiche
            stats = self.db_manager.get_support_statistics()
            self.total_tickets.setText(f"Ticket Totali: {stats['total_tickets']}")
            self.active_tickets.setText(f"Ticket Attivi: {stats['active_tickets']}")
            self.resolved_tickets.setText(f"Ticket Risolti: {stats['resolved_tickets']}")
            self.avg_response_time.setText(
                f"Tempo Medio Risposta: {stats['avg_response_time']:.1f}m"
            )
            
            # Aggiorna tabella ticket
            tickets = self.db_manager.get_recent_tickets()
            self.tickets_table.setRowCount(len(tickets))
            
            for row, ticket in enumerate(tickets):
                self.tickets_table.setItem(row, 0, QTableWidgetItem(str(ticket['id'])))
                self.tickets_table.setItem(row, 1, QTableWidgetItem(ticket['client_id']))
                self.tickets_table.setItem(row, 2, QTableWidgetItem(ticket['subject']))
                self.tickets_table.setItem(row, 3, QTableWidgetItem(ticket['priority']))
                self.tickets_table.setItem(row, 4, QTableWidgetItem(ticket['status']))
                self.tickets_table.setItem(row, 5, QTableWidgetItem(
                    datetime.fromisoformat(ticket['created_at']).strftime("%d/%m/%Y %H:%M")
                ))
                
                # Pulsanti azioni
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                view_button = QPushButton("Visualizza")
                view_button.clicked.connect(lambda _, t=ticket: self._view_ticket(t))
                actions_layout.addWidget(view_button)
                
                reply_button = QPushButton("Rispondi")
                reply_button.clicked.connect(lambda _, t=ticket: self._reply_to_ticket(t))
                actions_layout.addWidget(reply_button)
                
                self.tickets_table.setCellWidget(row, 6, actions_widget)
                
            # Aggiorna chat attive
            chats = self.db_manager.get_active_chats()
            self.active_chats_list.clear()
            
            for chat in chats:
                item = QListWidgetItem(
                    f"Chat con {chat['client_id']} - {chat['started_at']}"
                )
                item.setData(Qt.ItemDataRole.UserRole, chat)
                self.active_chats_list.addItem(item)
                
        except Exception as e:
            logging.error(f"Error refreshing support data: {e}")
            
    def _export_support_report(self):
        """Esporta report del supporto"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Esporta Report Supporto",
            "",
            "PDF Files (*.pdf);;Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.pdf'):
                    self._export_pdf_report(file_path)
                else:
                    self._export_excel_report(file_path)
                    
                QMessageBox.information(
                    self,
                    "Successo",
                    "Report esportato con successo!"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Errore",
                    f"Errore durante l'esportazione: {str(e)}"
                )

def main():
    app = QApplication(sys.argv)
    window = LicenseGeneratorWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 