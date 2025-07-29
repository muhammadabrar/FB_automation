import os
import csv
import time
import random
import logging
from datetime import datetime
from configuration import config
from logging_module import logger
from dataclasses import dataclass
from contextlib import contextmanager
from session_management import SessionState
from account_management import AccountManager
from typing import List, Dict, Tuple, Optional
from playwright.sync_api import sync_playwright
from post_url_management import PostURLManager
from login_handler import enhanced_login_to_facebook
from utils import human_like_delay, random_user_agent
from post_interaction import enhanced_like_comment_post


@dataclass
class AutomationConfig:
    """Configuration constants for the automation tool"""
    LOG_DIR: str = "logs"
    SUCCESS_FILE: str = os.path.join(LOG_DIR, "successful_accounts.txt")
    DISABLED_FILE: str = os.path.join(LOG_DIR, "disabled_accounts.txt")
    ACTIVITY_LOG: str = os.path.join(LOG_DIR, "activity_log.csv")
    
    # Timing configurations
    ACCOUNT_DELAY_RANGE: Tuple[float, float] = (5.0, 10.0)
    POST_DELAY_RANGE: Tuple[float, float] = (5.0, 15.0)
    LOGIN_CHECK_DELAY_RANGE: Tuple[float, float] = (2.0, 4.0)
    
    # Browser configurations
    VIEWPORT_WIDTH: int = 1280
    VIEWPORT_HEIGHT: int = 720


class CSVLogger:
    """Handles CSV logging operations"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self._initialize_csv_log()
    
    def _initialize_csv_log(self) -> None:
        """Initialize CSV log file with headers"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'Timestamp', 'Account', 'Action', 'Status', 'Details', 'Post_URL', 'Duration_Seconds'
                ])
    
    def log_activity(self, account: str, action: str, status: str, 
                    details: str = "", post_url: str = "", duration: Optional[float] = None) -> None:
        """Enhanced CSV logging with duration tracking"""
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    account,
                    action,
                    status,
                    details,
                    post_url,
                    duration if duration else ""
                ])
        except Exception as e:
            logger.error(f"Failed to write to CSV log: {str(e)}")


class LoginStatusChecker:
    """Handles login status verification"""
    
    POST_SELECTORS = [
        'h3:has-text("Create a post")',
        '[aria-label="Create a post"]',
        'span:has-text("What\'s on your mind")',
        '[placeholder*="What\'s on your mind"]'
    ]
    
    @classmethod
    def is_logged_in(cls, page) -> bool:
        """Check if user is logged in"""
        try:
            for selector in cls.POST_SELECTORS:
                if page.locator(selector).is_visible(timeout=3000):
                    return True
            return False
        except:
            return False


class BrowserManager:
    """Manages browser context creation and configuration"""
    
    def __init__(self, config: AutomationConfig):
        self.config = config
    
    @staticmethod
    def get_profile_dir(account: str) -> str:
        """Get unique profile directory for each account"""
        return os.path.expanduser(f"~/chrome_profile_{account}")
    
    def _get_browser_args(self) -> List[str]:
        """Get browser launch arguments"""
        return [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-popup-blocking',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ]
    
    @contextmanager
    def create_browser_context(self, account_id: str):
        """Create and manage browser context with proper cleanup"""
        profile_dir = self.get_profile_dir(account_id)
        browser = None
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    headless=config.get('browser.headless', False),
                    viewport={
                        'width': config.get('browser.viewport_width', self.config.VIEWPORT_WIDTH),
                        'height': config.get('browser.viewport_height', self.config.VIEWPORT_HEIGHT)
                    },
                    user_agent=random_user_agent(),
                    args=self._get_browser_args()
                )
                
                page = browser.new_page()
                yield page, browser
                
        except Exception as e:
            logger.error(f"Browser context error for {account_id}: {str(e)}")
            raise
        finally:
            if browser:
                try:
                    browser.close()
                except Exception as e:
                    if "Event loop is closed" not in str(e):
                        logger.error(f"Error closing browser: {str(e)}")


