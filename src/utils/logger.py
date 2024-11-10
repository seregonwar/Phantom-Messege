import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any
from .stats_visualizer import StatsVisualizer, NotificationManager

class UnicodeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Forza l'encoding UTF-8 per il stream
            stream = sys.stdout if stream is sys.stderr else stream
            stream.buffer.write(msg.encode('utf-8'))
            stream.buffer.write(self.terminator.encode('utf-8'))
            self.flush()
        except Exception:
            self.handleError(record)

class MessageLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.stats_file = os.path.join(log_dir, "stats.json")
        self.session_stats = {
            'messages_sent': 0,
            'messages_failed': 0,
            'total_time': 0,
            'average_delay': 0,
            'burst_protections_triggered': 0
        }
        self._setup_logging()
        self._load_stats()
        self.stats_visualizer = StatsVisualizer()
        self.notification_manager = NotificationManager()

    def _setup_logging(self):
        """Setup del sistema di logging"""
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configura il logger con supporto Unicode
        logger = logging.getLogger("NGL_Sender")
        logger.setLevel(logging.INFO)
        
        # File handler con encoding UTF-8
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, f"ngl_sender_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            encoding='utf-8'
        )
        
        # Stream handler personalizzato per output console
        console_handler = UnicodeStreamHandler()
        
        # Formattazione
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.logger = logger

    def _load_stats(self):
        """Carica le statistiche dal file"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.all_time_stats = json.load(f)
            else:
                self.all_time_stats = {
                    'total_messages_sent': 0,
                    'total_messages_failed': 0,
                    'sessions_count': 0,
                    'most_used_profile': None,
                    'profile_usage': {},
                    'hourly_stats': {str(i): 0 for i in range(24)}
                }
        except Exception as e:
            self.logger.error(f"Errore nel caricamento delle statistiche: {e}")
            self.all_time_stats = {}

    def save_stats(self):
        """Salva le statistiche su file"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_time_stats, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Errore nel salvataggio delle statistiche: {e}")

    def log_message(self, message: str, success: bool, delay: float, profile: str):
        """Registra un messaggio inviato"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"[{status}] Message: {message[:50]}... | Delay: {delay:.2f}s | Profile: {profile}")
        
        # Aggiorna statistiche
        hour = datetime.now().hour
        self.all_time_stats['hourly_stats'][str(hour)] += 1
        
        if success:
            self.session_stats['messages_sent'] += 1
            self.all_time_stats['total_messages_sent'] += 1
        else:
            self.session_stats['messages_failed'] += 1
            self.all_time_stats['total_messages_failed'] += 1
            
        # Aggiorna statistiche del profilo
        if profile not in self.all_time_stats['profile_usage']:
            self.all_time_stats['profile_usage'][profile] = 0
        self.all_time_stats['profile_usage'][profile] += 1
        
        # Aggiorna il profilo più usato
        most_used = max(self.all_time_stats['profile_usage'].items(), key=lambda x: x[1])
        self.all_time_stats['most_used_profile'] = most_used[0]
        
        self.session_stats['average_delay'] = (
            (self.session_stats['average_delay'] * (self.session_stats['messages_sent'] - 1) + delay) / 
            self.session_stats['messages_sent']
        ) if self.session_stats['messages_sent'] > 0 else delay

        # Controlla traguardi
        self.notify_milestone()

    def log_burst_protection(self):
        """Registra l'attivazione della protezione anti-burst"""
        self.logger.warning("Burst protection activated")
        self.session_stats['burst_protections_triggered'] += 1

    def get_session_summary(self) -> Dict[str, Any]:
        """Ottiene un riepilogo della sessione corrente"""
        return {
            'Messaggi inviati con successo': self.session_stats['messages_sent'],
            'Messaggi falliti': self.session_stats['messages_failed'],
            'Tempo medio di attesa': f"{self.session_stats['average_delay']:.2f}s",
            'Protezioni anti-burst attivate': self.session_stats['burst_protections_triggered']
        }

    def get_all_time_stats(self) -> Dict[str, Any]:
        """Ottiene le statistiche complete"""
        return {
            'Totale messaggi inviati': self.all_time_stats['total_messages_sent'],
            'Totale messaggi falliti': self.all_time_stats['total_messages_failed'],
            'Profilo più utilizzato': self.all_time_stats['most_used_profile'],
            'Ora più attiva': max(self.all_time_stats['hourly_stats'].items(), key=lambda x: x[1])[0]
        }

    def print_stats(self):
        """Stampa un riepilogo delle statistiche"""
        print("\n=== Statistiche Sessione Corrente ===")
        for key, value in self.get_session_summary().items():
            print(f"{key}: {value}")
            
        print("\n=== Statistiche Totali ===")
        for key, value in self.get_all_time_stats().items():
            print(f"{key}: {value}")

    def export_stats(self):
        """Esporta tutte le statistiche"""
        # Crea grafici
        hourly_chart = self.stats_visualizer.create_hourly_chart(
            self.all_time_stats['hourly_stats']
        )
        profile_chart = self.stats_visualizer.create_profile_usage_chart(
            self.all_time_stats['profile_usage']
        )
        
        # Esporta CSV
        csv_file = self.stats_visualizer.export_to_csv({
            **self.get_session_summary(),
            **self.get_all_time_stats()
        })
        
        return {
            'hourly_chart': hourly_chart,
            'profile_chart': profile_chart,
            'csv_export': csv_file
        }

    def notify_milestone(self):
        """Invia notifiche per traguardi raggiunti"""
        total_messages = self.all_time_stats['total_messages_sent']
        
        # Notifica ogni 100 messaggi
        if total_messages > 0 and total_messages % 100 == 0:
            self.notification_manager.send_notification(
                "Traguardo Raggiunto!",
                f"Hai inviato {total_messages} messaggi in totale!"
            )
        
        # Notifica per sessioni lunghe
        if self.session_stats['messages_sent'] > 50:
            self.notification_manager.send_notification(
                "Sessione Lunga",
                "Hai inviato più di 50 messaggi in questa sessione. Considera una pausa."
            )