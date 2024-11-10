import json
import os
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from .stats_analyzer import StatsAnalyzer
from .stats_visualizer import StatsVisualizer

class StatsManager:
    def __init__(self, stats_dir: str = "stats"):
        self.stats_dir = stats_dir
        self.stats_file = os.path.join(stats_dir, "stats.json")
        self.analyzer = StatsAnalyzer()
        self.visualizer = StatsVisualizer(stats_dir)
        
        # Crea la directory se non esiste
        os.makedirs(stats_dir, exist_ok=True)
        
        # Statistiche della sessione corrente
        self.session_stats = {
            'messages_sent': 0,
            'messages_failed': 0,
            'total_time': 0,
            'average_delay': 0,
            'burst_protections_triggered': 0,
            'languages_used': {},
            'styles_used': {},
            'start_time': datetime.now().isoformat()
        }
        
        self.all_time_stats = {
            'total_messages_sent': 0,
            'total_messages_failed': 0,
            'sessions_count': 0,
            'most_used_profile': None,
            'profile_usage': {},
            'hourly_stats': {str(i): 0 for i in range(24)},
            'language_stats': {},
            'style_stats': {},
            'success_rate_history': [],
            'average_delays': []
        }
        
        self.load_stats()

    def load_stats(self):
        """Carica le statistiche dal file"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.all_time_stats = json.load(f)
        except Exception as e:
            print(f"Errore nel caricamento delle statistiche: {e}")

    def save_stats(self):
        """Salva le statistiche su file"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_time_stats, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Errore nel salvataggio delle statistiche: {e}")

    def get_session_summary(self) -> Dict[str, Any]:
        """Ottiene un riepilogo della sessione corrente"""
        total = self.session_stats['messages_sent'] + self.session_stats['messages_failed']
        success_rate = 0 if total == 0 else (
            self.session_stats['messages_sent'] / total * 100
        )
        
        return {
            'Messaggi inviati': self.session_stats['messages_sent'],
            'Messaggi falliti': self.session_stats['messages_failed'],
            'Tasso di successo': f"{success_rate:.1f}%",
            'Tempo medio di attesa': (
                f"{self.session_stats['average_delay']:.2f}s"
                if self.session_stats['messages_sent'] > 0 else "N/A"
            ),
            'Lingue utilizzate': dict(self.session_stats['languages_used']),
            'Stili utilizzati': dict(self.session_stats['styles_used']),
            'Inizio sessione': self.session_stats['start_time']
        }

    def get_all_time_stats(self) -> Dict[str, Any]:
        """Ottiene le statistiche complete"""
        total_messages = (
            self.all_time_stats['total_messages_sent'] + 
            self.all_time_stats['total_messages_failed']
        )
        
        return {
            'Totale messaggi inviati': self.all_time_stats['total_messages_sent'],
            'Totale messaggi falliti': self.all_time_stats['total_messages_failed'],
            'Tasso globale': (
                f"{(self.all_time_stats['total_messages_sent'] / total_messages * 100):.1f}%"
                if total_messages > 0 else "N/A"
            ),
            'Profilo più usato': self.all_time_stats['most_used_profile'],
            'Ora più attiva': max(
                self.all_time_stats['hourly_stats'].items(),
                key=lambda x: int(x[1])
            )[0] if self.all_time_stats['hourly_stats'] else "N/A"
        }

    def get_analysis(self) -> Dict[str, Any]:
        """Ottiene un'analisi completa delle statistiche"""
        return self.analyzer.get_comprehensive_analysis(self.all_time_stats)

    def export_stats(self, format: str = 'all') -> Dict[str, str]:
        """Esporta le statistiche nei formati richiesti"""
        exports = {}
        
        if format in ['all', 'charts']:
            # Crea grafici
            exports['hourly_chart'] = self.visualizer.create_hourly_chart(
                self.all_time_stats['hourly_stats']
            )
            exports['success_rate_chart'] = self.visualizer.create_success_rate_chart(
                self.all_time_stats.get('success_rate_history', [])
            )
        
        if format in ['all', 'csv']:
            # Esporta CSV
            exports['csv'] = self.visualizer.export_to_csv({
                **self.get_session_summary(),
                **self.all_time_stats
            })
        
        return exports

    def end_session(self):
        """Finalizza la sessione corrente"""
        self.all_time_stats['sessions_count'] += 1
        self.save_stats()