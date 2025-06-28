import logging
import os
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright
import msvcrt
import csv
from configuration import config
from logging_module import MAIN_LOG, logger
from post_url_management import PostURLManager
from account_management import ACCOUNTS_FILE, AccountManager
from session_management import SessionState

# Configuration
LOG_DIR = "logs"
SUCCESS_FILE = os.path.join(LOG_DIR, "successful_accounts.txt")
DISABLED_FILE = os.path.join(LOG_DIR, "disabled_accounts.txt")
ACTIVITY_LOG = os.path.join(LOG_DIR, "activity_log.csv")
# Initialize session state
session = SessionState()

class FacebookAutomationException(Exception):
    """Base exception for Facebook automation"""
    pass

class LoginFailedException(FacebookAutomationException):
    """Raised when login fails"""
    pass

class SecurityChallengeException(FacebookAutomationException):
    """Raised when security challenge is encountered"""
    pass

class PostInteractionException(FacebookAutomationException):
    """Raised when post interaction fails"""
    pass

def setup_secure_credentials():
    """Setup secure credential management"""
    # Method 1: Environment variables (RECOMMENDED)
    password = os.getenv('FB_PASSWORD')
    if not password:
        # Method 2: Secure input
        import getpass
        password = getpass.getpass("Enter Facebook password: ")

    return password

def human_like_delay(min_delay=2, max_delay=8):
    """Add human-like delays to avoid detection"""
    delay = random.uniform(min_delay, max_delay)
    logger.debug(f"Human-like delay: {delay:.2f} seconds")
    time.sleep(delay)

