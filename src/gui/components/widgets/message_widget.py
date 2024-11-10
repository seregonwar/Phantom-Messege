from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit, QCheckBox

class MessageWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Message", parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Enter the message...")
        layout.addWidget(self.message_input)
        
        self.use_random = QCheckBox("Generate random messages")
        layout.addWidget(self.use_random)
        
        self.setLayout(layout)

    def toggle_message_input(self, state):
        self.message_input.setEnabled(not state)
        if state:
            self.message_input.setPlaceholderText("Automatic generation active...")
        else:
            self.message_input.setPlaceholderText("Enter the message...") 