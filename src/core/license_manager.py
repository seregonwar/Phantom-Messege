import hashlib
import json
import os
import uuid
import platform
import subprocess
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict
import base64
from .crypto_utils import CryptoManager
from tools.db_manager import LicenseDBManager
import requests
import jwt
import socket
import psutil
import threading
import time
from .dropbox_sync import DropboxSync
from PyQt6.QtWidgets import QProgressDialog
from PyQt6.QtCore import Qt

class LicenseManager:
    def __init__(self):
        self.config_dir = "config"
        self.license_file = os.path.join(self.config_dir, "license.bin")
        self.crypto = CryptoManager()
        self.db = LicenseDBManager()
        self.dropbox = DropboxSync()
        self.heartbeat_interval = 300  # 5 minuti
        self.heartbeat_thread = None
        self._stop_heartbeat = False

    def _get_hardware_id(self) -> str:
        """Generate a unique hardware ID"""
        system = platform.system()
        
        if system == "Windows":
            # Get Windows UUID
            command = "wmic csproduct get UUID"
            uuid = subprocess.check_output(command).decode().split("\n")[1].strip()
            
            # Get CPU ID
            command = "wmic cpu get processorid"
            cpu_id = subprocess.check_output(command).decode().split("\n")[1].strip()
            
            # Get motherboard serial
            command = "wmic baseboard get serialnumber"
            mb_serial = subprocess.check_output(command).decode().split("\n")[1].strip()
            
        elif system == "Linux":
            # Get machine-id
            with open("/etc/machine-id", "r") as f:
                uuid = f.read().strip()
            
            # Get CPU info
            with open("/proc/cpuinfo", "r") as f:
                cpu_id = [l for l in f if "serial" in l][0].split(":")[1].strip()
                
            mb_serial = subprocess.check_output(["dmidecode", "-s", "system-uuid"]).decode().strip()
            
        else:  # macOS
            uuid = subprocess.check_output(["system_profiler", "SPHardwareDataType"]).decode()
            cpu_id = uuid
            mb_serial = uuid
            
        combined = f"{uuid}:{cpu_id}:{mb_serial}"
        return hashlib.sha256(combined.encode()).hexdigest()
        
    def _verify_signature(self, key: str, metadata: dict, signature: str) -> bool:
        """Verify the cryptographic signature of the license"""
        data = f"{key}:{json.dumps(metadata, sort_keys=True)}"
        computed_signature = hashlib.sha512(data.encode()).hexdigest()
        return signature == computed_signature
        
    def _get_system_info(self) -> dict:
        """Get detailed system information"""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            
            system_info = {
                'system': {
                    'os': platform.system(),
                    'version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor(),
                    'ram': f"{psutil.virtual_memory().total / (1024**3):.1f}GB",
                    'cpu_count': psutil.cpu_count(),
                    'python_version': platform.python_version()
                },
                'hostname': hostname,
                'ip_address': ip_address,
                'username': os.getenv('USERNAME') or os.getenv('USER'),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
            
            # Prova a ottenere la posizione dall'IP
            try:
                response = requests.get(f'https://ipapi.co/{ip_address}/json/')
                if response.status_code == 200:
                    location_data = response.json()
                    system_info['location'] = {
                        'city': location_data.get('city'),
                        'region': location_data.get('region'),
                        'country': location_data.get('country_name')
                    }
            except:
                pass
                
            return system_info
            
        except Exception as e:
            logging.error(f"Error getting system info: {e}")
            return {}
            
    def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while not self._stop_heartbeat:
            try:
                if os.path.exists(self.license_file):
                    with open(self.license_file, 'rb') as f:
                        license_data = json.loads(self.crypto.decrypt(f.read()))
                    
                    # Aggiorna le informazioni del dispositivo
                    system_info = self._get_system_info()
                    self.db.add_device(
                        self._get_hardware_id(),
                        license_data['key'],
                        system_info
                    )
                    
                    # Verifica lo stato su Dropbox
                    dropbox_status = self.dropbox.check_license_status(license_data['key'])
                    if dropbox_status['status'] != 'active':
                        logging.warning("License is no longer active")
                        self._stop_heartbeat = True
                        break
                        
            except Exception as e:
                logging.error(f"Heartbeat error: {e}")
                
            time.sleep(self.heartbeat_interval)
            
    def verify_license(self, parent=None) -> bool:
        """Verify if the license is valid"""
        # Crea il dialogo di progresso
        progress = QProgressDialog("Verifica della licenza in corso...", None, 0, 100, parent)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowTitle("Verifica Licenza")
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)  # Mostra immediatamente
        
        try:
            progress.setValue(10)
            if not os.path.exists(self.license_file):
                logging.error("License file not found")
                return False
                
            progress.setValue(20)
            # Read and decrypt the license file
            with open(self.license_file, 'rb') as f:
                encrypted_data = f.read()
                
            progress.setValue(30)
            # Decrypt the license data
            license_data = json.loads(self.crypto.decrypt(encrypted_data))
            
            key = license_data['key']
            metadata = license_data['metadata']
            signature = license_data['signature']
            
            progress.setValue(40)
            # Verify signature
            if not self._verify_signature(key, metadata, signature):
                logging.error("Invalid license signature")
                return False
            
            progress.setValue(50)
            current_hardware_id = self._get_hardware_id()
            
            progress.setValue(60)
            # Verifica su Dropbox
            dropbox_status = self.dropbox.check_license_status(key)
            if dropbox_status['status'] == 'revoked':
                logging.error("License has been revoked")
                return False
            elif dropbox_status['status'] == 'not_found':
                logging.error("License not found in central database")
                return False
            
            progress.setValue(70)
            # Verifica scadenza dalla licenza Dropbox
            license_data = dropbox_status['data']
            expiration_date = datetime.fromisoformat(license_data['data']['created_at']) + \
                            timedelta(days=license_data['data']['valid_days'])
            
            if datetime.now() > expiration_date:
                logging.error("License has expired")
                return False
            
            progress.setValue(80)
            # Ottieni informazioni di sistema
            system_info = self._get_system_info()
            
            progress.setValue(90)
            # Registra il dispositivo nel database locale
            if not self.db.add_device(current_hardware_id, key, system_info):
                logging.error("Failed to register device")
                return False
            
            progress.setValue(95)
            # Start heartbeat thread if license is valid
            if not self.heartbeat_thread or not self.heartbeat_thread.is_alive():
                self._stop_heartbeat = False
                self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
                self.heartbeat_thread.daemon = True
                self.heartbeat_thread.start()
            
            progress.setValue(100)
            return True
            
        except Exception as e:
            logging.error(f"Error verifying license: {e}")
            return False
        finally:
            progress.close()
            
    def deactivate_current_license(self) -> bool:
        """Deactivate the license on this machine"""
        try:
            self._stop_heartbeat = True
            if self.heartbeat_thread:
                self.heartbeat_thread.join()
                
            with open(self.license_file, 'rb') as f:
                license_data = json.loads(self.crypto.decrypt(f.read()))
            
            key = license_data['key']
            current_hardware_id = self._get_hardware_id()
            
            # Revoca su Dropbox
            if not self.dropbox.revoke_license(
                key, 
                reason=f"Deactivated by user {current_hardware_id} on {datetime.now().isoformat()}"
            ):
                logging.error("Failed to revoke license on Dropbox")
                return False
            
            # Revoca nel database locale
            if not self.db.revoke_device(current_hardware_id, key):
                logging.error("Failed to revoke license in local database")
                return False
            
            # Rimuovi il file di licenza locale
            if os.path.exists(self.license_file):
                os.remove(self.license_file)
            
            return True
            
        except Exception as e:
            logging.error(f"Error deactivating license: {e}")
            return False
            
    def install_license(self, license_file_path: str) -> bool:
        """Install a license file permanently"""
        try:
            if not os.path.exists(license_file_path):
                logging.error("Source license file not found")
                return False
                
            os.makedirs(self.config_dir, exist_ok=True)
            
            # Copy and verify the license file
            with open(license_file_path, 'rb') as src:
                encrypted_data = src.read()
                
            # Verify the license is valid before installing
            try:
                license_data = json.loads(self.crypto.decrypt(encrypted_data))
                key = license_data['key']
                
                # Verifica su Dropbox
                dropbox_status = self.dropbox.check_license_status(key)
                if dropbox_status['status'] == 'revoked':
                    logging.error("License has been revoked")
                    return False
                elif dropbox_status['status'] == 'not_found':
                    logging.error("License not found in central database")
                    return False
                
                # Salva i dettagli della licenza in un file JSON separato
                license_info_path = os.path.join(self.config_dir, "license_info.json")
                with open(license_info_path, 'w') as f:
                    json.dump({
                        'key': key,
                        'metadata': license_data['metadata'],
                        'installation_date': datetime.now().isoformat(),
                        'file_path': self.license_file
                    }, f, indent=4)
                
            except Exception:
                logging.error("Invalid license file format")
                return False
                
            # Save the verified license file
            with open(self.license_file, 'wb') as dst:
                dst.write(encrypted_data)
                
            return True
            
        except Exception as e:
            logging.error(f"Error installing license: {e}")
            return False

    def get_license_info(self) -> dict:
        """Get current license information"""
        try:
            info_path = os.path.join(self.config_dir, "license_info.json")
            if not os.path.exists(info_path):
                return None
                
            with open(info_path, 'r') as f:
                info = json.load(f)
                
            # Aggiungi informazioni aggiuntive
            if os.path.exists(self.license_file):
                with open(self.license_file, 'rb') as f:
                    license_data = json.loads(self.crypto.decrypt(f.read()))
                    
                dropbox_status = self.dropbox.check_license_status(license_data['key'])
                
                # Gestisci le date in modo sicuro
                created_at = info['metadata'].get('created_at')
                if isinstance(created_at, str):
                    try:
                        expiration_date = (
                            datetime.fromisoformat(created_at) + 
                            timedelta(days=info['metadata'].get('valid_days', 0))
                        ).isoformat() if not info['metadata'].get('is_lifetime') else 'Never'
                    except:
                        expiration_date = 'Unknown'
                else:
                    expiration_date = 'Unknown'
                
                info.update({
                    'status': dropbox_status['status'],
                    'last_check': datetime.now().isoformat(),
                    'expiration_date': expiration_date,
                    'days_remaining': self._get_remaining_days(info)
                })
                
            return info
            
        except Exception as e:
            logging.error(f"Error getting license info: {e}")
            return None

    def _get_remaining_days(self, license_info: dict) -> Optional[int]:
        """Calculate remaining days for license"""
        if license_info['metadata'].get('is_lifetime'):
            return None
            
        try:
            created_at = license_info['metadata'].get('created_at')
            valid_days = license_info['metadata'].get('valid_days', 0)
            
            if isinstance(created_at, str):
                expiration = datetime.fromisoformat(created_at) + timedelta(days=valid_days)
                remaining = (expiration - datetime.now()).days
                return max(0, remaining)
        except:
            pass
            
        return 0

    def quick_verify_license(self) -> bool:
        """Verifica veloce della licenza senza controlli online"""
        try:
            if not os.path.exists(self.license_file):
                return False
                
            # Leggi e decripta il file
            with open(self.license_file, 'rb') as f:
                license_data = json.loads(self.crypto.decrypt(f.read()))
            
            # Verifica base
            key = license_data['key']
            metadata = license_data['metadata']
            signature = license_data['signature']
            
            # Verifica firma
            if not self._verify_signature(key, metadata, signature):
                return False
            
            # Verifica scadenza
            if not metadata.get('is_lifetime'):
                expiration = datetime.fromisoformat(metadata['created_at']) + \
                           timedelta(days=metadata['valid_days'])
                if datetime.now() > expiration:
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error in quick license verification: {e}")
            return False