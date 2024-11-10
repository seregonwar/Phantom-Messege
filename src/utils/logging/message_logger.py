import logging
import json
import os
from datetime import datetime
from typing import Dict, Any
from .handlers import UnicodeStreamHandler, RotatingFileHandler

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

    def _setup_logging(self):
        """Setup del sistema di logging con rotazione dei file"""
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configura il logger principale
        logger = logging.getLogger("NGL_Sender")
        logger.setLevel(logging.INFO)
        
        # File handler con rotazione
        file_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "ngl_sender.log"),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Stream handler per la console
        console_handler = UnicodeStreamHandler()
        
        # Formattazione
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
        )
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
                    'hourly_stats': {str(i): 0 for i in range(24)},
                    'success_rate_history': [],
                    'average_delays': []
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
        """Registra un messaggio inviato con statistiche dettagliate"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"[{status}] Message: {message[:50]}... | "
            f"Delay: {delay:.2f}s | Profile: {profile}"
        )
        
        # Aggiorna statistiche
        hour = datetime.now().hour
        self.all_time_stats['hourly_stats'][str(hour)] += 1
        
        if success:
            self.session_stats['messages_sent'] += 1
            self.all_time_stats['total_messages_sent'] += 1
            self.session_stats['total_time'] += delay
            
            # Aggiorna media dei ritardi
            self.all_time_stats['average_delays'].append(delay)
            if len(self.all_time_stats['average_delays']) > 100:  # Mantieni solo gli ultimi 100
                self.all_time_stats['average_delays'].pop(0)
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
        
        # Calcola e salva il tasso di successo
        total = self.all_time_stats['total_messages_sent'] + self.all_time_stats['total_messages_failed']
        if total > 0:
            success_rate = (self.all_time_stats['total_messages_sent'] / total) * 100
            self.all_time_stats['success_rate_history'].append(success_rate)
            if len(self.all_time_stats['success_rate_history']) > 100:
                self.all_time_stats['success_rate_history'].pop(0)

        # Salva le statistiche
        self.save_stats()

    def log_burst_protection(self):
        """Registra l'attivazione della protezione anti-burst"""
        self.logger.warning("Burst protection activated")
        self.session_stats['burst_protections_triggered'] += 1

    def get_session_summary(self) -> Dict[str, Any]:
        """Ottiene un riepilogo dettagliato della sessione corrente"""
        total_messages = self.session_stats['messages_sent'] + self.session_stats['messages_failed']
        success_rate = 0 if total_messages == 0 else (self.session_stats['messages_sent'] / total_messages) * 100
        
        return {
            'Messaggi inviati con successo': self.session_stats['messages_sent'],
            'Messaggi falliti': self.session_stats['messages_failed'],
            'Tasso di successo': f"{success_rate:.1f}%",
            'Tempo medio di attesa': (
                f"{self.session_stats['total_time'] / self.session_stats['messages_sent']:.2f}s"
                if self.session_stats['messages_sent'] > 0 else "N/A"
            ),
            'Protezioni anti-burst attivate': self.session_stats['burst_protections_triggered']
        }

    def get_all_time_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche complete e dettagliate"""
        total_messages = (
            self.all_time_stats['total_messages_sent'] + 
            self.all_time_stats['total_messages_failed']
        )
        
        return {
            'Totale messaggi inviati': self.all_time_stats['total_messages_sent'],
            'Totale messaggi falliti': self.all_time_stats['total_messages_failed'],
            'Tasso di successo globale': (
                f"{(self.all_time_stats['total_messages_sent'] / total_messages * 100):.1f}%"
                if total_messages > 0 else "N/A"
            ),
            'Profilo più utilizzato': self.all_time_stats['most_used_profile'],
            'Ora più attiva': max(
                self.all_time_stats['hourly_stats'].items(),
                key=lambda x: x[1]
            )[0],
            'Media ritardi recenti': (
                f"{sum(self.all_time_stats['average_delays'][-10:]) / 10:.2f}s"
                if self.all_time_stats['average_delays'] else "N/A"
            )
        } 