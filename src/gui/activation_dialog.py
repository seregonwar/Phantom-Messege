from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
import os
from ..core.license_manager import LicenseManager

class ActivationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_manager = LicenseManager()
        self.license_file_path = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Attivazione Prodotto")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(
            "Per utilizzare questo software è necessaria una licenza valida.\n"
            "Seleziona il file di licenza (.bin) per attivare il prodotto."
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # File selection
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("Nessun file selezionato")
        self.file_label.setStyleSheet("color: gray;")
        file_layout.addWidget(self.file_label)
        
        browse_button = QPushButton("Sfoglia...")
        browse_button.clicked.connect(self.browse_license_file)
        file_layout.addWidget(browse_button)
        
        layout.addLayout(file_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.activate_button = QPushButton("Attiva")
        self.activate_button.clicked.connect(self.activate_license)
        self.activate_button.setEnabled(False)
        
        self.quit_button = QPushButton("Esci")
        self.quit_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.activate_button)
        button_layout.addWidget(self.quit_button)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def browse_license_file(self):
        """Apre il dialogo per selezionare il file di licenza"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file di licenza",
            "",
            "File di licenza (*.bin);;Tutti i file (*)"
        )
        
        if file_path:
            self.license_file_path = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.file_label.setStyleSheet("color: black;")
            self.activate_button.setEnabled(True)
            self.status_label.setText("")
        
    def activate_license(self):
        """Attiva la licenza usando il file selezionato"""
        if not self.license_file_path:
            self.status_label.setText("Seleziona un file di licenza valido")
            return
            
        try:
            # Installa e verifica la licenza
            if (self.license_manager.install_license(self.license_file_path) and 
                self.license_manager.verify_license()):
                QMessageBox.information(
                    self,
                    "Successo",
                    "Licenza attivata con successo!"
                )
                self.accept()
            else:
                self.status_label.setText("File di licenza non valido o già in uso")
                
        except Exception as e:
            self.status_label.setText(f"Errore durante l'attivazione: {str(e)}")