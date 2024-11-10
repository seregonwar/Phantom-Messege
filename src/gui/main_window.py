from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QSpinBox, QLabel, 
    QComboBox, QTabWidget, QProgressBar, QGroupBox,
    QSlider, QCheckBox, QMenuBar, QMenu, QStatusBar,
    QFileDialog, QLineEdit, QStackedWidget, QGridLayout,
    QScrollArea, QMessageBox, QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QAction, QIcon, QDesktopServices, QFont, QPixmap
from ..core.message_sender import MessageSender
from ..config.settings import ConfigManager
from ..parsers.page_parser import NGLPageParser
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from .styles import Themes, get_stylesheet
from .components.widgets.enhanced_preview_widget import EnhancedPreviewWidget
from ..text_generator import TextGenerator
import os
from .components.widgets.stats_dashboard_widget import StatsDashboardWidget
from ..utils.stats import StatsManager
from .components.widgets.sidebar_widget import SidebarWidget
from .icons import ICONS
from .activation_dialog import ActivationDialog
from ..core.license_manager import LicenseManager
from .components.license_info_widget import LicenseInfoWidget
import logging
from .components.support_widget import SupportWidget, AgentChatDialog

class SendMessageWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(tuple)
    message_sent = pyqtSignal(str, bool)

    def __init__(self, sender, message, count, use_random):
        super().__init__()
        self.sender = sender
        self.message = message
        self.count = count
        self.use_random = use_random

    def run(self):
        successful = 0
        failed = 0
        
        for i in range(self.count):
            success = self.sender.send_message(self.message, self.use_random)
            if success:
                successful += 1
            else:
                failed += 1
            
            self.progress.emit(int((i + 1) * 100 / self.count))
            self.message_sent.emit(self.message, success)
            
        self.finished.emit((successful, failed))

