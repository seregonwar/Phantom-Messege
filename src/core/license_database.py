import sqlite3
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict

class LicenseDatabase:
    def __init__(self):
        self.db_path = os.path.join("config", "licenses.db")
        self._init_database()
    
    def _init_database(self):
        """Initialize the database and create tables if they don't exist"""
        os.makedirs("config", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_licenses (
                    license_key TEXT PRIMARY KEY,
                    hardware_id TEXT NOT NULL,
                    activation_date TEXT NOT NULL,
                    last_check TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            conn.commit()
    
    def is_license_active(self, license_key: str) -> bool:
        """Check if a license is already activated on another device"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT hardware_id FROM active_licenses WHERE license_key = ?",
                (license_key,)
            )
            result = cursor.fetchone()
            return bool(result)
    
    def get_active_hardware_id(self, license_key: str) -> Optional[str]:
        """Get the hardware ID where this license is currently active"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT hardware_id FROM active_licenses WHERE license_key = ?",
                (license_key,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    def activate_license(self, license_key: str, hardware_id: str, metadata: Dict) -> bool:
        """Activate a license for a specific hardware ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if license is already activated
                cursor.execute(
                    "SELECT hardware_id FROM active_licenses WHERE license_key = ?",
                    (license_key,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    if existing[0] != hardware_id:
                        logging.error(f"License already active on different hardware: {existing[0]}")
                        return False
                    
                    # Update last check time for existing activation
                    cursor.execute("""
                        UPDATE active_licenses 
                        SET last_check = ? 
                        WHERE license_key = ?
                    """, (datetime.now().isoformat(), license_key))
                else:
                    # New activation
                    cursor.execute("""
                        INSERT INTO active_licenses 
                        (license_key, hardware_id, activation_date, last_check, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        license_key,
                        hardware_id,
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        json.dumps(metadata)
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logging.error(f"Error activating license: {e}")
            return False
    
    def deactivate_license(self, license_key: str, hardware_id: str) -> bool:
        """Deactivate a license for a specific hardware ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM active_licenses 
                    WHERE license_key = ? AND hardware_id = ?
                """, (license_key, hardware_id))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logging.error(f"Error deactivating license: {e}")
            return False 