class LoginProcessor:
    """Handles the login phase of automation"""
    
    def __init__(self, session: SessionState, browser_manager: BrowserManager, 
                 csv_logger: CSVLogger, automation_config: AutomationConfig):
        self.session = session
        self.browser_manager = browser_manager
        self.csv_logger = csv_logger
        self.config = automation_config
    
    def process_login_phase(self, accounts: List[Dict]) -> None:
        """Process login attempts for all accounts"""
        accounts_to_login = self.session.get_accounts_for_login(accounts)
        logger.info(f"Accounts needing login: {len(accounts_to_login)}")
        
        for i, account in enumerate(accounts_to_login, 1):
            self._process_single_login(account, i, len(accounts_to_login))
            self._add_inter_account_delay(i, len(accounts_to_login))
    
    def _process_single_login(self, account: Dict, current: int, total: int) -> None:
        """Process login for a single account"""
        account_id = account.get("id")
        account_password = account.get("password")
        
        logger.info(f"🔐 LOGIN PHASE: Processing account {current}/{total}: {account_id}")
        self.session.set_current_account(account_id)
        
        try:
            with self.browser_manager.create_browser_context(account_id) as (page, browser):
                if enhanced_login_to_facebook(page, account_id, account_password, self.session):
                    logger.info(f"✅ LOGIN SUCCESS for {account_id}")
                else:
                    logger.error(f"❌ LOGIN FAILED for {account_id}")
                    
        except Exception as e:
            logger.error(f"💥 Error during login for {account_id}: {str(e)}")
            self.csv_logger.log_activity(account_id, "BROWSER", "ERROR", str(e))
    
    def _add_inter_account_delay(self, current: int, total: int) -> None:
        """Add delay between account processing"""
        if current < total:
            delay = random.uniform(*self.config.ACCOUNT_DELAY_RANGE)
            logger.info(f"⏳ Waiting {delay:.1f}s before next account...")
            time.sleep(delay)


class PostProcessor:
    """Handles the post interaction phase of automation"""
    
    def __init__(self, session: SessionState, browser_manager: BrowserManager, 
                 csv_logger: CSVLogger, automation_config: AutomationConfig):
        self.session = session
        self.browser_manager = browser_manager
        self.csv_logger = csv_logger
        self.config = automation_config
        self.login_checker = LoginStatusChecker()
    
    def process_post_phase(self, accounts: List[Dict], post_urls: List[str]) -> None:
        """Process post interactions for all account-post combinations"""
        post_tasks = self.session.get_accounts_for_posts(accounts, post_urls)
        logger.info(f"Post tasks to process: {len(post_tasks)}")
        
        for i, (account, post_url) in enumerate(post_tasks, 1):
            self._process_single_post_task(account, post_url, i, len(post_tasks))
            self._add_inter_post_delay(i, len(post_tasks))
    
    def _process_single_post_task(self, account: Dict, post_url: str, 
                                 current: int, total: int) -> None:
        """Process a single post interaction task"""
        account_id = account.get("id")
        account_password = account.get("password")
        
        logger.info(f"📝 POST PHASE: Processing task {current}/{total}: {account_id} -> {post_url}")
        self.session.set_current_account(account_id)
        
        try:
            with self.browser_manager.create_browser_context(account_id) as (page, browser):
                if self._ensure_logged_in(page, account_id, account_password,from_post=True):
                    self._interact_with_post(page, post_url, account_id)
                else:
                    logger.error(f"❌ Could not establish login for {account_id}, skipping post: {post_url}")
                    
        except Exception as e:
            logger.error(f"💥 Error during post interaction for {account_id}: {str(e)}")
            self.csv_logger.log_activity(account_id, "BROWSER", "ERROR", str(e))
    
    def _ensure_logged_in(self, page, account_id: str, account_password: str,from_post:Optional[bool]=False) -> bool:
        """Ensure the account is logged in, attempt re-login if necessary"""
        page.goto('https://www.facebook.com')
        human_like_delay(*self.config.LOGIN_CHECK_DELAY_RANGE)
        
        if not self.login_checker.is_logged_in(page):
            logger.warning(f"⚠️ Session lost for {account_id}, attempting re-login")
            return enhanced_login_to_facebook(page, account_id, account_password, self.session,from_post=from_post)
        
        return True
    
    def _interact_with_post(self, page, post_url: str, account_id: str) -> None:
        """Interact with a specific post"""
        if enhanced_like_comment_post(page, post_url, account_id):
            logger.info(f"🎉 POST SUCCESS: {account_id} -> {post_url}")
            self.session.mark_post_processed(account_id, post_url)
        else:
            logger.error(f"❌ POST FAILED: {account_id} -> {post_url}")
    
    def _add_inter_post_delay(self, current: int, total: int) -> None:
        """Add delay between post processing"""
        if current < total:
            delay = random.uniform(*self.config.POST_DELAY_RANGE)
            logger.info(f"⏳ Waiting {delay:.1f}s before next post...")
            time.sleep(delay)


