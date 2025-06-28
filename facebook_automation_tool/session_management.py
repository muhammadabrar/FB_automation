import os
import json
from datetime import datetime
from logging_module import logger

class SessionState:
    """Manage session state and recovery with improved account tracking"""

    def __init__(self, session_file="session_state.json"):
        self.session_file = session_file
        self.state = self.load_state()

    def load_state(self):
        """Load session state from file"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load session state: {e}")
        # Only create new state if file does not exist
        return {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "login_attempts": [],
            "successful_logins": [],
            "failed_logins": [],
            "processed_posts": [],
            "current_account": None,
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }

    def save_state(self):
        """Save current session state"""
        self.state["last_update"] = datetime.now().isoformat()
        try:
            with open(self.session_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")

    def mark_login_attempt(self, account, success):
        """Record login attempt result"""
        if account not in self.state["login_attempts"]:
            self.state["login_attempts"].append(account)

        if success:
            if account not in self.state["successful_logins"]:
                self.state["successful_logins"].append(account)
            if account in self.state["failed_logins"]:
                self.state["failed_logins"].remove(account)
        else:
            if account not in self.state["failed_logins"]:
                self.state["failed_logins"].append(account)
            if account in self.state["successful_logins"]:
                self.state["successful_logins"].remove(account)

        self.save_state()

    def mark_post_processed(self, account, post_url):
        """Mark an account as having completed post interaction for a specific post"""
        entry = {"account": account, "post_url": post_url}
        if entry not in self.state["processed_posts"]:
            self.state["processed_posts"].append(entry)
        self.save_state()

    def has_processed_post(self, account, post_url):
        """Check if account has processed a specific post"""
        return {"account": account, "post_url": post_url} in self.state["processed_posts"]

    def get_accounts_for_login(self, all_accounts):
        """Get accounts that haven't attempted login yet"""
        return [acc for acc in all_accounts if acc not in self.state["login_attempts"]]

    def get_accounts_for_posts(self, all_accounts, post_urls):
        """
        Get (account, post_url) pairs that need post processing:
        - Only for accounts that have successfully logged in
        - Only for posts that haven't been processed by that account
        """
        result = []
        for acc in self.state["successful_logins"]:
            if acc in all_accounts:
                for url in post_urls:
                    if not self.has_processed_post(acc, url):
                        result.append((acc, url))
        return result

    def get_remaining_accounts(self, all_accounts, post_urls):
        """Get all accounts that haven't completed both login and posts"""
        login_remaining = self.get_accounts_for_login(all_accounts)
        posts_remaining = self.get_accounts_for_posts(all_accounts, post_urls)
        return login_remaining + posts_remaining

    def reset_session(self):
        """Reset session for new run"""
        self.state = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "login_attempts": [],
            "successful_logins": [],
            "failed_logins": [],
            "processed_posts": [],
            "current_account": None,
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }
        self.save_state()
