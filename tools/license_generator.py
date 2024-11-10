from src.core.dropbox_sync import DropboxSync
from src.core.crypto_utils import CryptoManager
import random
import string
import hashlib
import argparse
import json
from datetime import datetime, timedelta
import uuid
import base64
import os
import logging
from typing import Dict, Tuple, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_json_file(file_path: str) -> dict:
    """Load JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON file {file_path}: {e}")
        return {}

def save_json_file(file_path: str, data: dict) -> bool:
    """Save JSON file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON file {file_path}: {e}")
        return False

class LicenseTypes:
    LIFETIME = "LIFETIME"
    SUBSCRIPTION = "SUBSCRIPTION"
    TRIAL = "TRIAL"
    BASIC = "BASIC"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"

class LicenseFeatures:
    BASIC = ["basic_features"]
    PROFESSIONAL = ["basic_features", "advanced_features", "priority_support"]
    ENTERPRISE = ["basic_features", "advanced_features", "priority_support", "custom_features"]
    
    @staticmethod
    def get_features_for_type(license_type: str) -> list:
        return {
            LicenseTypes.BASIC: LicenseFeatures.BASIC,
            LicenseTypes.PROFESSIONAL: LicenseFeatures.PROFESSIONAL,
            LicenseTypes.ENTERPRISE: LicenseFeatures.ENTERPRISE,
        }.get(license_type, LicenseFeatures.BASIC)