class ReportGenerator:
    """Handles report generation and summary display"""
    
    @staticmethod
    def display_startup_banner() -> None:
        """Display startup banner with information"""
        print("="*80)
        print("🚀 ENHANCED FACEBOOK AUTOMATION TOOL")
        print("="*80)
        print("Features:")
        print("✅ Secure credential management")
        print("✅ Advanced security challenge handling")
        print("✅ Interactive account and post management")
        print("✅ Session state recovery")
        print("✅ Comprehensive logging and reporting")
        print("✅ Human-like behavior simulation")
        print("✅ Rate limiting and retry mechanisms")
        print("✅ Separate login and post processing phases")
        print("="*80)
        print()
    
    @staticmethod
    def generate_final_statistics(session: SessionState, accounts: List[Dict], 
                                post_urls: List[str]) -> None:
        """Generate and log final statistics"""
        logger.info("🏁 AUTOMATION COMPLETED")
        session.print_session_summary(accounts, post_urls)
        
        login_status = session.get_login_status(accounts)
        post_status = session.get_post_processing_status(accounts, post_urls)
        
        logger.info(f"📊 FINAL STATISTICS:")
        logger.info(f"  Total Accounts: {login_status['total']}")
        logger.info(f"  Login Attempts: {login_status['attempted']}")
        logger.info(f"  Successful Logins: {login_status['successful']}")
        logger.info(f"  Failed Logins: {login_status['failed']}")
        logger.info(f"  Post Tasks Completed: {post_status['completed_tasks']}/{post_status['total_tasks']}")
        
        if login_status['failed'] > 0:
            logger.warning(f"⚠️ {login_status['failed']} accounts failed to login")
        
        if post_status['remaining_tasks'] > 0:
            logger.warning(f"⚠️ {post_status['remaining_tasks']} post tasks remaining")
    
    @staticmethod
    def display_final_summary(session: SessionState, account_manager: AccountManager) -> None:
        """Display a comprehensive final summary"""
        accounts = account_manager.get_accounts()
        
        print("\n" + "="*80)
        print("🎯 FINAL AUTOMATION SUMMARY")
        print("="*80)
        
        # Account status breakdown
        print("📋 ACCOUNT STATUS:")
        successful_ids = set(session.state.get('successful_logins', []))
        failed_ids = set(session.state.get('failed_logins', []))
        
        for account in accounts:
            account_id = account.get("id")
            if account_id in successful_ids:
                status = "✅ SUCCESSFUL"
            elif account_id in failed_ids:
                status = "❌ FAILED"
            else:
                status = "⏳ PENDING"
            
            print(f"  {account_id}: {status}")
        
        # Post processing summary
        processed_posts = session.state.get('processed_posts', [])
        print(f"Debug: processed_posts type: {type(processed_posts)}, value: {processed_posts}")
        if processed_posts:
            print(f"📝 POST INTERACTIONS COMPLETED: {len(processed_posts)}")
            post_summary = {}
            for entry in processed_posts:
                account_id = entry.get('account_id', 'Unknown')
                if account_id not in post_summary:
                    post_summary[account_id] = 0
                post_summary[account_id] += 1

            for account_id, count in post_summary.items():
                print(f"  {account_id}: {count} posts processed")
        
        print(f"\n🕒 Session Duration: {session.state.get('session_id', 'Unknown')}")
        print(f"⏰ Started: {session.state.get('start_time', 'Unknown')}")
        print(f"🔄 Last Updated: {session.state.get('last_update', 'Unknown')}")
        print("="*80)


