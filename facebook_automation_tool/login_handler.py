import time
from datetime import datetime
from configuration import config
from logging_module import logger
from exceptions import LoginFailedException, SecurityChallengeException
from utils import human_like_delay, retry_with_backoff

def handle_facebook_security_challenges(page, account):
    """Handle various Facebook security challenges"""
    try:
        current_url = page.url.lower()
        logger.info(f"Checking for security challenges on URL: {current_url}")

        if "checkpoint" in current_url:
            logger.warning("🔒 CHECKPOINT DETECTED - Manual intervention required")
            print("="*60)
            print("🔒 FACEBOOK CHECKPOINT DETECTED")
            print("Please complete the verification in the browser window.")
            print("="*60)

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
            print("="*60)
            print("🤖 CAPTCHA DETECTED")
            print("Please solve the CAPTCHA in the browser window.")
            print("="*60)
            input("Press Enter after solving the CAPTCHA...")
            return True

        elif "two_factor" in current_url or "2fa" in current_url:
            logger.warning("📱 TWO-FACTOR AUTHENTICATION REQUIRED")
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

def enhanced_login_to_facebook(page, username, password, session):
    """Enhanced login function with all critical improvements"""
    start_time = datetime.now()

    def login_attempt():
        logger.info(f"=== ENHANCED LOGIN ATTEMPT FOR: {username} ===")

        page.goto('https://www.facebook.com')
        human_like_delay(1, 3)

        if check_login_status(page):
            logger.info("Already logged in")
            return True

        if handle_facebook_security_challenges(page, username):
            human_like_delay(2, 5)
            if check_login_status(page):
                return True

        if not page.locator('input[name="email"]').is_visible(timeout=config.get('timeouts.element_wait', 10) * 1000):
            raise LoginFailedException("Login form not found")

        page.fill('input[name="email"]', username)
        human_like_delay(0.5, 1.5)

        page.fill('input[name="pass"]', password)
        human_like_delay(0.5, 1.5)

        page.click('button[name="login"]')
        page.wait_for_load_state('networkidle', timeout=config.get('timeouts.page_load', 30) * 1000)
        human_like_delay(2, 4)

        max_wait = config.get('timeouts.login_max_wait', 120)
        waited = 0
        check_interval = 3

        while waited < max_wait:
            if handle_facebook_security_challenges(page, username):
                human_like_delay(2, 5)

            if check_login_status(page):
                return True

            if page.locator('div[role="alert"]').is_visible(timeout=1000):
                error_text = page.locator('div[role="alert"]').text_content()
                raise LoginFailedException(f"Login error: {error_text}")

            time.sleep(check_interval)
            waited += check_interval

        raise LoginFailedException(f"Login timeout after {max_wait} seconds")

    try:
        success = retry_with_backoff(
            login_attempt,
            max_retries=config.get('retry.max_attempts', 3),
            base_delay=config.get('retry.base_delay', 2)
        )

        duration = (datetime.now() - start_time).total_seconds()

        if success:
            logger.info(f"✅ LOGIN SUCCESS in {duration:.2f}s")
            session.mark_login_attempt(username, True)
            return True

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)
        logger.error(f"❌ LOGIN FAILED in {duration:.2f}s: {error_msg}")
        session.mark_login_attempt(username, False)
        return False
