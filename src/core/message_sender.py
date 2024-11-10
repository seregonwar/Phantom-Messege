import uuid
import requests
import time
import random
from ..text_generator import TextGenerator
from ..utils.logger import MessageLogger

class MessageSender:
    def __init__(self, config):
        try:
            self.url = config["BASE_URL"]
            self.headers = config["HEADERS"]
            self.username = config["USERNAME"]
            self.text_generator = TextGenerator()
            self.logger = MessageLogger()
            self.current_profile = "normal"
            
            # Default timing configuration
            self.timing_config = {
                'base_delay': {
                    'min': 10.0,
                    'max': 30.0
                },
                'variation_factor': 0.3,
                'burst_protection': 120.0,
                'burst_threshold': 5
            }
        except Exception as e:
            print(f"Error initializing MessageSender: {str(e)}")
            raise

    def set_timing_config(self, min_delay: float, max_delay: float, 
                         burst_protection: float = None, burst_threshold: int = None,
                         variation_factor: float = None, profile_name: str = "custom"):
        """Set the timing configuration"""
        self.timing_config['base_delay']['min'] = max(5.0, min_delay)  # Minimum 5 seconds
        self.timing_config['base_delay']['max'] = max(min_delay + 5, max_delay)
        
        if burst_protection is not None:
            self.timing_config['burst_protection'] = burst_protection
        if burst_threshold is not None:
            self.timing_config['burst_threshold'] = burst_threshold
        if variation_factor is not None:
            self.timing_config['variation_factor'] = max(0.1, min(0.5, variation_factor))
        
        self.current_profile = profile_name

    def _create_payload(self, message):
        return {
            "username": self.username,
            "question": message,
            "deviceId": str(uuid.uuid4()),
            "gameSlug": "",
            "gameId": "default"
        }

    def _get_random_delay(self, message: str, message_count: int) -> float:
        """Generate a smart random delay based on various factors."""
        # Base delay
        base = random.uniform(
            self.timing_config['base_delay']['min'], 
            self.timing_config['base_delay']['max']
        )
        
        # Add random variation
        variation = base * random.uniform(
            -self.timing_config['variation_factor'], 
            self.timing_config['variation_factor']
        )
        delay = base + variation
        
        # Add burst protection
        if message_count > 0 and message_count % self.timing_config['burst_threshold'] == 0:
            self.logger.log_burst_protection()
            delay += self.timing_config['burst_protection']
            
        # Add length factor (longer messages need more time)
        length_factor = len(message) / 100  # 1 extra second for every 100 characters
        delay += length_factor
        
        # Add random "human" factor
        if random.random() < 0.1:  # 10% chance
            delay += random.uniform(5, 15)  # Random "distraction"
            
        return max(5.0, delay)  # Minimum 5 seconds

    def send_message(self, message, use_random_text=False):
        try:
            final_message = self.text_generator.generate_message() if use_random_text else message
            start_time = time.time()
            
            response = requests.post(
                self.url, 
                headers=self.headers, 
                data=self._create_payload(final_message)
            )
            
            delay = time.time() - start_time
            success = response.status_code == 200
            
            self.logger.log_message(
                message=final_message,
                success=success,
                delay=delay,
                profile=self.current_profile
            )
            
            if success:
                print(f"Message sent successfully: {final_message}")
            else:
                print(f"Error sending message. Status code: {response.status_code}")
            
            return success
            
        except Exception as e:
            self.logger.logger.error(f"Error sending message: {e}")
            return False

    def text_bomb(self, message, count, use_random_text=False):
        successful, failed = super().text_bomb(message, count, use_random_text)
        
        print("\n=== Sending Statistics ===")
        self.logger.print_stats()
        self.logger.save_stats()
        
        return successful, failed