class FacebookAutomationOrchestrator:
    """Main orchestrator class that coordinates all automation components"""
    
    def __init__(self):
        self.config = AutomationConfig()
        self.session = SessionState()
        self.account_manager = AccountManager()
        self.post_url_manager = PostURLManager()
        self.csv_logger = CSVLogger(self.config.ACTIVITY_LOG)
        self.browser_manager = BrowserManager(self.config)
        self.report_generator = ReportGenerator()
        
        # Initialize processors
        self.login_processor = LoginProcessor(
            self.session, self.browser_manager, self.csv_logger, self.config
        )
        self.post_processor = PostProcessor(
            self.session, self.browser_manager, self.csv_logger, self.config
        )
    
    def run_automation(self) -> None:
        """Main automation execution method"""
        # Load data and initialize
        accounts = self.account_manager.get_accounts()
        post_urls = self.post_url_manager.get_urls()
        
        logger.info(f"Starting automation with {len(accounts)} accounts and {len(post_urls)} post URLs")
        
        # Print session summary at start
        self.session.print_session_summary(accounts, post_urls)
        
        # Execute phases
        self._execute_login_phase(accounts)
        self._execute_post_phase(accounts, post_urls)
        self._generate_final_reports(accounts, post_urls)
    
    def _execute_login_phase(self, accounts: List[Dict]) -> None:
        """Execute the login phase"""
        logger.info("🔐 STARTING LOGIN PHASE")
        self.login_processor.process_login_phase(accounts)
        logger.info("🔐 LOGIN PHASE COMPLETED")
    
    def _execute_post_phase(self, accounts: List[Dict], post_urls: List[str]) -> None:
        """Execute the post interaction phase"""
        logger.info("📝 STARTING POST INTERACTION PHASE")
        self.post_processor.process_post_phase(accounts, post_urls)
        logger.info("📝 POST INTERACTION PHASE COMPLETED")
    
    def _generate_final_reports(self, accounts: List[Dict], post_urls: List[str]) -> None:
        """Generate final reports and summaries"""
        self.report_generator.generate_final_statistics(self.session, accounts, post_urls)
        self.report_generator.display_final_summary(self.session, self.account_manager)


def run_enhanced_facebook_automation():
    """Main entry point for the enhanced Facebook automation"""
    # Display startup information
    ReportGenerator.display_startup_banner()
    
    # Create and run orchestrator
    orchestrator = FacebookAutomationOrchestrator()
    orchestrator.run_automation()


# Maintain backward compatibility
display_startup_banner = ReportGenerator.display_startup_banner
display_final_summary = ReportGenerator.display_final_summary

# Legacy function aliases for backward compatibility
def log_to_csv(account, action, status, details="", post_url="", duration=None):
    """Legacy function for backward compatibility"""
    csv_logger = CSVLogger(AutomationConfig.ACTIVITY_LOG)
    csv_logger.log_activity(account, action, status, details, post_url, duration)

def check_login_status(page):
    """Legacy function for backward compatibility"""
    return LoginStatusChecker.is_logged_in(page)

def get_profile_dir(account):
    """Legacy function for backward compatibility"""
    return BrowserManager.get_profile_dir(account)

def initialize_csv_log():
    """Legacy function for backward compatibility"""
    csv_logger = CSVLogger(AutomationConfig.ACTIVITY_LOG)