class MainWindow(QMainWindow):
    def __init__(self, text_generator=None, stats_manager=None, db_manager=None):
        super().__init__()
        
        # Inizializza i servizi
        self.text_generator = text_generator
        self.stats_manager = stats_manager
        self.db_manager = db_manager
        
        # Disabilita la finestra durante l'inizializzazione
        self.setEnabled(False)
        
        # Mostra un dialogo di caricamento
        self.loading_dialog = QProgressDialog(
            "Inizializzazione in corso...", 
            None, 0, 0, self
        )
        self.loading_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.loading_dialog.setAutoClose(True)
        self.loading_dialog.show()
        
        # Setup UI
        self.setup_ui()

    def setup_menubar(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        export_action = QAction("Export statistics", self)
        export_action.triggered.connect(self.export_stats)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View Menu
        view_menu = menubar.addMenu("View")
        
        theme_menu = view_menu.addMenu("Theme")
        
        dark_action = QAction("Dark", self)
        dark_action.triggered.connect(lambda: self.change_theme(Themes.DARK))
        theme_menu.addAction(dark_action)
        
        light_action = QAction("Light", self)
        light_action.triggered.connect(lambda: self.change_theme(Themes.LIGHT))
        theme_menu.addAction(light_action)

        # Help menu
        help_menu = menubar.addMenu("&Aiuto")
        
        # License management
        license_menu = help_menu.addMenu("&Licenza")
        
        # Activation status
        status_action = license_menu.addAction("Stato Attivazione")
        status_action.triggered.connect(self.show_license_status)
        
        # Deactivate license
        deactivate_action = license_menu.addAction("Disattiva Licenza")
        deactivate_action.triggered.connect(self.deactivate_license)

    def setup_statusbar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.pageChanged.connect(self.change_page)
        main_layout.addWidget(self.sidebar)
        
        # Page stack
        self.page_stack = QStackedWidget()
        
        # Add pages
        self.page_stack.addWidget(self._create_messages_page())
        self.page_stack.addWidget(self._create_stats_page())
        self.page_stack.addWidget(self._create_settings_page())
        self.page_stack.addWidget(self._create_help_page())
        
        main_layout.addWidget(self.page_stack)

    def _create_messages_page(self) -> QWidget:
        """Create the main messages page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Profile
        profile_group = QGroupBox("Profile")
        profile_layout = QVBoxLayout()
        
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://ngl.link/username")
        url_layout.addWidget(self.url_input)
        
        self.load_profile_button = QPushButton("Load")
        self.load_profile_button.clicked.connect(self.load_ngl_profile)
        url_layout.addWidget(self.load_profile_button)
        
        profile_layout.addLayout(url_layout)
        self.profile_info = QLabel("No profile loaded")
        profile_layout.addWidget(self.profile_info)
        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)        
        # Message configuration
        message_config = QHBoxLayout()
        
        # Left column: message input
        left_column = QVBoxLayout()
        
        message_group = QGroupBox("Message")
        message_layout = QVBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Enter the message...")
        self.message_input.setEnabled(False)
        message_layout.addWidget(self.message_input)
        
        self.use_random = QCheckBox("Generate random messages")
        self.use_random.setEnabled(False)
        self.use_random.stateChanged.connect(self._toggle_message_input)
        message_layout.addWidget(self.use_random)
        message_group.setLayout(message_layout)
        left_column.addWidget(message_group)
        
        # Preview
        self.preview_widget = EnhancedPreviewWidget(self.text_generator)
        self.preview_widget.messageAccepted.connect(self.use_preview_message)
        left_column.addWidget(self.preview_widget)
        
        message_config.addLayout(left_column)
        
        # Right column: configurations
        right_column = QVBoxLayout()
        
        # Language and style
        language_style_group = QGroupBox("Language and Style")
        language_layout = QVBoxLayout()
        
        # Language selection
        lang_label = QLabel("Available languages:")
        language_layout.addWidget(lang_label)
        
        self.language_checkboxes = {}
        for lang_code, lang_name in {
            'it': 'Italian 🇮🇹',
            'en': 'English 🇬🇧'
        }.items():
            checkbox = QCheckBox(lang_name)
            if lang_code == 'en':  # English as default
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_languages)
            self.language_checkboxes[lang_code] = checkbox
            language_layout.addWidget(checkbox)
        
        # Style selection
        style_label = QLabel("Message style:")
        language_layout.addWidget(style_label)
        
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "Standard",
            "Informal",
            "Internet/Gen-Z",
            "Regional"
        ])
        self.style_combo.currentTextChanged.connect(self._update_dialect_options)
        language_layout.addWidget(self.style_combo)
        
        self.dialect_combo = QComboBox()
        self.dialect_combo.addItems([
            "Roman",
            "Milanese",
            "Neapolitan"
        ])
        self.dialect_combo.hide()
        language_layout.addWidget(self.dialect_combo)
        
        language_style_group.setLayout(language_layout)
        right_column.addWidget(language_style_group)
        
        # Generation options
        generation_group = QGroupBox("Generation Options")
        generation_layout = QVBoxLayout()
        
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Number of messages:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 1000)
        self.count_spin.setValue(1)
        self.count_spin.setEnabled(False)
        count_layout.addWidget(self.count_spin)
        generation_layout.addLayout(count_layout)
        
        self.emoji_enabled = QCheckBox("Include emojis")
        self.emoji_enabled.setChecked(True)
        self.emoji_enabled.setEnabled(False)
        generation_layout.addWidget(self.emoji_enabled)
        
        generation_group.setLayout(generation_layout)
        right_column.addWidget(generation_group)
        
        message_config.addLayout(right_column)
        layout.addLayout(message_config)
        
        # Progress and Log
        bottom_layout = QVBoxLayout()
        
        # Progress
        progress_group = QGroupBox("Progresso")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m messages")
        progress_layout.addWidget(self.progress_bar)
        
        button_layout = QHBoxLayout()
        self.send_button = QPushButton("Send Messages")
        self.send_button.clicked.connect(self.send_messages)
        self.send_button.setEnabled(False)
        button_layout.addWidget(self.send_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_sending)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        progress_layout.addLayout(button_layout)
        progress_group.setLayout(progress_layout)
        bottom_layout.addWidget(progress_group)
        
        # Log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumHeight(150)
        log_layout.addWidget(self.status_log)
        
        log_group.setLayout(log_layout)
        bottom_layout.addWidget(log_group)
        
        layout.addLayout(bottom_layout)
        
        return page

    def _create_stats_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.stats_dashboard = StatsDashboardWidget(self.stats_manager)
        layout.addWidget(self.stats_dashboard)
        
        return page

    def _create_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Create tabs widget
        tabs = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # About section (moved to top)
        about_group = QGroupBox("Information")
        about_layout = QVBoxLayout()
        
        # Avatar and app info in horizontal layout
        header_layout = QHBoxLayout()
        
        # Avatar on the left
        avatar_label = QLabel()
        avatar_path = str(ICONS['avatar'])  # Use the path from ICONS
        avatar_pixmap = QPixmap(avatar_path)
        if not avatar_pixmap.isNull():  # Check if the image was loaded
            scaled_pixmap = avatar_pixmap.scaled(
                150, 150,  # Increased size
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            avatar_label.setPixmap(scaled_pixmap)
        else:
            print(f"Error loading avatar from: {avatar_path}")
            # Fallback text if the image cannot be loaded
            avatar_label.setText("KK")
            avatar_label.setStyleSheet("""
                QLabel {
                    background-color: #007acc;
                    color: white;
                    font-size: 40px;
                    font-weight: bold;
                    padding: 20px;
                    border-radius: 75px;
                    min-width: 150px;
                    min-height: 150px;
                    qproperty-alignment: AlignCenter;
                }
            """)
        
        header_layout.addWidget(avatar_label)
        
        # App info on the right
        info_layout = QVBoxLayout()
        app_name = QLabel("Phantom Messenger")
        app_name.setFont(QFont("", 20, QFont.Weight.Bold))  # Larger font
        info_layout.addWidget(app_name)
        
        version_label = QLabel("Version 1.0.0")
        version_label.setObjectName("versionLabel")
        version_label.mousePressEvent = self._handle_version_click
        version_label.setCursor(Qt.CursorShape.PointingHandCursor)
        info_layout.addWidget(version_label)
        
        # Credits below the version
        credits_text = QLabel(
            "Developed by Seregon\n"
            "With ❤️ and lots of ☕\n\n"
            "© 2024 Seregon. All rights reserved."
        )
        credits_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info_layout.addWidget(credits_text)
        
        header_layout.addLayout(info_layout)
        about_layout.addLayout(header_layout)
        
        # Social links in grid
        links_layout = QGridLayout()
        social_links = [
            ("Ko-fi", "https://ko-fi.com/seregon", "☕"),
            ("GitHub", "https://github.com/seregonwar", "💻"),
            ("Twitter/X", "https://x.com/SeregonWar", "🐦"),
            ("Reddit", "https://www.reddit.com/user/S3R3GON/", "🤖")
        ]
        
        for i, (name, url, icon) in enumerate(social_links):
            row = i // 2
            col = i % 2
            btn = QPushButton(f"{icon} {name}")
            btn.setObjectName("socialButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, u=url: QDesktopServices.openUrl(QUrl(u)))
            links_layout.addWidget(btn, row, col)
            
        about_layout.addLayout(links_layout)
        about_group.setLayout(about_layout)
        general_layout.addWidget(about_group)
        
        # Timing settings
        timing_group = QGroupBox("Timing Configuration")
        timing_layout = QVBoxLayout()
        
        # Profile selection
        timing_layout.addWidget(QLabel("Sending profile:"))
        self.timing_profile = QComboBox()
        self.timing_profile.addItems(["Normal", "Stealth", "Aggressive", "Custom"])
        self.timing_profile.currentTextChanged.connect(self._update_timing_settings)
        timing_layout.addWidget(self.timing_profile)
        
        # Delay settings
        delay_layout = QGridLayout()
        
        # Min delay
        delay_layout.addWidget(QLabel("Min delay (s):"), 0, 0)
        self.min_delay_spin = QSpinBox()
        self.min_delay_spin.setRange(1, 300)
        self.min_delay_spin.setValue(10)
        delay_layout.addWidget(self.min_delay_spin, 0, 1)
        
        # Max delay
        delay_layout.addWidget(QLabel("Max delay (s):"), 1, 0)
        self.max_delay_spin = QSpinBox()
        self.max_delay_spin.setRange(1, 600)
        self.max_delay_spin.setValue(30)
        delay_layout.addWidget(self.max_delay_spin, 1, 1)
        
        # Burst protection
        delay_layout.addWidget(QLabel("Burst protection (s):"), 2, 0)
        self.burst_protection_spin = QSpinBox()
        self.burst_protection_spin.setRange(0, 900)
        self.burst_protection_spin.setValue(120)
        delay_layout.addWidget(self.burst_protection_spin, 2, 1)
        
        timing_layout.addLayout(delay_layout)
        timing_group.setLayout(timing_layout)
        general_layout.addWidget(timing_group)
        
        # Interface settings
        interface_group = QGroupBox("Interface")
        interface_layout = QVBoxLayout()
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.currentTextChanged.connect(self._change_theme)
        theme_layout.addWidget(self.theme_combo)
        interface_layout.addLayout(theme_layout)
        
        # Notifications
        self.enable_notifications = QCheckBox("Enable desktop notifications")
        self.enable_notifications.setChecked(True)
        interface_layout.addWidget(self.enable_notifications)
        
        # Auto-save
        self.auto_save_stats = QCheckBox("Automatically save statistics")
        self.auto_save_stats.setChecked(True)
        interface_layout.addWidget(self.auto_save_stats)
        
        interface_group.setLayout(interface_layout)
        general_layout.addWidget(interface_group)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout()
        
        # Message generation
        self.advanced_generation = QCheckBox("Advanced message generation")
        self.advanced_generation.setToolTip("Use more sophisticated algorithms for message generation")
        advanced_layout.addWidget(self.advanced_generation)
        
        # Anti-detection
        self.anti_detection = QCheckBox("Anti-detection mode")
        self.anti_detection.setToolTip("Use techniques to avoid automation detection")
        advanced_layout.addWidget(self.anti_detection)
        
        advanced_group.setLayout(advanced_layout)
        general_layout.addWidget(advanced_group)
        
        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self._save_settings)
        general_layout.addWidget(save_button)
        
        # Add stretch to push everything up
        general_layout.addStretch()
        
        tabs.addTab(general_tab, "Generale")
        
        # License info tab
        license_tab = QWidget()
        license_layout = QVBoxLayout(license_tab)
        license_info = LicenseInfoWidget()
        license_layout.addWidget(license_info)
        tabs.addTab(license_tab, "Licenza")
        
        # Support tab
        support_tab = QWidget()
        support_layout = QVBoxLayout(support_tab)
        
        # Contact agent button
        contact_layout = QHBoxLayout()
        contact_layout.addWidget(QLabel("Hai bisogno di aiuto?"))
        
        contact_button = QPushButton("Contatta un Agente")
        contact_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        contact_button.clicked.connect(self._open_agent_chat)
        contact_layout.addWidget(contact_button)
        
        support_layout.addLayout(contact_layout)
        
        # Add support widget
        support_widget = SupportWidget(self.db_manager)
        support_layout.addWidget(support_widget)
        
        tabs.addTab(support_tab, "Supporto")
        
        # Add tabs to main layout
        layout.addWidget(tabs)
        
        return page

    def _create_help_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
            <h2>User Guide</h2>
            <p>Welcome to Message Sender! Here's how to use the application:</p>
            <ol>
                <li>Enter the profile URL to contact</li>
                <li>Select the languages and message style</li>
                <li>Configure the generation options</li>
                <li>Click "Send Messages" to start</li>
            </ol>
            <h3>Main Features</h3>
            <ul>
                <li>Multilingual support</li>
                <li>Intelligent message generation</li>
                <li>Real-time statistics</li>
                <li>Anti-detection protection</li>
            </ul>
        """)
        layout.addWidget(help_text)
        
        return page

    def change_page(self, page_id: str):
        """Change the displayed page"""
        page_index = {
            "messages": 0,
            "stats": 1,
            "settings": 2,
            "help": 3
        }.get(page_id, 0)
        
        self.page_stack.setCurrentIndex(page_index)

    def apply_theme(self):
        self.setStyleSheet(get_stylesheet(self.current_theme))

    def change_theme(self, theme):
        self.current_theme = theme
        is_dark = theme == Themes.DARK
        self.sidebar.update_theme(is_dark)
        self.apply_theme()

    def export_stats(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export statistics",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_name:
            # Implement export
            self.statusBar.showMessage(f"Statistics exported to {file_name}")

    def load_ngl_profile(self):
        """Load the NGL profile from the provided URL"""
        url = self.url_input.text().strip()
        if not url:
            self.show_error("Enter a valid URL")
            return
            
        try:
            self.statusBar.showMessage("Loading profile...")
            parser = NGLPageParser(url)
            
            if (parser.fetch_page() and parser.extract_data()):
                config = parser.get_config()
                self.current_config = config
                
                # Update the interface
                self.profile_info.setText(f"Profile loaded: @{config['USERNAME']}")
                self.enable_controls()
                self.statusBar.showMessage("Profile loaded successfully!", 3000)
            else:
                self.show_error("Unable to load profile. Check the URL.")
                
        except Exception as e:
            self.show_error(f"Error loading profile: {str(e)}")

    def enable_controls(self):
        """Enable controls after loading the profile"""
        self.message_input.setEnabled(True)
        self.use_random.setEnabled(True)
        self.emoji_enabled.setEnabled(True)
        self.count_spin.setEnabled(True)
        self.send_button.setEnabled(True)

    def show_error(self, message: str):
        """Show an error message"""
        self.statusBar.showMessage(f"Error: {message}", 5000)
        self.status_log.append(f"❌ {message}")

    def send_messages(self):
        """Send the messages"""
        if not hasattr(self, 'current_config'):
            self.show_error("Load an NGL profile first")
            return
            
        message = self.message_input.toPlainText()
        count = self.count_spin.value()
        use_random = self.use_random.isChecked()
        
        if not message and not use_random:
            self.show_error("Enter a message or select random text")
            return
        
        self.send_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Setup sender with current profile and config
        sender = MessageSender(self.current_config)
        
        # Get language and style settings
        selected_languages = [
            lang for lang, checkbox in self.language_checkboxes.items()
            if checkbox.isChecked()
        ]
        
        style = self.style_combo.currentText().lower()
        
        # Set dialect if style is regional
        if style == "regional":
            sender.text_generator.regional_dialect = self.dialect_combo.currentText()
        else:
            sender.text_generator.regional_dialect = None
            
        # Configure text generator
        sender.text_generator.set_languages(selected_languages)
        
        # Create and start worker thread
        self.worker = SendMessageWorker(sender, message, count, use_random)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.message_sent.connect(self.log_message)
        self.worker.finished.connect(self.on_sending_finished)
        self.worker.start()

    def log_message(self, message, success):
        status = "✓" if success else "✗"
        self.status_log.append(f"{status} {message}")

    def on_sending_finished(self, results):
        successful, failed = results
        self.status_log.append(f"\nCompleted! Successful: {successful}, Failed: {failed}")
        self.send_button.setEnabled(True)
        # Update statistics
        self.stats_dashboard.update_stats()

    def update_stats(self):
        """Update the statistics charts"""
        if not hasattr(self, 'figure'):
            return
            
        self.figure.clear()
        
        # Create subplots
        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)
        
        # Plot hourly stats
        if hasattr(self, 'logger'):
            hours = range(24)
            values = [self.logger.all_time_stats['hourly_stats'].get(str(h), 0) for h in hours]
            ax1.bar(hours, values)
            ax1.set_title('Hourly distribution')
            ax1.set_xlabel('Hour of the day')
            ax1.set_ylabel('Number of messages')
            
            # Plot profile usage
            if self.logger.all_time_stats['profile_usage']:
                profiles = list(self.logger.all_time_stats['profile_usage'].keys())
                usage = list(self.logger.all_time_stats['profile_usage'].values())
                ax2.pie(usage, labels=profiles, autopct='%1.1f%%')
                ax2.set_title('Profile usage')
        
        self.canvas.draw()

    def update_languages(self):
        """Update the selected languages for message generation"""
        selected_languages = [
            lang for lang, checkbox in self.language_checkboxes.items()
            if checkbox.isChecked()
        ]
        
        if not selected_languages:  # Ensure at least one language is selected
            self.language_checkboxes['en'].setChecked(True)
            selected_languages = ['en']
        
        if hasattr(self, 'text_generator'):
            self.text_generator.set_languages(selected_languages)

    def _create_progress_group(self):
        """Create the group for the progress bar and send controls"""
        group = QGroupBox("Progress")
        layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m messages")
        layout.addWidget(self.progress_bar)
        
        # Send button
        button_layout = QHBoxLayout()
        self.send_button = QPushButton("Send Messages")
        self.send_button.clicked.connect(self.send_messages)
        self.send_button.setEnabled(False)  # Disabled until a profile is loaded
        button_layout.addWidget(self.send_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_sending)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group

    def _create_log_group(self):
        """Create the group for the message log"""
        group = QGroupBox("Log")
        layout = QVBoxLayout()
        
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumHeight(150)
        layout.addWidget(self.status_log)
        
        # Clear log button
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.status_log.clear)
        layout.addWidget(clear_button)
        
        group.setLayout(layout)
        return group

    def _create_settings_tab(self):
        """Create the settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Timing settings
        timing_group = QGroupBox("Timing Configuration")
        timing_layout = QVBoxLayout()
        
        # Profile selection
        timing_layout.addWidget(QLabel("Sending profile:"))
        self.timing_profile = QComboBox()
        self.timing_profile.addItems(["Normal", "Stealth", "Aggressive", "Custom"])
        timing_layout.addWidget(self.timing_profile)
        
        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)
        
        # Add other settings as needed
        layout.addStretch()
        return tab

    def stop_sending(self):
        """Stop sending messages"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.send_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_log.append("Sending stopped by user")

    def use_preview_message(self, message: str):
        """Use the message from the preview"""
        self.message_input.setText(message)
        self.use_random.setChecked(False)
        self.statusBar.showMessage("Message from preview set", 3000)

    def _toggle_message_input(self, state):
        """Enable/disable message input based on checkbox state"""
        self.message_input.setEnabled(not state)
        if state:
            self.message_input.setPlaceholderText("Automatic generation active...")
        else:
            self.message_input.setPlaceholderText("Enter the message...")
            
    def _update_dialect_options(self, style: str):
        """Show/hide dialect options based on selected style"""
        self.dialect_combo.setVisible(style.lower() == "regional")

    def _update_timing_settings(self, profile: str):
        """Update timing settings based on selected profile"""
        profiles = {
            "Normal": (10, 30, 120),
            "Stealth": (30, 180, 300),
            "Aggressive": (5, 15, 60),
            "Custom": (self.min_delay_spin.value(), 
                      self.max_delay_spin.value(),
                      self.burst_protection_spin.value())
        }
        
        if profile != "Custom":
            min_delay, max_delay, burst = profiles[profile]
            self.min_delay_spin.setValue(min_delay)
            self.max_delay_spin.setValue(max_delay)
            self.burst_protection_spin.setValue(burst)

    def _change_theme(self, theme: str):
        """Change the interface theme"""
        self.current_theme = getattr(Themes, theme.upper())
        self.apply_theme()

    def _save_settings(self):
        """Save all settings"""
        # Save timing settings
        timing_config = {
            'min_delay': self.min_delay_spin.value(),
            'max_delay': self.max_delay_spin.value(),
            'burst_protection': self.burst_protection_spin.value()
        }
        
        # Save interface settings
        interface_config = {
            'theme': self.theme_combo.currentText(),
            'notifications': self.enable_notifications.isChecked(),
            'auto_save': self.auto_save_stats.isChecked()
        }
        
        # Save advanced settings
        advanced_config = {
            'advanced_generation': self.advanced_generation.isChecked(),
            'anti_detection': self.anti_detection.isChecked()
        }
        
        # TODO: Implementa il salvataggio effettivo delle configurazioni
        self.statusBar.showMessage("Impostazioni salvate con successo", 3000)

    def _handle_version_click(self, event):
        """Gestisce i click sulla versione per l'easter egg"""
        if not hasattr(self, 'click_count'):
            self.click_count = 0
        self.click_count += 1
        if self.click_count >= 5:
            self.click_count = 0
            self._show_easter_egg()

    def _show_easter_egg(self):
        """Display the easter egg"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt6.QtCore import Qt
        
        # Create a dialog for the easter egg
        dialog = QDialog(self)
        dialog.setWindowTitle("Terminal")
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # Remove the title bar
        layout = QVBoxLayout()
        
        # ASCII art for the terminal display
        ascii_art = """
    _________________________________________________
   /                                                 \\
  |    _________________________________________     |
  |   |                                         |    |
  |   |  C:\\> HACK THE PLANET                   |    |
  |   |                                         |    |
  |   |  SYSTEM COMPROMISED                     |    |
  |   |  ACCESSING MAINFRAME...                 |    |
  |   |  DOWNLOADING SECRET FILES...            |    |
  |   |                                         |    |
  |   |  CONGRATULATIONS! YOU FOUND THE         |    |
  |   |  SUPER SECRET EASTER EGG!               |    |
  |   |                                         |    |
  |   |  NOW GO FORTH AND CODE, YOUNG PADAWAN   |    |
  |   |_________________________________________|    |
  |                                                  |
   \\_________________________________________________/
          \\___________________________________/
       ___________________________________________
    _-'    .-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  --- `-_
 _-'.-.-. .---.-.-.-.-.-.-.-.-.-.-.-.-.-.-.--.  .-.-.`-_
