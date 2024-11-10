from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTabWidget, QWidget, QLabel
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from ....utils.stats import StatsVisualizer, StatsManager

class StatsDashboardWidget(QGroupBox):
    def __init__(self, stats_manager: StatsManager, parent=None):
        super().__init__("Statistics Dashboard", parent)
        self.stats_manager = stats_manager
        self.stats_visualizer = StatsVisualizer()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Tabs for different types of charts
        tabs = QTabWidget()
        
        # Hourly distribution tab
        hourly_tab = QWidget()
        hourly_layout = QVBoxLayout(hourly_tab)
        self.hourly_canvas = self.stats_visualizer.create_hourly_chart(
            self.stats_manager.all_time_stats['hourly_stats'],
            interactive=True
        )
        hourly_layout.addWidget(self.hourly_canvas)
        tabs.addTab(hourly_tab, "Hourly Distribution")
        
        # Success rate tab
        success_tab = QWidget()
        success_layout = QVBoxLayout(success_tab)
        self.success_canvas = self.stats_visualizer.create_success_rate_chart(
            self.stats_manager.all_time_stats.get('success_rate_history', []),
            interactive=True
        )
        success_layout.addWidget(self.success_canvas)
        tabs.addTab(success_tab, "Success Rate")
        
        # Language distribution tab
        lang_tab = QWidget()
        lang_layout = QVBoxLayout(lang_tab)
        self.lang_canvas = self.stats_visualizer.create_language_distribution_chart(
            self.stats_manager.all_time_stats.get('language_stats', {}),
            interactive=True
        )
        lang_layout.addWidget(self.lang_canvas)
        tabs.addTab(lang_tab, "Languages Used")
        
        # Delay distribution tab
        delay_tab = QWidget()
        delay_layout = QVBoxLayout(delay_tab)
        self.delay_canvas = self.stats_visualizer.create_delay_distribution_chart(
            self.stats_manager.all_time_stats.get('average_delays', []),
            interactive=True
        )
        delay_layout.addWidget(self.delay_canvas)
        tabs.addTab(delay_tab, "Delay Distribution")
        
        layout.addWidget(tabs)
        
        # Statistics summary
        summary_layout = QHBoxLayout()
        
        # Current session statistics
        session_group = QGroupBox("Current Session")
        session_layout = QVBoxLayout()
        self.session_labels = {}
        for key in ['Messages Sent', 'Messages Failed', 'Success Rate', 'Average Time']:
            self.session_labels[key] = QLabel(f"{key}: 0")
            session_layout.addWidget(self.session_labels[key])
        session_group.setLayout(session_layout)
        summary_layout.addWidget(session_group)
        
        # Total statistics
        total_group = QGroupBox("Total Statistics")
        total_layout = QVBoxLayout()
        self.total_labels = {}
        for key in ['Total Messages', 'Global Rate', 'Most Used Profile', 'Most Active Hour']:
            self.total_labels[key] = QLabel(f"{key}: 0")
            total_layout.addWidget(self.total_labels[key])
        total_group.setLayout(total_layout)
        summary_layout.addWidget(total_group)
        
        layout.addLayout(summary_layout)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.update_stats)
        controls_layout.addWidget(refresh_button)
        
        export_button = QPushButton("Export")
        export_button.clicked.connect(self.export_stats)
        controls_layout.addWidget(export_button)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)

    def update_stats(self):
        """Update all charts and statistics"""
        # Update charts
        self.hourly_canvas.figure.clear()
        self.success_canvas.figure.clear()
        self.lang_canvas.figure.clear()
        self.delay_canvas.figure.clear()
        
        # Recreate charts with updated data
        self.hourly_canvas = self.stats_visualizer.create_hourly_chart(
            self.stats_manager.all_time_stats['hourly_stats'],
            interactive=True
        )
        self.success_canvas = self.stats_visualizer.create_success_rate_chart(
            self.stats_manager.all_time_stats.get('success_rate_history', []),
            interactive=True
        )
        self.lang_canvas = self.stats_visualizer.create_language_distribution_chart(
            self.stats_manager.all_time_stats.get('language_stats', {}),
            interactive=True
        )
        self.delay_canvas = self.stats_visualizer.create_delay_distribution_chart(
            self.stats_manager.all_time_stats.get('average_delays', []),
            interactive=True
        )
        
        # Update labels
        session_stats = self.stats_manager.get_session_summary()
        for key, label in self.session_labels.items():
            label.setText(f"{key}: {session_stats.get(key, 'N/A')}")
            
        total_stats = self.stats_manager.get_all_time_stats()
        for key, label in self.total_labels.items():
            label.setText(f"{key}: {total_stats.get(key, 'N/A')}")

    def export_stats(self):
        """Export all statistics"""
        exports = self.stats_manager.export_stats()
        if exports:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Export Completed",
                f"Statistics exported to:\n{exports['csv']}\n\nCharts saved to:\n" +
                "\n".join(f"- {name}: {path}" for name, path in exports.items() if name != 'csv')
            ) 