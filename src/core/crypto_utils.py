import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import os

class CryptoManager:
    def __init__(self):
        # Chiave master segreta - MANTIENI QUESTO VALORE SICURO E NON CONDIVIDERLO!
        self._master_key = b'YOUR_SUPER_SECRET_MASTER_KEY_CHANGE_THIS'
        self._salt = b'YOUR_SALT_VALUE_CHANGE_THIS'
        
    def _derive_key(self) -> bytes:
        """Deriva una chiave sicura dal master key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self._master_key))
        
    def encrypt(self, data: str) -> bytes:
        """Cripta i dati usando la chiave derivata"""
        key = self._derive_key()
        f = Fernet(key)
        return f.encrypt(data.encode())
        
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decripta i dati usando la chiave derivata"""
        key = self._derive_key()
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode() 