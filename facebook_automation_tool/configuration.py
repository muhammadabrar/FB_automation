import os
import json
import logging
from datetime import datetime

logger = logging.getLogger('FacebookAutomation')

class AutomationConfig:
    """Configuration management for automation"""

    def __init__(self, config_file="automation_config.json"):
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        """Load configuration from file or create default"""
        default_config = {
            "delays": {
                "human_min": 2,
                "human_max": 8,
                "action_delay": 1.5,
                "page_load": 3
            },
            "timeouts": {
                "login_max_wait": 120,
                "page_load": 30,
                "element_wait": 10
            },
            "retry": {
                "max_attempts": 3,
                "base_delay": 2
            },
            "browser": {
                "headless": False,
                "viewport_width": 1280,
                "viewport_height": 720
            },
            "posts": {
                "comment_variations": [
                    "Nice post!",
                    "Great content!",
                    "Love this!",
                    "Amazing!",
                    "Well said!",
                    "Awesome!",
                    "Perfect!",
                    "Excellent!"
                ]
            }
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.config = {**default_config, **loaded_config}
                logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                logger.warning(f"Error loading config file: {e}. Using defaults.")
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, key_path, default=None):
        """Get configuration value using dot notation (e.g., 'delays.human_min')"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

config = AutomationConfig()
