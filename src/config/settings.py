import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_file: str = "config/timing_profiles.json"):
        self.config_file = config_file
        self.default_config = {
            'normal': {
                'min_delay': 10.0,
                'max_delay': 30.0,
                'burst_protection': 120.0,
                'burst_threshold': 5,
                'variation_factor': 0.3
            },
            'stealth': {
                'min_delay': 30.0,
                'max_delay': 180.0,
                'burst_protection': 300.0,
                'burst_threshold': 3,
                'variation_factor': 0.5
            },
            'aggressive': {
                'min_delay': 5.0,
                'max_delay': 15.0,
                'burst_protection': 60.0,
                'burst_threshold': 10,
                'variation_factor': 0.2
            }
        }
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configurations from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return self.default_config
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return self.default_config

    def save_config(self, name: str, config: Dict[str, Any]) -> bool:
        """Save a new configuration"""
        try:
            current_config = self.load_config()
            current_config[name] = config
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(current_config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def get_profile(self, name: str) -> Dict[str, Any]:
        """Get a specific configuration"""
        configs = self.load_config()
        return configs.get(name, self.default_config['normal'])

    def list_profiles(self) -> list:
        """List all available profiles"""
        return list(self.load_config().keys())