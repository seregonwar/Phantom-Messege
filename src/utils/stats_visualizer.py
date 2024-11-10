import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any
from plyer import notification

class StatsVisualizer:
    def __init__(self, stats_dir: str = "stats"):
        self.stats_dir = stats_dir
        os.makedirs(stats_dir, exist_ok=True)

    def create_hourly_chart(self, hourly_stats: Dict[str, int], save: bool = True) -> str:
        """Crea un grafico delle attività orarie"""
        hours = list(range(24))
        values = [hourly_stats.get(str(h), 0) for h in hours]
        
        plt.figure(figsize=(12, 6))
        plt.bar(hours, values)
        plt.title("Distribuzione oraria dei messaggi")
        plt.xlabel("Ora del giorno")
        plt.ylabel("Numero di messaggi")
        plt.grid(True, alpha=0.3)
        
        if save:
            filename = os.path.join(self.stats_dir, f"hourly_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            plt.savefig(filename)
            plt.close()
            return filename
        plt.show()
        plt.close()
        return ""

    def create_profile_usage_chart(self, profile_usage: Dict[str, int], save: bool = True) -> str:
        """Crea un grafico dell'utilizzo dei profili"""
        profiles = list(profile_usage.keys())
        values = list(profile_usage.values())
        
        plt.figure(figsize=(10, 6))
        plt.pie(values, labels=profiles, autopct='%1.1f%%')
        plt.title("Utilizzo dei profili")
        
        if save:
            filename = os.path.join(self.stats_dir, f"profile_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            plt.savefig(filename)
            plt.close()
            return filename
        plt.show()
        plt.close()
        return ""

    def export_to_csv(self, stats: Dict[str, Any]) -> str:
        """Esporta le statistiche in formato CSV"""
        df = pd.DataFrame([stats])
        filename = os.path.join(self.stats_dir, f"stats_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        df.to_csv(filename, index=False)
        return filename

class NotificationManager:
    @staticmethod
    def send_notification(title: str, message: str):
        """Invia una notifica desktop"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_icon=None,  # e.g. 'C:\\icon_32x32.ico'
                timeout=10,  # seconds
            )
        except Exception as e:
            print(f"Errore nell'invio della notifica: {e}") 