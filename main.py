import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QDialog, QProgressDialog, QMessageBox
from PyQt6.QtCore import Qt, QLocale, QThread, pyqtSignal
from src.gui import MainWindow
from src.gui.activation_dialog import ActivationDialog
from src.core.license_manager import LicenseManager
from src.core.dropbox_sync import DropboxSync
from src.text_generator import TextGenerator
from src.utils.stats import StatsManager
from tools.db_manager import LicenseDBManager

def verify_license(license_manager: LicenseManager, parent=None) -> bool:
    """Verifica la licenza locale e online"""
    try:
        # Verifica se esiste il file di licenza locale
        if os.path.exists(os.path.join("config", "license.bin")):
            # Verifica veloce offline
            if license_manager.quick_verify_license():
                # Verifica online
                progress = QProgressDialog(
                    "Verifica licenza online...", 
                    None, 0, 100, parent
                )
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.show()
                
                # Controlla lo stato su Dropbox
                progress.setValue(50)
                if license_manager.verify_license(parent):
                    progress.setValue(100)
                    return True
                    
                progress.close()
                QMessageBox.warning(
                    parent,
                    "Errore",
                    "La licenza non è più valida o è stata revocata.\n"
                    "È necessario riattivare il prodotto."
                )
        
        # Se non c'è licenza o non è valida, mostra il dialogo di attivazione
        activation_dialog = ActivationDialog(parent)
        if activation_dialog.exec() != QDialog.DialogCode.Accepted:
            logging.info("User cancelled activation")
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"Error verifying license: {e}")
        QMessageBox.critical(
            parent,
            "Errore",
            f"Errore durante la verifica della licenza:\n{str(e)}"
        )
        return False

class BackgroundInitializer(QThread):
    finished = pyqtSignal()
    
    def __init__(self, license_manager, dropbox):
        super().__init__()
        self.license_manager = license_manager
        self.dropbox = dropbox
        
    def run(self):
        """Esegui le operazioni di inizializzazione in background"""
        try:
            # Sincronizza con Dropbox
            self.dropbox.get_all_licenses()
            
            # Avvia il thread di heartbeat
            self.license_manager._start_heartbeat()
            
        except Exception as e:
            logging.error(f"Background initialization error: {e}")
        finally:
            self.finished.emit()

def setup_logging():
    """Configure the logging system"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                os.path.join(log_dir, "app.log"),
                encoding='utf-8'
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )

def setup_environment():
    """Configure the application environment"""
    # Create necessary directories
    for directory in ["logs", "stats", "config"]:
        os.makedirs(directory, exist_ok=True)
    
    # Set environment variables
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    # Set number format to avoid decimal issues
    locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
    QLocale.setDefault(locale)

def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

def main():
    """Main application function"""
    try:
        # Configure environment
        setup_logging()
        setup_environment()
        
        # Set exception handler
        sys.excepthook = handle_exception
        
        # Create application
        app = QApplication(sys.argv)
        
        # Create managers and services
        license_manager = LicenseManager()
        dropbox = DropboxSync()
        text_generator = TextGenerator()
        stats_manager = StatsManager()
        db_manager = LicenseDBManager()
        
        # Verifica la connessione internet
        if not dropbox.check_connection():
            QMessageBox.critical(
                None,
                "Errore",
                "È necessaria una connessione internet per utilizzare l'applicazione."
            )
            sys.exit(1)
        
        # Verifica la licenza
        if not verify_license(license_manager):
            sys.exit(0)
            
        # Create main window with dependencies
        window = MainWindow(
            text_generator=text_generator,
            stats_manager=stats_manager,
            db_manager=db_manager
        )
        
        # Create and start background initialization
        background_init = BackgroundInitializer(license_manager, dropbox)
        background_init.finished.connect(window.on_background_init_complete)
        background_init.start()
        
        # Show window immediately
        window.show()
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logging.error(f"Error during application startup: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Errore",
            f"Errore durante l'avvio dell'applicazione:\n{str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
