import logging
from .license_generator import LicenseGenerator
from .db_manager import LicenseDBManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

__all__ = ['LicenseGenerator', 'LicenseDBManager'] 