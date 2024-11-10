from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, 
                           QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from datetime import datetime
from ...core.license_manager import LicenseManager

class LicenseInfoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_manager = LicenseManager()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # License Details Group
        details_group = QGroupBox("Dettagli Licenza")
        details_layout = QVBoxLayout()
        
        self.key_label = QLabel()
        self.type_label = QLabel()
        self.status_label = QLabel()
        self.expiration_label = QLabel()
        self.features_label = QLabel()
        self.customer_label = QLabel()
        
        for label in [self.key_label, self.type_label, self.status_label,
                     self.expiration_label, self.features_label, self.customer_label]:
            details_layout.addWidget(label)
            
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Actions Group
        actions_group = QGroupBox("Azioni")
        actions_layout = QVBoxLayout()
        
        deactivate_button = QPushButton("Disattiva Licenza")
        deactivate_button.clicked.connect(self._deactivate_license)
        actions_layout.addWidget(deactivate_button)
        
        refresh_button = QPushButton("Aggiorna Stato")
        refresh_button.clicked.connect(self.update_info)
        actions_layout.addWidget(refresh_button)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Add stretch to bottom
        layout.addStretch()
        
        # Load initial info
        self.update_info()
        
    def update_info(self):
        """Update license information display"""
        info = self.license_manager.get_license_info()
        if not info:
            self._show_no_license()
            return
            
        # Update labels
        self.key_label.setText(f"<b>Chiave:</b> {info['key']}")
        self.type_label.setText(f"<b>Tipo:</b> {info['metadata']['type']}")
        
        status_color = {
            'active': 'green',
            'revoked': 'red',
            'expired': 'red'
        }.get(info['status'], 'black')
        
        self.status_label.setText(
            f"<b>Stato:</b> <span style='color: {status_color};'>{info['status']}</span>"
        )
        
        if info['metadata'].get('is_lifetime'):
            expiration = "Mai (Licenza Lifetime)"
        else:
            expiration = f"{info['expiration_date']} ({info['days_remaining']} giorni rimanenti)"
        self.expiration_label.setText(f"<b>Scadenza:</b> {expiration}")
        
        features = ", ".join(info['metadata'].get('features', ['basic']))
        self.features_label.setText(f"<b>Funzionalità:</b> {features}")
        
        customer = info['metadata'].get('customer_info', {})
        if customer:
            customer_text = f"{customer.get('name', '')} - {customer.get('email', '')}"
        else:
            customer_text = "N/A"
        self.customer_label.setText(f"<b>Cliente:</b> {customer_text}")
        
    def _show_no_license(self):
        """Show placeholder text when no license is installed"""
        for label in [self.key_label, self.type_label, self.status_label,
                     self.expiration_label, self.features_label, self.customer_label]:
            label.setText("N/A")
            
    def _deactivate_license(self):
        """Handle license deactivation"""
        reply = QMessageBox.question(
            self,
            "Conferma Disattivazione",
            "Sei sicuro di voler disattivare questa licenza?\n"
            "L'applicazione verrà chiusa dopo la disattivazione.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.license_manager.deactivate_current_license():
                QMessageBox.information(
                    self,
                    "Successo",
                    "Licenza disattivata con successo.\n"
                    "L'applicazione verrà ora chiusa."
                )
                # Signal main window to close
                self.window().close()
            else:
                QMessageBox.critical(
                    self,
                    "Errore",
                    "Errore durante la disattivazione della licenza."
                ) 