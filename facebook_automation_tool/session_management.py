import os
import json
from datetime import datetime
from logging_module import logger

SESSION_FILE = os.path.join(os.path.dirname(__file__), "data", "session_state.json")
os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)

class SessionState:
    """Manage session state and recovery with improved account tracking"""

    def __init__(self, session_file=None):
        if session_file is None:
            session_file = SESSION_FILE
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

    def mark_login_attempt(self, account_id, success):
        """Record login attempt result"""
        if account_id not in self.state["login_attempts"]:
            self.state["login_attempts"].append(account_id)

        if success:
            if account_id not in self.state["successful_logins"]:
                self.state["successful_logins"].append(account_id)
            if account_id in self.state["failed_logins"]:
                self.state["failed_logins"].remove(account_id)
        else:
            if account_id not in self.state["failed_logins"]:
                self.state["failed_logins"].append(account_id)
            if account_id in self.state["successful_logins"]:
                self.state["successful_logins"].remove(account_id)

        self.save_state()

    def mark_post_processed(self, account_id, post_url):
        """Mark an account as having completed post interaction for a specific post"""
        entry = {"account_id": account_id, "post_url": post_url}
        if entry not in self.state["processed_posts"]:
            self.state["processed_posts"].append(entry)
        self.save_state()

    def has_processed_post(self, account_id, post_url):
        """Check if account has processed a specific post"""
        return {"account_id": account_id, "post_url": post_url} in self.state["processed_posts"]

    def get_accounts_for_login(self, all_accounts):
        """Get accounts that haven't attempted login yet"""
        attempted_ids = set(self.state["login_attempts"])
        return [acc for acc in all_accounts if acc.get("id") not in attempted_ids]

    def get_accounts_for_posts(self, all_accounts, post_urls):
        """
        Get (account, post_url) pairs that need post processing:
        - Only for accounts that have successfully logged in
        - Only for posts that haven't been processed by that account
        """
        result = []
        successful_ids = set(self.state["successful_logins"])
        
        for acc in all_accounts:
            account_id = acc.get("id")
            if account_id in successful_ids:
                for url in post_urls:
                    if not self.has_processed_post(account_id, url):
                        result.append((acc, url))
        return result

    def get_remaining_accounts(self, all_accounts, post_urls):
        """Get all accounts that haven't completed both login and posts"""
        login_remaining = self.get_accounts_for_login(all_accounts)
        posts_remaining = self.get_accounts_for_posts(all_accounts, post_urls)
        return login_remaining + [acc for acc, _ in posts_remaining]

    def get_account_by_id(self, all_accounts, account_id):
        """Get account object by ID"""
        for acc in all_accounts:
            if acc.get("id") == account_id:
                return acc
        return None

    def get_login_status(self, all_accounts):
        """Get comprehensive login status for all accounts"""
        status = {
            "total": len(all_accounts),
            "attempted": len(self.state["login_attempts"]),
            "successful": len(self.state["successful_logins"]),
            "failed": len(self.state["failed_logins"]),
            "pending": []
        }
        
        attempted_ids = set(self.state["login_attempts"])
        for acc in all_accounts:
            account_id = acc.get("id")
            if account_id not in attempted_ids:
                status["pending"].append(account_id)
        
        return status

    def get_post_processing_status(self, all_accounts, post_urls):
        """Get comprehensive post processing status"""
        total_tasks = len(self.state["successful_logins"]) * len(post_urls)
        completed_tasks = len(self.state["processed_posts"])
        
        status = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "remaining_tasks": total_tasks - completed_tasks,
            "accounts_with_successful_login": len(self.state["successful_logins"]),
            "posts_per_account": len(post_urls)
        }
        
        return status

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

    def set_current_account(self, account_id):
        """Set the currently active account"""
        self.state["current_account"] = account_id
        self.save_state()

    def get_current_account(self):
        """Get the currently active account ID"""
        return self.state.get("current_account")

    def print_session_summary(self, all_accounts, post_urls=None):
        """Print a summary of the current session state"""
        print("\n" + "="*60)
        print("📊 SESSION SUMMARY")
        print("="*60)
        
        login_status = self.get_login_status(all_accounts)
        print(f"Login Status:")
        print(f"  Total Accounts: {login_status['total']}")
        print(f"  Login Attempts: {login_status['attempted']}")
        print(f"  Successful: {login_status['successful']}")
        print(f"  Failed: {login_status['failed']}")
        print(f"  Pending: {len(login_status['pending'])}")
        
        if post_urls:
            post_status = self.get_post_processing_status(all_accounts, post_urls)
            print(f"\nPost Processing Status:")
            print(f"  Total Tasks: {post_status['total_tasks']}")
            print(f"  Completed: {post_status['completed_tasks']}")
            print(f"  Remaining: {post_status['remaining_tasks']}")
        
        print(f"\nSession ID: {self.state['session_id']}")
        print(f"Started: {self.state['start_time']}")
        print(f"Last Updated: {self.state['last_update']}")
        print("="*60)