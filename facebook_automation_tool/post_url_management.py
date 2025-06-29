import os
import json
from datetime import datetime
from logging_module import logger
import re

POST_URLS_FILE = os.path.join(os.path.dirname(__file__), "data", "post_urls.json")
os.makedirs(os.path.dirname(POST_URLS_FILE), exist_ok=True)

class PostURLManager:
    """Manage post URLs and user interactions"""

    def __init__(self, config_file=None):
        if config_file is None:
            config_file = POST_URLS_FILE
        self.config_file = config_file
        self.current_urls = []
        self.load_urls()

    def load_urls(self):
        """Load saved post URLs from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.current_urls = data.get('urls', [])
                logger.info(f"Loaded {len(self.current_urls)} saved post URLs")
            except Exception as e:
                logger.warning(f"Error loading post URLs: {e}")
                self.current_urls = []
        else:
            # Default post URL
            self.current_urls = ["https://www.facebook.com/share/p/1ZQbJMQ2wW/"]
            self.save_urls()

    def save_urls(self):
        """Save current post URLs to file"""
        try:
            data = {
                'urls': self.current_urls,
                'last_updated': datetime.now().isoformat(),
                'total_urls': len(self.current_urls)
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.current_urls)} post URLs")
        except Exception as e:
            logger.error(f"Error saving post URLs: {e}")

    def get_urls(self):
        """Get current post URLs"""
        return self.current_urls.copy()