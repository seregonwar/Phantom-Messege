from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import QTimer
import time

class RealtimeStatsWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Realtime Statistics", parent)
        self.setup_ui()
        self.start_timer()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Success rate
        self.success_rate_label = QLabel("Success rate: 0%")
        layout.addWidget(self.success_rate_label)
        
        self.success_rate_bar = QProgressBar()
        self.success_rate_bar.setRange(0, 100)
        layout.addWidget(self.success_rate_bar)
        
        # Message rate
        self.message_rate_label = QLabel("Messages per minute: 0")
        layout.addWidget(self.message_rate_label)
        
        # Average delay
        self.avg_delay_label = QLabel("Average delay: 0.0s")
        layout.addWidget(self.avg_delay_label)
        
        # Session duration
        self.duration_label = QLabel("Session duration: 00:00:00")
        layout.addWidget(self.duration_label)
        
        self.setLayout(layout)
        
        # Initialize stats
        self.stats = {
            'successful': 0,
            'failed': 0,
            'start_time': None,
            'messages_last_minute': [],
            'total_delay': 0
        }

    def start_timer(self):
        """Start the timer for updating statistics"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # Update every second

    def update_stats(self):
        """Update the displayed statistics"""
        if self.stats['start_time']:
            # Calculate success rate
            total = self.stats['successful'] + self.stats['failed']
            if total > 0:
                success_rate = (self.stats['successful'] / total) * 100
                self.success_rate_label.setText(f"Success rate: {success_rate:.1f}%")
                self.success_rate_bar.setValue(int(success_rate))
            
            # Calculate messages per minute
            current_time = time.time()
            self.stats['messages_last_minute'] = [
                t for t in self.stats['messages_last_minute']
                if current_time - t <= 60
            ]
            rate = len(self.stats['messages_last_minute'])
            self.message_rate_label.setText(f"Messages per minute: {rate}")
            
            # Calculate average delay
            if self.stats['successful'] > 0:
                avg_delay = self.stats['total_delay'] / self.stats['successful']
                self.avg_delay_label.setText(f"Average delay: {avg_delay:.1f}s")
            
            # Update session duration
            duration = int(current_time - self.stats['start_time'])
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            self.duration_label.setText(
                f"Session duration: {hours:02d}:{minutes:02d}:{seconds:02d}"
            )

    def log_message(self, success: bool, delay: float):
        """Log a new message in the statistics"""
        if self.stats['start_time'] is None:
            self.stats['start_time'] = time.time()
        
        if success:
            self.stats['successful'] += 1
            self.stats['total_delay'] += delay
        else:
            self.stats['failed'] += 1
            
        self.stats['messages_last_minute'].append(time.time()) 