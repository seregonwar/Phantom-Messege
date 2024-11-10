import os
import sys

# Aggiungi la directory root al Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from tools.license_generator_gui import main

if __name__ == "__main__":
    main() 