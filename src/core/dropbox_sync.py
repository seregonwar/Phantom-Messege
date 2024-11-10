import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError
import json
import os
import logging
from datetime import datetime

class DropboxSync:
    def __init__(self):
        self.access_token = ""
        self.dbx = dropbox.Dropbox(oauth2_access_token=self.access_token)
        self.license_folder = "/licenses"
        self.revoked_folder = "/licenses/revoked"
        
        # Cache per ridurre le richieste
        self._cache = {
            'licenses': None,
            'last_update': None,
            'cache_duration': 300  # 5 minuti
        }
        
    def get_all_licenses(self) -> list:
        """Get all licenses with caching"""
        # Usa la cache se valida
        if (self._cache['licenses'] is not None and 
            self._cache['last_update'] and 
            (datetime.now() - self._cache['last_update']).total_seconds() < self._cache['cache_duration']):
            return self._cache['licenses']
            
        try:
            licenses = []
            
            # Ottieni solo le licenze attive
            result = self.dbx.files_list_folder(self.license_folder)
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    _, response = self.dbx.files_download(entry.path_display)
                    license_data = json.loads(response.content)
                    licenses.append(license_data)
                    
            # Aggiorna la cache
            self._cache['licenses'] = licenses
            self._cache['last_update'] = datetime.now()
            
            return licenses
            
        except Exception as e:
            logging.error(f"Error getting licenses: {e}")
            return self._cache['licenses'] or []  # Usa cache anche se scaduta in caso di errore
            
    def check_license_status(self, license_key: str) -> dict:
        """Check if a license is valid"""
        try:
            # Controlla prima le licenze attive
            file_path = f"{self.license_folder}/{license_key}.json"
            try:
                _, response = self.dbx.files_download(file_path)
                return {'status': 'active', 'data': json.loads(response.content)}
            except:
                pass
                
            # Se non è attiva, controlla se è revocata
            revoked_path = f"{self.revoked_folder}/{license_key}.json"
            try:
                _, response = self.dbx.files_download(revoked_path)
                return {'status': 'revoked', 'data': json.loads(response.content)}
            except:
                pass
                
            return {'status': 'not_found'}
            
        except Exception as e:
            logging.error(f"Error checking license: {e}")
            return {'status': 'error'}
            
    def revoke_license(self, license_key: str, reason: str = None) -> bool:
        """Revoke a license"""
        try:
            # Ottieni i dati della licenza attiva
            file_path = f"{self.license_folder}/{license_key}.json"
            _, response = self.dbx.files_download(file_path)
            license_data = json.loads(response.content)
            
            # Aggiungi info revoca
            license_data['status'] = 'revoked'
            license_data['revoked_at'] = datetime.now().isoformat()
            license_data['revoke_reason'] = reason
            
            # Sposta in revoked
            revoked_path = f"{self.revoked_folder}/{license_key}.json"
            self.dbx.files_upload(
                json.dumps(license_data).encode(),
                revoked_path,
                mode=WriteMode('overwrite')
            )
            
            # Elimina da active
            self.dbx.files_delete_v2(file_path)
            
            # Invalida cache
            self._cache['licenses'] = None
            
            return True
            
        except Exception as e:
            logging.error(f"Error revoking license: {e}")
            return False

    def update_license(self, license_key: str, metadata: dict) -> bool:
        """Update license metadata on Dropbox"""
        try:
            # Controlla se la licenza esiste
            file_path = f"{self.license_folder}/{license_key}.json"
            try:
                _, response = self.dbx.files_download(file_path)
                current_data = json.loads(response.content)
            except:
                logging.error(f"License {license_key} not found")
                return False
                
            # Aggiorna i metadati
            current_data.update({
                'metadata': metadata,
                'last_modified': datetime.now().isoformat()
            })
            
            # Carica il file aggiornato
            self.dbx.files_upload(
                json.dumps(current_data, indent=2).encode(),
                file_path,
                mode=WriteMode('overwrite')
            )
            
            # Invalida la cache
            self._cache['licenses'] = None
            
            logging.info(f"Updated license {license_key}")
            return True
            
        except Exception as e:
            logging.error(f"Error updating license: {e}")
            return False

    def check_connection(self) -> bool:
        """Verifica la connessione a Dropbox"""
        try:
            self.dbx.users_get_current_account()
            return True
        except:
            return False

    def upload_license(self, license_key: str, hardware_id: str = None, metadata: dict = None) -> bool:
        """Upload a license file to Dropbox"""
        try:
            # Prepara i dati della licenza
            license_data = {
                'license_key': license_key,
                'hardware_id': hardware_id,
                'data': metadata,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # Carica il file
            file_path = f"{self.license_folder}/{license_key}.json"
            self.dbx.files_upload(
                json.dumps(license_data, indent=2).encode(),
                file_path,
                mode=WriteMode('overwrite')
            )
            
            # Invalida la cache
            self._cache['licenses'] = None
            
            logging.info(f"Uploaded license {license_key}")
            return True
            
        except Exception as e:
            logging.error(f"Error uploading license: {e}")
            return False