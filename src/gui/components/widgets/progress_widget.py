from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar

class ProgressWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Progress", parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m messages")
        layout.addWidget(self.progress_bar)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.send_button = QPushButton("Send Messages")
        self.send_button.setEnabled(False)  # Disabled until a profile is loaded
        button_layout.addWidget(self.send_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def update_progress(self, value: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(value)

    def set_sending_state(self, is_sending: bool):
        self.send_button.setEnabled(not is_sending)
        self.stop_button.setEnabled(is_sending) 