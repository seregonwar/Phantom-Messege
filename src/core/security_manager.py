import hashlib
import json
import os
import platform
import subprocess
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import sqlite3
from .crypto_utils import CryptoManager

class SecurityManager:
    def __init__(self):
        self.db_path = os.path.join("config", "security.db")
        self.crypto = CryptoManager()
        self._initialize_database()
        self._load_security_rules()
        
    def _initialize_database(self):
        """Initialize security database"""
        os.makedirs("config", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Blacklist tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blacklisted_devices (
                    hardware_id TEXT PRIMARY KEY,
                    reason TEXT,
                    added_at TEXT,
                    expires_at TEXT,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blacklisted_ips (
                    ip_address TEXT PRIMARY KEY,
                    reason TEXT,
                    added_at TEXT,
                    expires_at TEXT,
                    metadata TEXT
                )
            ''')
            
            # Suspicious activity tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suspicious_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hardware_id TEXT,
                    ip_address TEXT,
                    activity_type TEXT,
                    severity TEXT,
                    details TEXT,
                    timestamp TEXT
                )
            ''')
            
            # System integrity checks
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_checksums (
                    file_path TEXT PRIMARY KEY,
                    checksum TEXT,
                    last_verified TEXT
                )
            ''')
            
            # Offline validation tokens
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS offline_tokens (
                    hardware_id TEXT,
                    token TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    used_count INTEGER DEFAULT 0,
                    max_uses INTEGER,
                    PRIMARY KEY (hardware_id, token)
                )
            ''')
            
            conn.commit()
            
    def _load_security_rules(self):
        """Load security rules from configuration"""
        self.rules = {
            'max_failed_attempts': 5,
            'blacklist_duration': 24,  # hours
            'offline_max_days': 7,
            'suspicious_patterns': [
                {'pattern': 'multiple_ips', 'threshold': 3, 'timeframe': 1},  # hours
                {'pattern': 'rapid_activations', 'threshold': 5, 'timeframe': 1},
                {'pattern': 'geographic_jump', 'distance': 1000}  # km
            ],
            'required_files': [
                'main.exe',
                'license.bin',
                'config/settings.json'
            ]
        }
        
    def is_blacklisted(self, hardware_id: str, ip_address: str) -> tuple[bool, str]:
        """Check if device or IP is blacklisted"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check device blacklist
                cursor.execute('''
                    SELECT reason FROM blacklisted_devices
                    WHERE hardware_id = ? AND (expires_at IS NULL OR expires_at > ?)
                ''', (hardware_id, datetime.now().isoformat()))
                
                device_result = cursor.fetchone()
                if device_result:
                    return True, f"Device blacklisted: {device_result[0]}"
                
                # Check IP blacklist
                cursor.execute('''
                    SELECT reason FROM blacklisted_ips
                    WHERE ip_address = ? AND (expires_at IS NULL OR expires_at > ?)
                ''', (ip_address, datetime.now().isoformat()))
                
                ip_result = cursor.fetchone()
                if ip_result:
                    return True, f"IP blacklisted: {ip_result[0]}"
                    
                return False, ""
                
        except Exception as e:
            logging.error(f"Error checking blacklist: {e}")
            return False, ""
            
    def add_to_blacklist(self, hardware_id: str = None, ip_address: str = None, 
                        reason: str = None, duration_hours: int = None):
        """Add device or IP to blacklist"""
        try:
            expires_at = None
            if duration_hours:
                expires_at = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if hardware_id:
                    cursor.execute('''
                        INSERT OR REPLACE INTO blacklisted_devices
                        (hardware_id, reason, added_at, expires_at)
                        VALUES (?, ?, ?, ?)
                    ''', (hardware_id, reason, datetime.now().isoformat(), expires_at))
                    
                if ip_address:
                    cursor.execute('''
                        INSERT OR REPLACE INTO blacklisted_ips
                        (ip_address, reason, added_at, expires_at)
                        VALUES (?, ?, ?, ?)
                    ''', (ip_address, reason, datetime.now().isoformat(), expires_at))
                    
                conn.commit()
                
        except Exception as e:
            logging.error(f"Error adding to blacklist: {e}")
            
    def verify_system_integrity(self) -> tuple[bool, list]:
        """Verify system files haven't been tampered with"""
        violations = []
        
        try:
            for file_path in self.rules['required_files']:
                if not os.path.exists(file_path):
                    violations.append(f"Missing required file: {file_path}")
                    continue
                    
                current_hash = self._calculate_file_hash(file_path)
                stored_hash = self._get_stored_hash(file_path)
                
                if stored_hash and current_hash != stored_hash:
                    violations.append(f"File modified: {file_path}")
                    
            # Check for debugging tools
            if self._detect_debugger():
                violations.append("Debugger detected")
                
            # Check for virtualization
            if self._detect_virtualization():
                violations.append("Virtualization detected")
                
            return len(violations) == 0, violations
            
        except Exception as e:
            logging.error(f"Error verifying system integrity: {e}")
            return False, ["Error during verification"]
            
    def generate_offline_token(self, hardware_id: str, days: int = 7) -> Optional[str]:
        """Generate offline validation token"""
        try:
            token = self.crypto.generate_token()
            expires_at = datetime.now() + timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO offline_tokens
                    (hardware_id, token, created_at, expires_at, max_uses)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    hardware_id,
                    token,
                    datetime.now().isoformat(),
                    expires_at.isoformat(),
                    days * 2  # Allow 2 validations per day
                ))
                conn.commit()
                
            return token
            
        except Exception as e:
            logging.error(f"Error generating offline token: {e}")
            return None
            
    def validate_offline_token(self, hardware_id: str, token: str) -> bool:
        """Validate an offline token"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT expires_at, used_count, max_uses 
                    FROM offline_tokens
                    WHERE hardware_id = ? AND token = ?
                ''', (hardware_id, token))
                
                result = cursor.fetchone()
                if not result:
                    return False
                    
                expires_at, used_count, max_uses = result
                
                # Check expiration
                if datetime.now() > datetime.fromisoformat(expires_at):
                    return False
                    
                # Check usage limit
                if used_count >= max_uses:
                    return False
                    
                # Update usage count
                cursor.execute('''
                    UPDATE offline_tokens
                    SET used_count = used_count + 1
                    WHERE hardware_id = ? AND token = ?
                ''', (hardware_id, token))
                
                conn.commit()
                return True
                
        except Exception as e:
            logging.error(f"Error validating offline token: {e}")
            return False
            
    def detect_suspicious_activity(self, hardware_id: str, ip_address: str, 
                                 activity_data: Dict) -> List[str]:
        """Detect suspicious activities"""
        suspicious_activities = []
        
        try:
            # Check for multiple IPs
            if self._check_multiple_ips(hardware_id):
                suspicious_activities.append("Multiple IPs detected")
                
            # Check for rapid activations
            if self._check_rapid_activations(hardware_id):
                suspicious_activities.append("Rapid activation attempts")
                
            # Check for geographic jumps
            if self._check_geographic_jump(hardware_id, ip_address):
                suspicious_activities.append("Suspicious location change")
                
            # Record suspicious activities
            if suspicious_activities:
                self._record_suspicious_activity(
                    hardware_id, 
                    ip_address,
                    suspicious_activities,
                    activity_data
                )
                
            return suspicious_activities
            
        except Exception as e:
            logging.error(f"Error detecting suspicious activity: {e}")
            return []
            
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def _get_stored_hash(self, file_path: str) -> Optional[str]:
        """Get stored hash for a file"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT checksum FROM system_checksums WHERE file_path = ?",
                (file_path,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
            
    def _detect_debugger(self) -> bool:
        """Detect if a debugger is attached"""
        try:
            return psutil.Process().is_running_under_debugger()
        except:
            return False
            
    def _detect_virtualization(self) -> bool:
        """Detect if running in a virtual machine"""
        try:
            # Check common VM identifiers
            with open("/sys/class/dmi/id/product_name", "r") as f:
                product_name = f.read().lower()
                return any(x in product_name for x in ["vmware", "virtualbox", "qemu"])
        except:
            return False
            
    def _check_multiple_ips(self, hardware_id: str) -> bool:
        """Check for multiple IPs in timeframe"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            timeframe = datetime.now() - timedelta(
                hours=self.rules['suspicious_patterns'][0]['timeframe']
            )
            
            cursor.execute('''
                SELECT COUNT(DISTINCT ip_address) 
                FROM suspicious_activities
                WHERE hardware_id = ? AND timestamp > ?
            ''', (hardware_id, timeframe.isoformat()))
            
            count = cursor.fetchone()[0]
            return count >= self.rules['suspicious_patterns'][0]['threshold']
            
    def _check_rapid_activations(self, hardware_id: str) -> bool:
        """Check for rapid activation attempts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            timeframe = datetime.now() - timedelta(
                hours=self.rules['suspicious_patterns'][1]['timeframe']
            )
            
            cursor.execute('''
                SELECT COUNT(*) 
                FROM suspicious_activities
                WHERE hardware_id = ? AND timestamp > ?
                AND activity_type = 'activation_attempt'
            ''', (hardware_id, timeframe.isoformat()))
            
            count = cursor.fetchone()[0]
            return count >= self.rules['suspicious_patterns'][1]['threshold']
            
    def _check_geographic_jump(self, hardware_id: str, ip_address: str) -> bool:
        """Check for suspicious geographic location changes"""
        try:
            # Get current location
            response = requests.get(f'https://ipapi.co/{ip_address}/json/')
            if response.status_code != 200:
                return False
                
            current_location = response.json()
            
            # Get last known location
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT details FROM suspicious_activities
                    WHERE hardware_id = ? AND activity_type = 'location'
                    ORDER BY timestamp DESC LIMIT 1
                ''', (hardware_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                    
                last_location = json.loads(result[0])
                
                # Calculate distance between locations
                from geopy.distance import geodesic
                distance = geodesic(
                    (last_location['latitude'], last_location['longitude']),
                    (current_location['latitude'], current_location['longitude'])
                ).kilometers
                
                return distance > self.rules['suspicious_patterns'][2]['distance']
                
        except Exception as e:
            logging.error(f"Error checking geographic jump: {e}")
            return False
            
    def _record_suspicious_activity(self, hardware_id: str, ip_address: str,
                                  activities: List[str], details: Dict):
        """Record suspicious activity in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for activity in activities:
                    cursor.execute('''
                        INSERT INTO suspicious_activities
                        (hardware_id, ip_address, activity_type, severity, details, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        hardware_id,
                        ip_address,
                        activity,
                        'high' if len(activities) > 1 else 'medium',
                        json.dumps(details),
                        datetime.now().isoformat()
                    ))
                conn.commit()
                
        except Exception as e:
            logging.error(f"Error recording suspicious activity: {e}") 