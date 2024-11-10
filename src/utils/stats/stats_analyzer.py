from typing import Dict, Any, List
import numpy as np
from datetime import datetime, timedelta

class StatsAnalyzer:
    def __init__(self):
        self.success_threshold = 0.8  # 80% tasso di successo minimo
        self.burst_threshold = 0.7    # 70% capacità burst

    def analyze_success_rate(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analizza il tasso di successo e fornisce suggerimenti"""
        total = stats['total_messages_sent'] + stats['total_messages_failed']
        if total == 0:
            return {"status": "insufficient_data"}
            
        success_rate = stats['total_messages_sent'] / total
        
        analysis = {
            "success_rate": success_rate,
            "status": "good" if success_rate >= self.success_threshold else "warning",
            "suggestions": []
        }
        
        if success_rate < self.success_threshold:
            analysis["suggestions"].append(
                "Il tasso di successo è basso. Prova ad aumentare i delay tra i messaggi."
            )
            
        return analysis

    def analyze_timing(self, delays: List[float]) -> Dict[str, Any]:
        """Analizza i pattern temporali e suggerisce miglioramenti"""
        if not delays:
            return {"status": "insufficient_data"}
            
        mean_delay = np.mean(delays)
        std_delay = np.std(delays)
        
        analysis = {
            "mean_delay": mean_delay,
            "std_delay": std_delay,
            "status": "good" if std_delay / mean_delay < 0.3 else "warning",
            "suggestions": []
        }
        
        if std_delay / mean_delay > 0.3:
            analysis["suggestions"].append(
                "La variazione nei delay è alta. Prova a mantenere timing più costanti."
            )
            
        return analysis

    def analyze_burst_protection(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analizza l'efficacia della protezione burst"""
        if 'burst_protections_triggered' not in stats:
            return {"status": "insufficient_data"}
            
        total_messages = stats['total_messages_sent'] + stats['total_messages_failed']
        if total_messages == 0:
            return {"status": "insufficient_data"}
            
        burst_rate = stats['burst_protections_triggered'] / total_messages
        
        analysis = {
            "burst_rate": burst_rate,
            "status": "good" if burst_rate < self.burst_threshold else "warning",
            "suggestions": []
        }
        
        if burst_rate >= self.burst_threshold:
            analysis["suggestions"].append(
                "La protezione burst si attiva spesso. Considera di ridurre la frequenza dei messaggi."
            )
            
        return analysis

    def predict_best_timing(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Predice i migliori timing basandosi sulle statistiche"""
        hourly_stats = stats.get('hourly_stats', {})
        if not hourly_stats:
            return {"status": "insufficient_data"}
            
        # Trova le ore con più successo
        best_hours = sorted(
            hourly_stats.items(),
            key=lambda x: int(x[1]),
            reverse=True
        )[:3]
        
        return {
            "status": "success",
            "best_hours": [int(hour) for hour, _ in best_hours],
            "suggestions": [
                f"Gli orari migliori per l'invio sono: {', '.join(f'{h}:00' for h, _ in best_hours)}"
            ]
        }

    def get_comprehensive_analysis(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Fornisce un'analisi completa con tutti i suggerimenti"""
        success_analysis = self.analyze_success_rate(stats)
        timing_analysis = self.analyze_timing(stats.get('average_delays', []))
        burst_analysis = self.analyze_burst_protection(stats)
        timing_prediction = self.predict_best_timing(stats)
        
        all_suggestions = []
        for analysis in [success_analysis, timing_analysis, burst_analysis, timing_prediction]:
            if analysis.get("status") != "insufficient_data":
                all_suggestions.extend(analysis.get("suggestions", []))
        
        return {
            "overall_status": (
                "good" if all(
                    a.get("status", "") == "good" 
                    for a in [success_analysis, timing_analysis, burst_analysis]
                ) else "warning"
            ),
            "success_analysis": success_analysis,
            "timing_analysis": timing_analysis,
            "burst_analysis": burst_analysis,
            "timing_prediction": timing_prediction,
            "suggestions": all_suggestions
        } 