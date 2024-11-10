import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import Dict, Any, List
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

class StatsVisualizer:
    def __init__(self, stats_dir: str = "stats"):
        self.stats_dir = stats_dir
        os.makedirs(stats_dir, exist_ok=True)
        
        # Imposta lo stile dei grafici
        if HAS_SEABORN:
            sns.set_theme(style="darkgrid")
            sns.set_palette("husl")
        else:
            plt.style.use('default')

    def create_hourly_chart(self, hourly_stats: Dict[str, int], 
                          interactive: bool = False) -> Any:
        """Crea un grafico delle attività orarie"""
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        hours = list(range(24))
        values = [hourly_stats.get(str(h), 0) for h in hours]
        
        # Crea il grafico a barre
        bars = ax.bar(hours, values)
        
        # Aggiungi etichette e titolo
        ax.set_title("Distribuzione oraria dei messaggi", pad=20)
        ax.set_xlabel("Ora del giorno")
        ax.set_ylabel("Numero di messaggi")
        
        # Aggiungi griglia
        ax.grid(True, alpha=0.3)
        
        # Aggiungi valori sopra le barre
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom')
        
        # Formatta l'asse x per mostrare tutte le ore
        ax.set_xticks(hours)
        ax.set_xticklabels([f"{h:02d}:00" for h in hours], rotation=45)
        
        if interactive:
            return FigureCanvasQTAgg(fig)
        else:
            # Salva il grafico
            filename = os.path.join(
                self.stats_dir, 
                f"hourly_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            fig.savefig(filename, bbox_inches='tight', dpi=300)
            plt.close(fig)
            return filename

    def create_success_rate_chart(self, success_history: List[float], 
                                interactive: bool = False) -> Any:
        """Crea un grafico del tasso di successo nel tempo"""
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        if not success_history:  # Se non ci sono dati
            ax.text(0.5, 0.5, 'Nessun dato disponibile',
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes)
            if interactive:
                return FigureCanvasQTAgg(fig)
            else:
                filename = os.path.join(
                    self.stats_dir, 
                    f"success_rate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )
                fig.savefig(filename, bbox_inches='tight', dpi=300)
                plt.close(fig)
                return filename
        
        # Crea il grafico lineare
        x = range(len(success_history))
        ax.plot(x, success_history, marker='o', linestyle='-', linewidth=2, markersize=4)
        
        # Aggiungi una linea di trend
        z = np.polyfit(x, success_history, 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), "r--", alpha=0.8, label='Trend')
        
        # Aggiungi etichette e titolo
        ax.set_title("Andamento del tasso di successo", pad=20)
        ax.set_xlabel("Numero di sessioni")
        ax.set_ylabel("Tasso di successo (%)")
        
        # Aggiungi griglia e legenda
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Imposta i limiti dell'asse y
        ax.set_ylim(0, 100)
        
        if interactive:
            return FigureCanvasQTAgg(fig)
        else:
            filename = os.path.join(
                self.stats_dir, 
                f"success_rate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            fig.savefig(filename, bbox_inches='tight', dpi=300)
            plt.close(fig)
            return filename

    def create_language_distribution_chart(self, language_stats: Dict[str, int], 
                                        interactive: bool = False) -> Any:
        """Crea un grafico a torta della distribuzione delle lingue"""
        fig = Figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
        
        # Prepara i dati
        labels = list(language_stats.keys())
        sizes = list(language_stats.values())
        
        # Crea il grafico a torta
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                        textprops={'color': "w"})
        
        # Aggiungi titolo
        ax.set_title("Distribuzione delle lingue utilizzate", pad=20)
        
        if interactive:
            return FigureCanvasQTAgg(fig)
        else:
            filename = os.path.join(
                self.stats_dir, 
                f"language_dist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            fig.savefig(filename, bbox_inches='tight', dpi=300)
            plt.close(fig)
            return filename

    def create_delay_distribution_chart(self, delays: List[float], 
                                     interactive: bool = False) -> Any:
        """Crea un istogramma della distribuzione dei ritardi"""
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Crea l'istogramma
        n, bins, patches = ax.hist(delays, bins=30, density=True, alpha=0.7)
        
        # Aggiungi una linea di densità
        density = sns.kdeplot(data=delays, ax=ax, color='red', label='Densità')
        
        # Aggiungi etichette e titolo
        ax.set_title("Distribuzione dei ritardi", pad=20)
        ax.set_xlabel("Ritardo (secondi)")
        ax.set_ylabel("Densità")
        
        # Aggiungi griglia e legenda
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        if interactive:
            return FigureCanvasQTAgg(fig)
        else:
            filename = os.path.join(
                self.stats_dir, 
                f"delay_dist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            fig.savefig(filename, bbox_inches='tight', dpi=300)
            plt.close(fig)
            return filename

    def create_summary_dashboard(self, stats: Dict[str, Any]) -> FigureCanvasQTAgg:
        """Crea un dashboard con tutti i grafici principali"""
        fig = Figure(figsize=(15, 10))
        
        # Crea una griglia 2x2 per i grafici
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Grafico orario
        ax1 = fig.add_subplot(gs[0, 0])
        hours = list(range(24))
        values = [stats['hourly_stats'].get(str(h), 0) for h in hours]
        ax1.bar(hours, values)
        ax1.set_title("Distribuzione oraria")
        ax1.set_xlabel("Ora")
        ax1.set_ylabel("Messaggi")
        
        # Tasso di successo
        ax2 = fig.add_subplot(gs[0, 1])
        success_rate = stats.get('success_rate_history', [])
        if success_rate:
            ax2.plot(success_rate)
            ax2.set_title("Tasso di successo")
            ax2.set_ylabel("%")
        
        # Distribuzione lingue
        ax3 = fig.add_subplot(gs[1, 0])
        lang_stats = stats.get('language_stats', {})
        if lang_stats:
            ax3.pie(lang_stats.values(), labels=lang_stats.keys(), autopct='%1.1f%%')
            ax3.set_title("Lingue utilizzate")
        
        # Ritardi
        ax4 = fig.add_subplot(gs[1, 1])
        delays = stats.get('average_delays', [])
        if delays:
            ax4.hist(delays, bins=20)
            ax4.set_title("Distribuzione ritardi")
            ax4.set_xlabel("Secondi")
        
        return FigureCanvasQTAgg(fig)

    def export_to_csv(self, stats: Dict[str, Any]) -> str:
        """Esporta le statistiche in formato CSV"""
        df = pd.DataFrame([stats])
        filename = os.path.join(
            self.stats_dir, 
            f"stats_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        df.to_csv(filename, index=False)
        return filename 