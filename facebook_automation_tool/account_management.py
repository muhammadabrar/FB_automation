import os
import json
from datetime import datetime
from logging_module import logger

ACCOUNTS_FILE = "accounts.json"

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
            # Default accounts
            self.accounts = [
                "61571921690396",
                "61571930150364",
                "61571919171009",
                "61571926700760",
                "61571935220014"
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

    def add_account(self, account):
        """Add a new account"""
        if account and account not in self.accounts:
            self.accounts.append(account)
            self.save_accounts()
            return True
        return False

    def remove_account(self, account):
        """Remove an account"""
        if account in self.accounts:
            self.accounts.remove(account)
            self.save_accounts()
            return True
        return False

    def get_accounts(self):
        """Get current accounts"""
        return self.accounts.copy()

    def clear_accounts(self):
        """Clear all accounts"""
        self.accounts = []
        self.save_accounts()

    def interactive_account_management(self):
        """Interactive account management"""
        while True:
            print("\n" + "="*60)
            print("👥 ACCOUNT MANAGEMENT")
            print("="*60)

            if self.accounts:
                print("Current Accounts:")
                for i, account in enumerate(self.accounts, 1):
                    print(f"  {i}. {account}")
            else:
                print("No accounts configured.")

            print("\nOptions:")
            print("1. Add new account")
            print("2. Remove account")
            print("3. Clear all accounts")
            print("4. Continue with current accounts")
            print("5. Exit program")

            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == "1":
                account = input("Enter new account (username/email/phone): ").strip()
                if account:
                    if self.add_account(account):
                        print(f"✅ Added: {account}")
                    else:
                        print("⚠️ Account already exists or invalid")
                else:
                    print("❌ Invalid account")

            elif choice == "2":
                if not self.accounts:
                    print("❌ No accounts to remove")
                    continue

                print("Select account to remove:")
                for i, account in enumerate(self.accounts, 1):
                    print(f"  {i}. {account}")

                try:
                    idx = int(input("Enter number: ").strip()) - 1
                    if 0 <= idx < len(self.accounts):
                        removed_account = self.accounts[idx]
                        self.remove_account(removed_account)
                        print(f"✅ Removed: {removed_account}")
                    else:
                        print("❌ Invalid selection")
                except ValueError:
                    print("❌ Invalid input")

            elif choice == "3":
                confirm = input("Clear all accounts? (yes/no): ").strip().lower()
                if confirm in ['yes', 'y']:
                    self.clear_accounts()
                    print("✅ All accounts cleared")

            elif choice == "4":
                if not self.accounts:
                    print("❌ No accounts configured. Please add at least one account.")
                    continue
                print("✅ Continuing with current accounts")
                break

            elif choice == "5":
                print("👋 Exiting program")
                return False

            else:
                print("❌ Invalid choice")

        return True
