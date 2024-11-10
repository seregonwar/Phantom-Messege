import os
import sys
import logging
from datetime import datetime

# Aggiungi il percorso root al Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

# Configura logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

# Importa le dipendenze comuni
from src.core.dropbox_sync import DropboxSync
from src.core.crypto_utils import CryptoManager

# Funzioni di utilità comuni
def format_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def load_json_file(file_path: str) -> dict:
    import json
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON file {file_path}: {e}")
        return {}

def save_json_file(file_path: str, data: dict) -> bool:
    import json
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON file {file_path}: {e}")
        return False 