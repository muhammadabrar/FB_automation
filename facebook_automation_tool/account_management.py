import os
import json
from datetime import datetime
from logging_module import logger

ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), "data", "accounts.json")
os.makedirs(os.path.dirname(ACCOUNTS_FILE), exist_ok=True)

class AccountManager:
    """Manage Facebook accounts with improved handling"""

    def __init__(self, accounts_file=ACCOUNTS_FILE):
        self.accounts_file = accounts_file
        self.accounts = []
        self.load_accounts()

    def load_accounts(self):
        """Load accounts from file or create default"""
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, 'r') as f:
                    data = json.load(f)
                    self.accounts = data.get('accounts', [])
                logger.info(f"Loaded {len(self.accounts)} accounts")
            except Exception as e:
                logger.warning(f"Error loading accounts: {e}")
                self.accounts = []
        else:
            # Default accounts - fixed to be a list of dictionaries
            self.accounts = [
                {"id": "61571921690396", "password": "kkk888"},
                {"id": "61571930150364", "password": "kkk888"},
                {"id": "61571919171009", "password": "kkk888"},
                {"id": "61571926700760", "password": "kkk888"},
                {"id": "61571935220014", "password": "kkk888"}
            ]
            self.save_accounts()

    def save_accounts(self):
        """Save current accounts to file"""
        try:
            data = {
                'accounts': self.accounts,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.accounts_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.accounts)} accounts")
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")

    def get_accounts(self):
        """Get current accounts"""
        return self.accounts.copy()
