from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QGroupBox, QScrollArea, QPushButton, QProgressBar)
from PyQt6.QtCore import Qt
import json
from datetime import datetime
import psutil
import logging

class DeviceDetailsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Scroll area for all content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        
        # System Info
        self.system_group = QGroupBox("System Information")
        self.system_layout = QVBoxLayout()
        self.system_group.setLayout(self.system_layout)
        self.content_layout.addWidget(self.system_group)
        
        # Hardware Info
        self.hardware_group = QGroupBox("Hardware Details")
        self.hardware_layout = QVBoxLayout()
        self.hardware_group.setLayout(self.hardware_layout)
        self.content_layout.addWidget(self.hardware_group)
        
        # Location Info
        self.location_group = QGroupBox("Location Information")
        self.location_layout = QVBoxLayout()
        self.location_group.setLayout(self.location_layout)
        self.content_layout.addWidget(self.location_group)
        
        # Usage Statistics
        self.usage_group = QGroupBox("Usage Statistics")
        self.usage_layout = QVBoxLayout()
        self.usage_group.setLayout(self.usage_layout)
        self.content_layout.addWidget(self.usage_group)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
    def update_device_info(self, device: dict):
        """Update all device information"""
        # Clear existing content
        self._clear_layouts()
        
        # System Info
        system_info = json.loads(device['system_info'])
        self._add_system_info(system_info)
        
        # Hardware Info
        self._add_hardware_info(system_info)
        
        # Location Info
        location = json.loads(device['location']) if device['location'] else {}
        self._add_location_info(location, device['ip_address'])
        
        # Usage Stats
        self._add_usage_stats(device)
        
    def _clear_layouts(self):
        """Clear all layout contents"""
        for layout in [self.system_layout, self.hardware_layout, 
                      self.location_layout, self.usage_layout]:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                    
    def _add_system_info(self, system_info: dict):
        """Add system information section"""
        try:
            # Gestisci il caso in cui system_info è None o non ha la chiave 'system'
            if not system_info or not isinstance(system_info, dict):
                system_info = {}
            
            system = system_info.get('system', {})
            if not isinstance(system, dict):
                system = {}
            
            info_items = [
                ("Operating System", system.get('os', 'Unknown')),
                ("Version", system.get('version', 'Unknown')),
                ("Python Version", system.get('python_version', 'Unknown')),
                ("Hostname", system_info.get('hostname', 'Unknown')),
                ("Username", system_info.get('username', 'Unknown')),
                ("Boot Time", self._format_datetime(system_info.get('boot_time', '')))
            ]
            
            for label, value in info_items:
                self.system_layout.addWidget(QLabel(f"<b>{label}:</b> {value}"))
                
        except Exception as e:
            logging.error(f"Error adding system info: {e}")
            self.system_layout.addWidget(QLabel("Error loading system information"))
            
    def _add_hardware_info(self, system_info: dict):
        """Add hardware information section"""
        try:
            if not system_info or not isinstance(system_info, dict):
                system_info = {}
            
            system = system_info.get('system', {})
            if not isinstance(system, dict):
                system = {}
            
            info_items = [
                ("Processor", system.get('processor', 'Unknown')),
                ("CPU Cores", str(system.get('cpu_count', 'Unknown'))),
                ("RAM", system.get('ram', 'Unknown')),
                ("Machine Type", system.get('machine', 'Unknown'))
            ]
            
            for label, value in info_items:
                self.hardware_layout.addWidget(QLabel(f"<b>{label}:</b> {value}"))
                
        except Exception as e:
            logging.error(f"Error adding hardware info: {e}")
            self.hardware_layout.addWidget(QLabel("Error loading hardware information"))
            
    def _add_location_info(self, location: dict, ip_address: str):
        """Add location information section"""
        info_items = [
            ("IP Address", ip_address),
            ("City", location.get('city', 'Unknown')),
            ("Region", location.get('region', 'Unknown')),
            ("Country", location.get('country', 'Unknown'))
        ]
        
        for label, value in info_items:
            self.location_layout.addWidget(QLabel(f"<b>{label}:</b> {value}"))
            
    def _add_usage_stats(self, device: dict):
        """Add usage statistics section"""
        # Session Info
        self.usage_layout.addWidget(QLabel("<b>Current Session</b>"))
        
        # Active Time
        active_time = self._calculate_active_time(device)
        self.usage_layout.addWidget(QLabel(f"Active Time: {active_time}"))
        
        # Activity Level
        activity_level = self._calculate_activity_level(device)
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(activity_level)
        progress.setFormat(f"Activity Level: {activity_level}%")
        self.usage_layout.addWidget(progress)
        
        # Historical Stats
        self.usage_layout.addWidget(QLabel("<b>Historical Statistics</b>"))
        stats = [
            f"Total Sessions: {device.get('activation_count', 0)}",
            f"First Seen: {self._format_datetime(device['activation_date'])}",
            f"Last Active: {self._format_datetime(device['last_check'])}",
            f"Status: {device['status']}"
        ]
        
        for stat in stats:
            self.usage_layout.addWidget(QLabel(stat))
            
    def _format_datetime(self, dt_str: str) -> str:
        """Format datetime string for display"""
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "Unknown"
            
    def _calculate_active_time(self, device: dict) -> str:
        """Calculate active time for current session"""
        try:
            start = datetime.fromisoformat(device['activation_date'])
            end = datetime.fromisoformat(device['last_check'])
            delta = end - start
            hours = delta.total_seconds() / 3600
            return f"{hours:.1f} hours"
        except:
            return "Unknown"
            
    def _calculate_activity_level(self, device: dict) -> int:
        """Calculate activity level as percentage"""
        try:
            # Base calculation on frequency of updates and total time
            updates = device.get('activation_count', 0)
            if updates < 10:
                return 25
            elif updates < 50:
                return 50
            elif updates < 100:
                return 75
            return 100
        except:
            return 0 