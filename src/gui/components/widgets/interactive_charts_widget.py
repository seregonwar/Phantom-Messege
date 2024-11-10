from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta

class InteractiveChartsWidget(QGroupBox):
    def __init__(self, stats_manager, parent=None):
        super().__init__("Interactive Charts", parent)
        self.stats_manager = stats_manager
        self.setup_ui()
        self.current_chart = 'hourly'

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Chart type selector
        self.chart_type = QComboBox()
        self.chart_type.addItems([
            "Hourly Distribution",
            "Success Rate",
            "Language Distribution",
            "Delays",
            "Complete Dashboard"
        ])
        self.chart_type.currentTextChanged.connect(self.change_chart)
        controls_layout.addWidget(self.chart_type)
        
        # Time range selector (for applicable charts)
        self.time_range = QComboBox()
        self.time_range.addItems([
            "Last Hour",
            "Last 24 Hours",
            "Last Week",
            "All Time"
        ])
        self.time_range.currentTextChanged.connect(self.update_chart)
        controls_layout.addWidget(self.time_range)
        
        layout.addLayout(controls_layout)
        
        # Figure and canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)
        
        # Add matplotlib toolbar
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        layout.addWidget(self.toolbar)
        
        self.setLayout(layout)
        
        # Initial chart
        self.update_chart()

    def change_chart(self, chart_type: str):
        """Change the type of chart displayed"""
        chart_map = {
            "Hourly Distribution": 'hourly',
            "Success Rate": 'success_rate',
            "Language Distribution": 'languages',
            "Delays": 'delays',
            "Complete Dashboard": 'dashboard'
        }
        self.current_chart = chart_map[chart_type]
        self.update_chart()

    def update_chart(self):
        """Update the current chart"""
        self.figure.clear()
        
        if self.current_chart == 'dashboard':
            self._create_dashboard()
        elif self.current_chart == 'hourly':
            self._create_hourly_chart()
        elif self.current_chart == 'success_rate':
            self._create_success_rate_chart()
        elif self.current_chart == 'languages':
            self._create_language_chart()
        elif self.current_chart == 'delays':
            self._create_delay_chart()
            
        self.canvas.draw()

    def _create_dashboard(self):
        """Create a dashboard with all main charts"""
        gs = self.figure.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Hourly chart
        ax1 = self.figure.add_subplot(gs[0, 0])
        self._plot_hourly_data(ax1)
        
        # Success rate
        ax2 = self.figure.add_subplot(gs[0, 1])
        self._plot_success_rate(ax2)
        
        # Language distribution
        ax3 = self.figure.add_subplot(gs[1, 0])
        self._plot_language_distribution(ax3)
        
        # Delay distribution
        ax4 = self.figure.add_subplot(gs[1, 1])
        self._plot_delays(ax4)

    def _create_hourly_chart(self):
        """Create a detailed chart of hourly distribution"""
        ax = self.figure.add_subplot(111)
        self._plot_hourly_data(ax, detailed=True)

    def _create_success_rate_chart(self):
        """Create a detailed chart of success rate"""
        ax = self.figure.add_subplot(111)
        self._plot_success_rate(ax, detailed=True)

    def _create_language_chart(self):
        """Create a detailed chart of language distribution"""
        ax = self.figure.add_subplot(111)
        self._plot_language_distribution(ax, detailed=True)

    def _create_delay_chart(self):
        """Create a detailed chart of delays"""
        ax = self.figure.add_subplot(111)
        self._plot_delays(ax, detailed=True)

    def _plot_hourly_data(self, ax, detailed=False):
        """Display hourly data"""
        stats = self.stats_manager.all_time_stats
        hours = list(range(24))
        values = [stats['hourly_stats'].get(str(h), 0) for h in hours]
        
        bars = ax.bar(hours, values)
        ax.set_title("Hourly Distribution")
        ax.set_xlabel("Hour of the Day")
        ax.set_ylabel("Number of Messages")
        
        if detailed:
            # Add values above bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom')
            
            # Format x-axis
            ax.set_xticks(hours)
            ax.set_xticklabels([f"{h:02d}:00" for h in hours], rotation=45)

    def _plot_success_rate(self, ax, detailed=False):
        """Display success rate"""
        stats = self.stats_manager.all_time_stats
        success_rate = stats.get('success_rate_history', [])
        
        if success_rate:
            x = range(len(success_rate))
            ax.plot(x, success_rate, marker='o', linestyle='-', linewidth=2, markersize=4)
            
            if detailed:
                # Add trend line
                z = np.polyfit(x, success_rate, 1)
                p = np.poly1d(z)
                ax.plot(x, p(x), "r--", alpha=0.8, label='Trend')
                ax.legend()
            
            ax.set_title("Success Rate")
            ax.set_ylabel("%")
            ax.set_ylim(0, 100)

    def _plot_language_distribution(self, ax, detailed=False):
        """Display language distribution"""
        stats = self.stats_manager.all_time_stats
        lang_stats = stats.get('language_stats', {})
        
        if lang_stats:
            labels = list(lang_stats.keys())
            sizes = list(lang_stats.values())
            
            if detailed:
                explode = [0.1] * len(labels)  # Slightly separate slices
                ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                      shadow=True, startangle=90)
            else:
                ax.pie(sizes, labels=labels, autopct='%1.1f%%')
                
            ax.set_title("Language Distribution")

    def _plot_delays(self, ax, detailed=False):
        """Display delay distribution"""
        stats = self.stats_manager.all_time_stats
        delays = stats.get('average_delays', [])
        
        if delays:
            if detailed:
                # Create a detailed histogram
                n, bins, patches = ax.hist(delays, bins=30, density=True, alpha=0.7)
                
                # Add density line
                mu = np.mean(delays)
                sigma = np.std(delays)
                x = np.linspace(min(delays), max(delays), 100)
                ax.plot(x, 1/(sigma * np.sqrt(2 * np.pi)) *
                       np.exp(- (x - mu)**2 / (2 * sigma**2)),
                       linewidth=2, label='Normal Distribution')
                ax.legend()
            else:
                ax.hist(delays, bins=20)
                
            ax.set_title("Delay Distribution")
            ax.set_xlabel("Seconds")