class LicenseGenerator:
    def __init__(self):
        self.chars = string.ascii_uppercase + string.digits
        self.key_length = 5
        self.segments = 5
        self._master_key = b'YOUR_SUPER_SECRET_MASTER_KEY_CHANGE_THIS'
        self._salt = b'YOUR_SALT_VALUE_CHANGE_THIS'
        self.custom_metadata = {}
        self.license_types = LicenseTypes
        
        try:
            self.dropbox = DropboxSync()
            logging.info("Dropbox sync initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Dropbox sync: {e}")
            self.dropbox = None
            
        self.keys_file = os.path.join("database", "generated_keys.json")
        self.load_generated_keys()
        
    def load_generated_keys(self):
        """Carica le chiavi generate precedentemente"""
        os.makedirs("database", exist_ok=True)
        self.generated_keys = load_json_file(self.keys_file) or {
            'keys': [],
            'stats': {
                'total_generated': 0,
                'active': 0,
                'revoked': 0,
                'expired': 0
            }
        }
            
    def save_generated_keys(self):
        """Salva le chiavi generate"""
        save_json_file(self.keys_file, self.generated_keys)
        
    def _generate_key_segments(self, hardware_id: str = None) -> Tuple[str, str]:
        """Genera i segmenti della chiave con informazioni codificate"""
        # Timestamp codificato (primi 5 caratteri)
        timestamp = int(datetime.now().timestamp())
        timestamp_segment = base64.b32encode(str(timestamp).encode()).decode()[:5]
        
        # Tipo licenza e validità (secondi 5 caratteri)
        license_type = self.custom_metadata.get('type', 'FULL')
        valid_days = self.custom_metadata.get('valid_days', 365)
        type_code = f"{license_type[0]}{valid_days//100}"
        type_segment = base64.b32encode(type_code.encode()).decode()[:5]
        
        # Hash di verifica (terzi 5 caratteri)
        verification_data = f"{timestamp_segment}{type_segment}{hardware_id or ''}"
        verification = hashlib.sha256(verification_data.encode()).hexdigest()[:5].upper()
        
        # Segmenti random per completare
        random_segments = [
            ''.join(random.choices(self.chars, k=5)) 
            for _ in range(2)
        ]
        
        key = f"{timestamp_segment}-{type_segment}-{verification}-{'-'.join(random_segments)}"
        return key, verification
        
    def generate_license_key(self, hardware_id: str = None) -> Tuple[str, Dict]:
        """Genera una nuova chiave di licenza con metadati"""
        key, verification = self._generate_key_segments(hardware_id)
        
        # Gestione licenza lifetime
        is_lifetime = self.custom_metadata.get('type') == LicenseTypes.LIFETIME
        valid_days = 36500 if is_lifetime else self.custom_metadata.get('valid_days', 365)
        
        metadata = {
            'created_at': datetime.now().isoformat(),
            'hardware_id': hardware_id,
            'type': self.custom_metadata.get('type', LicenseTypes.BASIC),
            'valid_days': valid_days,
            'is_lifetime': is_lifetime,
            'version': '3.0',
            'issuer': 'Official License Generator',
            'verification': verification,
            'features': LicenseFeatures.get_features_for_type(
                self.custom_metadata.get('type', LicenseTypes.BASIC)
            ),
            'restrictions': {
                'max_devices': self.custom_metadata.get('max_devices', 1),
                'offline_days': self.custom_metadata.get('offline_days', 7),
                'geographic_restriction': self.custom_metadata.get('geographic_restriction', None),
            },
            'customer_info': self.custom_metadata.get('customer_info', {}),
            'support_level': self.custom_metadata.get('support_level', 'standard'),
            'updates_until': (
                datetime.now() + timedelta(days=valid_days)
            ).isoformat() if not is_lifetime else 'lifetime'
        }
        
        # Aggiungi la chiave alla lista
        key_data = {
            'key': key,
            'metadata': metadata,
            'status': 'active',
            'generated_at': datetime.now().isoformat(),
            'activations': [],
            'revocation_info': None,
            'last_check': None,
            'offline_activations': [],
            'update_history': []
        }
        
        self.generated_keys['keys'].append(key_data)
        self.save_generated_keys()
        
        return key, metadata
        
    def generate_license_file(self, output_path: str, hardware_id: str = None) -> Tuple[str, Dict]:
        """Genera un file di licenza completo"""
        key, metadata = self.generate_license_key(hardware_id)
        encrypted_data = self._create_encrypted_license_file(key, metadata)
        
        # Salva il file di licenza
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
            
        # Aggiorna il record con il percorso del file
        for key_data in self.generated_keys['keys']:
            if key_data['key'] == key:
                key_data['file_path'] = output_path
                break
                
        self.save_generated_keys()
        
        # Carica su Dropbox se disponibile
        if self.dropbox is not None:
            try:
                self.dropbox.upload_license(key, hardware_id, metadata)
            except Exception as e:
                logging.warning(f"Failed to upload license to Dropbox: {e}")
        
        return key, metadata
        
    def revoke_license(self, key: str, reason: str) -> bool:
        """Revoca una licenza"""
        try:
            # Trova la chiave nei record
            for key_data in self.generated_keys['keys']:
                if key_data['key'] == key and key_data['status'] == 'active':
                    # Aggiorna lo stato
                    key_data['status'] = 'revoked'
                    key_data['revocation_info'] = {
                        'date': datetime.now().isoformat(),
                        'reason': reason
                    }
                    
                    # Aggiorna le statistiche
                    self.generated_keys['stats']['active'] -= 1
                    self.generated_keys['stats']['revoked'] += 1
                    
                    # Salva le modifiche
                    self.save_generated_keys()
                    
                    # Revoca su Dropbox
                    self.dropbox.revoke_license(key, reason)
                    
                    return True
                    
            return False
            
        except Exception as e:
            logging.error(f"Error revoking license: {e}")
            return False
            
    def get_license_info(self, key: str) -> Dict:
        """Ottiene informazioni dettagliate su una licenza"""
        for key_data in self.generated_keys['keys']:
            if key_data['key'] == key:
                # Aggiungi informazioni aggiuntive
                key_data['is_expired'] = self._is_license_expired(key_data)
                key_data['days_remaining'] = self._get_remaining_days(key_data)
                key_data['active_devices'] = self._get_active_devices(key_data)
                return key_data
        return None
        
    def _is_license_expired(self, license_data: Dict) -> bool:
        """Verifica se una licenza è scaduta"""
        if license_data['metadata'].get('is_lifetime', False):
            return False
            
        created_at = datetime.fromisoformat(license_data['metadata']['created_at'])
        valid_days = license_data['metadata']['valid_days']
        expiration_date = created_at + timedelta(days=valid_days)
        return datetime.now() > expiration_date
        
    def _get_remaining_days(self, license_data: Dict) -> Optional[int]:
        """Calcola i giorni rimanenti di una licenza"""
        if license_data['metadata'].get('is_lifetime', False):
            return None
            
        created_at = datetime.fromisoformat(license_data['metadata']['created_at'])
        valid_days = license_data['metadata']['valid_days']
        expiration_date = created_at + timedelta(days=valid_days)
        remaining = (expiration_date - datetime.now()).days
        return max(0, remaining)
        
    def _get_active_devices(self, license_data: Dict) -> list:
        """Ottiene la lista dei dispositivi attivi per una licenza"""
        return [
            activation for activation in license_data['activations']
            if activation['status'] == 'active'
        ]

    def update_license(self, key: str, updates: Dict) -> bool:
        """Aggiorna i metadati di una licenza"""
        for key_data in self.generated_keys['keys']:
            if key_data['key'] == key:
                # Registra l'aggiornamento
                key_data['update_history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'changes': updates
                })
                
                # Applica gli aggiornamenti
                key_data['metadata'].update(updates)
                self.save_generated_keys()
                
                # Aggiorna su Dropbox
                if self.dropbox:
                    self.dropbox.upload_license(key, key_data['metadata'].get('hardware_id'), key_data['metadata'])
                    
                return True
        return False

    def extend_license(self, key: str, days: int) -> bool:
        """Estende la validità di una licenza"""
        for key_data in self.generated_keys['keys']:
            if key_data['key'] == key and not key_data['metadata'].get('is_lifetime', False):
                key_data['metadata']['valid_days'] += days
                self.save_generated_keys()
                return True
        return False

    def get_statistics(self) -> Dict:
        """Ottiene statistiche sulle licenze generate"""
        stats = self.generated_keys['stats'].copy()
        
        # Aggiungi statistiche aggiuntive
        stats['by_type'] = {}
        stats['by_month'] = {}
        
        for key_data in self.generated_keys['keys']:
            # Statistiche per tipo
            license_type = key_data['metadata']['type']
            stats['by_type'][license_type] = stats['by_type'].get(license_type, 0) + 1
            
            # Statistiche per mese
            month = datetime.fromisoformat(key_data['generated_at']).strftime('%Y-%m')
            stats['by_month'][month] = stats['by_month'].get(month, 0) + 1
            
        return stats

    def _create_encrypted_license_file(self, key: str, metadata: dict) -> bytes:
        """Create an encrypted license file"""
        try:
            # Create signature
            data = f"{key}:{json.dumps(metadata, sort_keys=True)}"
            signature = hashlib.sha512(data.encode()).hexdigest()
            
            # Create license data
            license_data = {
                'key': key,
                'metadata': metadata,
                'signature': signature,
                'created_at': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat()  # Aggiunto per tracking modifiche
            }
            
            # Encrypt the data
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self._salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self._master_key))
            f = Fernet(key)
            
            # Encrypt and return data
            encrypted_data = f.encrypt(json.dumps(license_data).encode())
            
            # Aggiorna Dropbox se disponibile
            if self.dropbox:
                try:
                    self.dropbox.upload_license(
                        license_data['key'],
                        metadata.get('hardware_id'),
                        metadata
                    )
                except Exception as e:
                    logging.warning(f"Failed to upload license to Dropbox: {e}")
            
            return encrypted_data
            
        except Exception as e:
            logging.error(f"Error creating encrypted license file: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Generate secure license files')
    parser.add_argument('-o', '--output', type=str, required=True,
                      help='Output path for the license file')
    parser.add_argument('--hardware-id', type=str,
                      help='Specific hardware ID to bind the license to')
    parser.add_argument('--type', choices=[
        'BASIC', 'PROFESSIONAL', 'ENTERPRISE', 'TRIAL', 'LIFETIME'
    ], default='BASIC', help='License type')
    parser.add_argument('--valid-days', type=int, default=365,
                      help='Validity period in days')
    parser.add_argument('--max-devices', type=int, default=1,
                      help='Maximum number of allowed devices')
    parser.add_argument('--offline-days', type=int, default=7,
                      help='Maximum days allowed offline')
    parser.add_argument('--geo-restriction', type=str,
                      help='Geographic restriction (country code)')
    parser.add_argument('--customer', type=str,
                      help='Customer information (JSON string)')
    
    args = parser.parse_args()
    
    generator = LicenseGenerator()
    
    try:
        # Configura i metadati personalizzati
        generator.custom_metadata = {
            'type': args.type,
            'valid_days': args.valid_days if args.type != 'LIFETIME' else 36500,
            'max_devices': args.max_devices,
            'offline_days': args.offline_days,
            'geographic_restriction': args.geo_restriction,
            'customer_info': json.loads(args.customer) if args.customer else {},
            'support_level': 'premium' if args.type in ['PROFESSIONAL', 'ENTERPRISE'] else 'standard'
        }
        
        key, metadata = generator.generate_license_file(args.output, args.hardware_id)
        
        print(f"\nLicense generated successfully!")
        print(f"Key: {key}")
        print(f"File: {args.output}")
        print("\nMetadata:")
        for k, v in metadata.items():
            print(f"{k}: {v}")
            
        # Mostra statistiche
        stats = generator.get_statistics()
        print("\nGeneration Statistics:")
        print(f"Total Generated: {stats['total_generated']}")
        print(f"Active: {stats['active']}")
        print(f"Revoked: {stats['revoked']}")
        
    except Exception as e:
        print(f"Error generating license: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())