def random_user_agent():
    """Return random user agent to avoid detection"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
    return random.choice(user_agents)

def retry_with_backoff(func, max_retries=3, base_delay=2):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries}")
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} attempts failed. Final error: {str(e)}")
                raise e

            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.2f}s...")
            time.sleep(delay)

def handle_facebook_security_challenges(page, account):
    """Handle various Facebook security challenges"""
    try:
        current_url = page.url.lower()
        logger.info(f"Checking for security challenges on URL: {current_url}")

        # Check for different types of challenges
        if "checkpoint" in current_url:
            logger.warning("🔒 CHECKPOINT DETECTED - Manual intervention required")
            log_to_csv(account, "SECURITY_CHALLENGE", "CHECKPOINT", "Identity verification required", current_url)

            print("="*60)
            print("🔒 FACEBOOK CHECKPOINT DETECTED")
            print("Please complete the verification in the browser window.")
            print("This may include:")
            print("- Identity verification")
            print("- Phone number verification")
            print("- Photo identification")
            print("="*60)

            # Wait for user to complete checkpoint
            while "checkpoint" in page.url.lower():
                user_input = input("Type 'done' when verification is complete, or 'skip' to skip this account: ").strip().lower()
                if user_input == "skip":
                    raise SecurityChallengeException("User skipped checkpoint")
                elif user_input == "done":
                    logger.info("User reported checkpoint completion")
                    break
                time.sleep(2)

            return True

        elif "captcha" in current_url or page.locator('[role="img"][aria-label*="captcha" i]').is_visible(timeout=3000):
            logger.warning("🤖 CAPTCHA DETECTED - Manual solving required")
            log_to_csv(account, "SECURITY_CHALLENGE", "CAPTCHA", "CAPTCHA verification required", current_url)

            print("="*60)
            print("🤖 CAPTCHA DETECTED")
            print("Please solve the CAPTCHA in the browser window.")
            print("="*60)

            input("Press Enter after solving the CAPTCHA...")
            return True

        elif "two_factor" in current_url or "2fa" in current_url:
            logger.warning("📱 TWO-FACTOR AUTHENTICATION REQUIRED")
            log_to_csv(account, "SECURITY_CHALLENGE", "2FA", "Two-factor authentication required", current_url)

            print("="*60)
            print("📱 TWO-FACTOR AUTHENTICATION")
            print("Please enter your 2FA code in the browser window.")
            print("="*60)

            input("Press Enter after entering 2FA code...")
            return True

        return False
    except Exception as e:
        logger.error(f"Error handling security challenges: {str(e)}")
        return False

def get_user_continuation_choice(account, remaining_count):
    """Get user choice for continuation with enhanced options"""
    print("\n" + "="*60)
    print(f"📱 ACCOUNT: {account}")
    print(f"⏳ REMAINING ACCOUNTS: {remaining_count}")
    print("="*60)
    print("Options:")
    print("1. Continue to next account")
    print("2. Add new post URL and continue")
    print("3. Manage post URLs")
    print("4. Exit program")
    print("5. Reset session and restart")

    while True:
        choice = input("\nEnter your choice (1-5): ").strip()

        if choice in ['1', '2', '3', '4', '5']:
            return choice
        else:
            print("❌ Invalid choice. Please enter 1-5.")

def handle_completion_options(post_url_manager, session, account_manager):
    """Handle options when all accounts are processed"""
    print("\n" + "="*60)
    print("🎉 ALL ACCOUNTS PROCESSED!")
    print("="*60)

    accounts = account_manager.get_accounts()
    successful = len(session.state.get("successful_logins", []))
    failed = len(session.state.get("failed_logins", []))
    total = len(accounts)

    print(f"📊 SUMMARY:")
    print(f"  ✅ Successful Logins: {successful}/{total}")
    print(f"  ❌ Failed Logins: {failed}/{total}")
    print(f"  📈 Login Success Rate: {(successful/total*100):.1f}%" if total > 0 else "  📈 Login Success Rate: 0%")

    print("\nOptions:")
    print("1. Add new account and restart")
    print("2. Add new post URL and restart")
    print("3. Manage accounts")
    print("4. Manage post URLs")
    print("5. Exit program")

    while True:
        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == "1":
            new_account = input("Enter new account (username/email/phone): ").strip()
            if new_account and account_manager.add_account(new_account):
                print(f"✅ Added new account: {new_account}")
                session.reset_session()
                return "restart"
            else:
                print("❌ Invalid account or account already exists")

        elif choice == "2":
            new_url = input("Enter new post URL: ").strip()
            if new_url and post_url_manager.add_url(new_url):
                print(f"✅ Added new URL: {new_url}")
                session.reset_session()
                return "restart"
            else:
                print("❌ Invalid URL or URL already exists")

        elif choice == "3":
            if account_manager.interactive_account_management():
                session.reset_session()
                return "restart"
            else:
                return "exit"

        elif choice == "4":
            if post_url_manager.interactive_url_management():
                session.reset_session()
                return "restart"
            else:
                return "exit"

        elif choice == "5":
            return "exit"

        else:
            print("❌ Invalid choice. Please enter 1-5.")

def initialize_csv_log():
    """Initialize CSV log file with headers"""
    if not os.path.exists(ACTIVITY_LOG):
        with open(ACTIVITY_LOG, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Timestamp', 'Account', 'Action', 'Status', 'Details', 'Post_URL', 'Duration_Seconds'
            ])

def log_to_csv(account, action, status, details="", post_url="", duration=None):
    """Enhanced CSV logging with duration tracking"""
    try:
        with open(ACTIVITY_LOG, 'a', newline='', encoding='utf-8') as csvfile:
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

def enhanced_login_to_facebook(page, username, password, session):
    """Enhanced login function with all critical improvements"""
    start_time = datetime.now()

    def login_attempt():
        logger.info(f"=== ENHANCED LOGIN ATTEMPT FOR: {username} ===")

        # Navigate with random user agent
        page.goto('https://www.facebook.com')
        human_like_delay(1, 3)  # Initial page load delay

        # Check if already logged in
        if check_login_status(page):
            logger.info("Already logged in")
            return True

        # Handle security challenges first
        if handle_facebook_security_challenges(page, username):
            # Recheck login status after handling challenges
            human_like_delay(2, 5)
            if check_login_status(page):
                return True

        # Find and fill login form
        if not page.locator('input[name="email"]').is_visible(timeout=config.get('timeouts.element_wait', 10) * 1000):
            raise LoginFailedException("Login form not found")

        # Human-like typing
        page.fill('input[name="email"]', username)
        human_like_delay(0.5, 1.5)

        page.fill('input[name="pass"]', password)
        human_like_delay(0.5, 1.5)

        # Click login with slight delay
        page.click('button[name="login"]')

        # Wait for navigation with timeout
        page.wait_for_load_state('networkidle', timeout=config.get('timeouts.page_load', 30) * 1000)
        human_like_delay(2, 4)

        # Enhanced login verification with security challenge handling
        max_wait = config.get('timeouts.login_max_wait', 120)
        waited = 0
        check_interval = 3

        while waited < max_wait:
            # Handle any security challenges that appear during login
            if handle_facebook_security_challenges(page, username):
                human_like_delay(2, 5)

            # Check if successfully logged in
            if check_login_status(page):
                return True

            # Check for login errors
            if page.locator('div[role="alert"]').is_visible(timeout=1000):
                error_text = page.locator('div[role="alert"]').text_content()
                raise LoginFailedException(f"Login error: {error_text}")

            time.sleep(check_interval)
            waited += check_interval

        raise LoginFailedException(f"Login timeout after {max_wait} seconds")

    try:
        # Use retry mechanism for login
        success = retry_with_backoff(
            login_attempt,
            max_retries=config.get('retry.max_attempts', 3),
            base_delay=config.get('retry.base_delay', 2)
        )

        duration = (datetime.now() - start_time).total_seconds()

        if success:
            logger.info(f"✅ LOGIN SUCCESS in {duration:.2f}s")
            session.mark_login_attempt(username, True)
            log_to_csv(username, "LOGIN", "SUCCESS", "Login successful", "", duration)
            return True

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)
        logger.error(f"❌ LOGIN FAILED in {duration:.2f}s: {error_msg}")
        session.mark_login_attempt(username, False)
        log_to_csv(username, "LOGIN", "FAILED", error_msg, "", duration)
        return False

def enhanced_like_comment_post(page, post_url, account):
    """Enhanced post interaction with all improvements"""
    start_time = datetime.now()

    try:
        logger.info(f"=== ENHANCED POST INTERACTION FOR: {account} ===")
        logger.info(f"🎯 Target URL: {post_url}")

        # Navigate to post
        page.goto(post_url)
        human_like_delay(
            config.get('delays.page_load', 3),
            config.get('delays.page_load', 3) + 2
        )

        # Enhanced like functionality with retry
        def like_attempt():
            like_selectors = [
                '[aria-label="Like"][role="button"]',
                'div[role="button"]:has-text("Like")',
                '[data-testid="fb-ufi-likelink"]',
                'span:text-is("Like")'
            ]

            for selector in like_selectors:
                try:
                    if page.locator(selector).first.is_visible(timeout=3000):
                        page.locator(selector).first.scroll_into_view_if_needed()
                        human_like_delay(0.5, 1.5)
                        page.locator(selector).first.click()
                        logger.info("✅ Like successful")
                        return True
                except:
                    continue
            return False

        like_success = retry_with_backoff(like_attempt, max_retries=2)

        # Enhanced comment functionality with variations
        def comment_attempt():
            comment_text = random.choice(config.get('posts.comment_variations', ['Nice post!']))

            comment_selectors = [
                '[placeholder*="comment" i]',
                'div[contenteditable="true"]',
                '[aria-label*="comment" i]'
            ]

            for selector in comment_selectors:
                try:
                    if page.locator(selector).first.is_visible(timeout=3000):
                        page.locator(selector).first.scroll_into_view_if_needed()
                        human_like_delay(0.5, 1.5)
                        page.locator(selector).first.click()

                        # Human-like typing
                        for char in comment_text:
                            page.keyboard.type(char)
                            time.sleep(random.uniform(0.05, 0.15))

                        human_like_delay(0.5, 1.5)
                        page.keyboard.press("Enter")
                        logger.info(f"✅ Comment successful: '{comment_text}'")
                        return True
                except:
                    continue
            return False

        comment_success = retry_with_backoff(comment_attempt, max_retries=2)

        # Calculate results
        duration = (datetime.now() - start_time).total_seconds()

        if like_success or comment_success:
            actions = []
            if like_success:
                actions.append("liked")
                log_to_csv(account, "LIKE", "SUCCESS", "Like successful", post_url, duration)
            if comment_success:
                actions.append("commented")
                log_to_csv(account, "COMMENT", "SUCCESS", "Comment successful", post_url, duration)

            success_msg = f"Successfully {' and '.join(actions)} in {duration:.2f}s"
            logger.info(f"🎉 {success_msg}")
            log_to_csv(account, "POST_INTERACTION", "SUCCESS", success_msg, post_url, duration)
            session.mark_post_processed(account,post_url)
            return True
        else:
            error_msg = f"Failed all post interactions in {duration:.2f}s"
            logger.error(f"❌ {error_msg}")
            log_to_csv(account, "POST_INTERACTION", "FAILED", error_msg, post_url, duration)
            return False
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        error_msg = f"Post interaction error in {duration:.2f}s: {str(e)}"
        logger.error(f"💥 {error_msg}")
        log_to_csv(account, "POST_INTERACTION", "ERROR", error_msg, post_url, duration)
        return False

def check_login_status(page):
    """Check if user is logged in"""
    try:
        post_selectors = [
            'h3:has-text("Create a post")',
            '[aria-label="Create a post"]',
            'span:has-text("What\'s on your mind")',
            '[placeholder*="What\'s on your mind"]'
        ]

        for selector in post_selectors:
            if page.locator(selector).is_visible(timeout=3000):
                return True
        return False
    except:
        return False

def get_profile_dir(account):
    """Get unique profile directory for each account"""
    return os.path.expanduser(f"~/chrome_profile_{account}")

def display_startup_banner():
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

def display_final_summary(session, account_manager):
    """Display final summary of automation run"""
    accounts = account_manager.get_accounts()
    print("\n" + "="*80)
    print("📊 FINAL AUTOMATION SUMMARY")
    print("="*80)

    successful_logins = session.state.get("successful_logins", [])
    failed_logins = session.state.get("failed_logins", [])
    processed_posts = session.state.get("processed_posts", [])
    total_accounts = len(accounts)

    print(f"📈 OVERALL STATISTICS:")
    print(f"  Total Accounts: {total_accounts}")
    print(f"  ✅ Successful Logins: {len(successful_logins)}")
    print(f"  ❌ Failed Logins: {len(failed_logins)}")
    print(f"  📝 Accounts Completed Posts: {len(processed_posts)}")
    print(f"  📊 Login Success Rate: {(len(successful_logins)/total_accounts*100):.1f}%" if total_accounts > 0 else "  📊 Login Success Rate: 0%")

    if successful_logins:
        print(f"\n✅ SUCCESSFUL LOGINS ({len(successful_logins)}):")
        for acc in successful_logins:
            print(f"  • {acc}")

    if failed_logins:
        print(f"\n❌ FAILED LOGINS ({len(failed_logins)}):")
        for acc in failed_logins:
            print(f"  • {acc}")

    print(f"\n📁 LOG FILES:")
    print(f"  • Main Log: {MAIN_LOG}")
    print(f"  • Activity Log: {ACTIVITY_LOG}")
    print(f"  • Session State: session_state.json")
    print(f"  • Post URLs: post_urls.json")
    print(f"  • Accounts: {ACCOUNTS_FILE}")

    print("="*80)

def run_enhanced_facebook_automation():
    """Fixed main automation function with proper loop handling"""
    # Always load the existing session state
    session = SessionState()
    account_manager = AccountManager()
    post_url_manager = PostURLManager()

    accounts = account_manager.get_accounts()
    post_urls = post_url_manager.get_urls()

    logger.info(f"Starting automation with {len(accounts)} accounts and {len(post_urls)} post URLs")

    # PHASE 1: LOGIN ATTEMPTS
    accounts_to_login = session.get_accounts_for_login(accounts)
    logger.info(f"Accounts needing login: {len(accounts_to_login)}")
    
    for i, account in enumerate(accounts_to_login, 1):
        logger.info(f"🔐 LOGIN PHASE: Processing account {i}/{len(accounts_to_login)}: {account}")
        session.state["current_account"] = account
        session.save_state()

        profile_dir = get_profile_dir(account)
        password = setup_secure_credentials()
        browser = None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    headless=config.get('browser.headless', False),
                    viewport={'width': config.get('browser.viewport_width', 1280),
                             'height': config.get('browser.viewport_height', 720)},
                    user_agent=random_user_agent(),
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-popup-blocking',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )

                page = browser.new_page()

                if enhanced_login_to_facebook(page, account, password, session):
                    logger.info(f"✅ LOGIN SUCCESS for {account}")
                else:
                    logger.error(f"❌ LOGIN FAILED for {account}")

        except Exception as e:
            logger.error(f"💥 Error during login for {account}: {str(e)}")
            log_to_csv(account, "BROWSER", "ERROR", str(e))
        finally:
            if browser:
                try:
                    browser.close()
                except:
                    pass

        # Add delay between accounts to avoid rate limiting
        if i < len(accounts_to_login):
            delay = random.uniform(10, 30)  # 10-30 seconds between accounts
            logger.info(f"⏳ Waiting {delay:.1f}s before next account...")
            time.sleep(delay)

    # PHASE 2: POST INTERACTIONS
    post_tasks = session.get_accounts_for_posts(accounts, post_urls)
    logger.info(f"Post tasks to process: {len(post_tasks)}")
    
    for i, (account, post_url) in enumerate(post_tasks, 1):
        logger.info(f"📝 POST PHASE: Processing task {i}/{len(post_tasks)}: {account} -> {post_url}")
        session.state["current_account"] = account
        session.save_state()

        profile_dir = get_profile_dir(account)
        password = setup_secure_credentials()
        browser = None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    headless=config.get('browser.headless', False),
                    viewport={'width': config.get('browser.viewport_width', 1280),
                             'height': config.get('browser.viewport_height', 720)},
                    user_agent=random_user_agent(),
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-popup-blocking',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )

                page = browser.new_page()

                # Verify login status
                page.goto('https://www.facebook.com')
                human_like_delay(2, 4)
                
                if not check_login_status(page):
                    logger.warning(f"⚠️ Session lost for {account}, attempting re-login")
                    if not enhanced_login_to_facebook(page, account, password, session):
                        logger.error(f"❌ Re-login failed for {account}, skipping post: {post_url}")
                        continue  # Skip this post, move to next

                # Process the post
                if enhanced_like_comment_post(page, post_url, account):
                    logger.info(f"🎉 POST SUCCESS: {account} -> {post_url}")
                else:
                    logger.error(f"❌ POST FAILED: {account} -> {post_url}")

        except Exception as e:
            logger.error(f"💥 Error during post interaction for {account}: {str(e)}")
            log_to_csv(account, "BROWSER", "ERROR", str(e))
        finally:
            if browser:
                try:
                    browser.close()
                except Exception as e:
                    logger.error(f"Error closing browser: {str(e)}")

        # Add delay between post interactions
        if i < len(post_tasks):
            delay = random.uniform(5, 15)  # 5-15 seconds between posts
            logger.info(f"⏳ Waiting {delay:.1f}s before next post...")
            time.sleep(delay)

    # FINAL SUMMARY
    logger.info("🏁 AUTOMATION COMPLETED")
    logger.info(f"Total login attempts: {len(session.state.get('login_attempts', []))}")
    logger.info(f"Successful logins: {len(session.state.get('successful_logins', []))}")
    logger.info(f"Failed logins: {len(session.state.get('failed_logins', []))}")
    logger.info(f"Processed posts: {len(session.state.get('processed_posts', []))}")
    
    display_final_summary(session, account_manager)

# Alternative version with better error handling and continuation logic
def run_enhanced_facebook_automation_with_recovery():
    """Enhanced version with better error recovery and continuation"""
    session = SessionState()
    account_manager = AccountManager()
    post_url_manager = PostURLManager()

    while True:
        accounts = account_manager.get_accounts()
        post_urls = post_url_manager.get_urls()

        # Check if there's work to do
        accounts_to_login = session.get_accounts_for_login(accounts)
        post_tasks = session.get_accounts_for_posts(accounts, post_urls)

        if not accounts_to_login and not post_tasks:
            logger.info("✅ All accounts and posts have been processed!")
            break

        # Process login phase
        if accounts_to_login:
            logger.info(f"🔐 LOGIN PHASE: {len(accounts_to_login)} accounts pending")
            for account in accounts_to_login:
                try:
                    process_single_login(account, session)
                except KeyboardInterrupt:
                    logger.info("User interrupted login phase")
                    return
                except Exception as e:
                    logger.error(f"Critical error in login for {account}: {e}")
                    continue

        # Process post phase
        post_tasks = session.get_accounts_for_posts(accounts, post_urls)  # Refresh after logins
        if post_tasks:
            logger.info(f"📝 POST PHASE: {len(post_tasks)} tasks pending")
            for account, post_url in post_tasks:
                try:
                    process_single_post(account, post_url, session)
                except KeyboardInterrupt:
                    logger.info("User interrupted post phase")
                    return
                except Exception as e:
                    logger.error(f"Critical error in post processing for {account}: {e}")
                    continue

        # Check for completion
        remaining_logins = session.get_accounts_for_login(accounts)
        remaining_posts = session.get_accounts_for_posts(accounts, post_urls)
        
        if not remaining_logins and not remaining_posts:
            logger.info("🎉 All tasks completed!")
            break

def process_single_login(account, session):
    """Process login for a single account"""
    logger.info(f"🔐 Processing login for: {account}")
    session.state["current_account"] = account
    session.save_state()

    profile_dir = get_profile_dir(account)
    password = setup_secure_credentials()

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=config.get('browser.headless', False),
            viewport={'width': 1280, 'height': 720},
            user_agent=random_user_agent()
        )

        try:
            page = browser.new_page()
            success = enhanced_login_to_facebook(page, account, password, session)
            logger.info(f"Login result for {account}: {'SUCCESS' if success else 'FAILED'}")
            
        finally:
            browser.close()

    # Delay between accounts
    time.sleep(random.uniform(10, 30))

def process_single_post(account, post_url, session):
    """Process post interaction for a single account-post pair"""
    logger.info(f"📝 Processing post for {account}: {post_url}")
    session.state["current_account"] = account
    session.save_state()

    profile_dir = get_profile_dir(account)
    password = setup_secure_credentials()

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=config.get('browser.headless', False),
            viewport={'width': 1280, 'height': 720},
            user_agent=random_user_agent()
        )

        try:
            page = browser.new_page()
            
            # Check login status
            page.goto('https://www.facebook.com')
            if not check_login_status(page):
                logger.warning(f"Re-login required for {account}")
                if not enhanced_login_to_facebook(page, account, password, session):
                    logger.error(f"Re-login failed for {account}")
                    return

            # Process post
            success = enhanced_like_comment_post(page, post_url, account)
            logger.info(f"Post result for {account}: {'SUCCESS' if success else 'FAILED'}")
            
        finally:
            browser.close()

    # Delay between posts
    time.sleep(random.uniform(5, 15))