:-------------------------------------------------------------------------:
`---._.-------------------------------------------------------------._.---'
        """
        
        # Create a label to display the ASCII art
        terminal = QLabel(ascii_art)
        terminal.setStyleSheet("""
            QLabel {
                font-family: monospace;
                color: #00ff00;
                background-color: #000000;
                padding: 20px;
                border: 2px solid #00ff00;
                border-radius: 10px;
            }
        """)
        layout.addWidget(terminal)
        
        # Add a button to close the dialog
        close_button = QPushButton("CLOSE TERMINAL")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: #00ff00;
                border: 2px solid #00ff00;
                padding: 10px;
                font-family: monospace;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #003300;
            }
        """)
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Set the layout and style for the dialog
        dialog.setLayout(layout)
        dialog.setStyleSheet("background-color: #000000;")
        dialog.exec()

    def show_license_status(self):
        """Show current license status"""
        try:
            if self.license_manager.verify_license():
                QMessageBox.information(
                    self,
                    "Stato Licenza",
                    "La licenza è attiva e valida."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Stato Licenza",
                    "La licenza non è valida o è scaduta."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante la verifica della licenza: {str(e)}"
            )
    
    def deactivate_license(self):
        """Deactivate current license"""
        reply = QMessageBox.question(
            self,
            "Disattiva Licenza",
            "Sei sicuro di voler disattivare la licenza su questo dispositivo?\n"
            "Dovrai riattivare il software per utilizzarlo nuovamente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.license_manager.deactivate_current_license():
                    QMessageBox.information(
                        self,
                        "Successo",
                        "Licenza disattivata con successo.\n"
                        "L'applicazione verrà chiusa."
                    )
                    self.close()
                else:
                    QMessageBox.warning(
                        self,
                        "Errore",
                        "Impossibile disattivare la licenza."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Errore",
                    f"Errore durante la disattivazione: {str(e)}"
                )

    def on_background_init_complete(self):
        """Chiamato quando l'inizializzazione in background è completata"""
        try:
            # Aggiorna le informazioni della licenza
            if hasattr(self, 'license_info'):
                self.license_info.update_info()
            
            # Aggiorna le statistiche
            if hasattr(self, 'stats_dashboard'):
                self.stats_dashboard.update_stats()
            
            # Abilita le funzionalità che richiedono l'inizializzazione
            self.setEnabled(True)
            
            # Nascondi eventuali dialoghi di caricamento
            if hasattr(self, 'loading_dialog'):
                self.loading_dialog.close()
                
            # Mostra la finestra principale
            self.show()
            self.raise_()
            self.activateWindow()
            
        except Exception as e:
            logging.error(f"Error in background init completion: {e}")
            QMessageBox.critical(
                self,
                "Errore",
                "Si è verificato un errore durante l'inizializzazione.\n"
                "Alcune funzionalità potrebbero non essere disponibili."
            )

    def _open_agent_chat(self):
        """Apre la chat con un agente di supporto"""
        dialog = AgentChatDialog(self)
        dialog.exec()
