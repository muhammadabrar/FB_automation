import time
from datetime import datetime
from typing import Optional
from configuration import config
from logging_module import logger
from exceptions import LoginFailedException, SecurityChallengeException
from utils import human_like_delay, retry_with_backoff

def handle_facebook_security_challenges(page, account, from_post: bool = False):
    """Handle various Facebook security challenges"""
    try:
        current_url = page.url.lower()
        logger.debug(f"Checking for security challenges on URL: {current_url}")

        # --- Checkpoint ---
        if "checkpoint" in current_url:
            if from_post:
                logger.info(f"🔒 CHECKPOINT detected for {account} during post-processing. Marking login as failed.")
                return False # Indicate failure to the login process
            else:
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
                return True # Indicate challenge was handled (manually)

        # --- CAPTCHA ---
        elif "captcha" in current_url or page.locator('[role="img"][aria-label*="captcha" i]').is_visible(timeout=3000):
            if from_post:
                logger.info(f"🤖 CAPTCHA detected for {account} during post-processing. Marking login as failed.")
                return False # Indicate failure
            else:
                logger.warning("🤖 CAPTCHA DETECTED - Manual solving required")
                print("="*60)
                print("🤖 CAPTCHA DETECTED")
                print("Please solve the CAPTCHA in the browser window.")
                print("="*60)
                input("Press Enter after solving the CAPTCHA...")
                return True # Indicate challenge was handled (manually)

        # --- Two-Factor Authentication ---
        elif "two_factor" in current_url or "2fa" in current_url:
            if from_post:
                logger.info(f"📱 2FA required for {account} during post-processing. Marking login as failed.")
                return False # Indicate failure
            else:
                logger.warning("📱 TWO-FACTOR AUTHENTICATION REQUIRED")
                print("="*60)
                print("📱 TWO-FACTOR AUTHENTICATION")
                print("Please enter your 2FA code in the browser window.")
                print("="*60)
                input("Press Enter after entering 2FA code...")
                return True # Indicate challenge was handled (manually)

        # --- No recognized challenge found ---
        return False
    except Exception as e:
        logger.error(f"Error handling security challenges for {account}: {str(e)}")
        # Even if there's an error *checking* for challenges, if we are in post-processing,
        # we should likely fail the login attempt rather than risk getting stuck.
        if from_post:
             logger.info(f"Error during challenge check for {account} in post-processing. Marking login as failed.")
             return False
        return False # Let the main login loop decide what to do if not from_post

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

def enhanced_login_to_facebook(page, username, password, session, from_post: bool = False):
    """Enhanced login function with all critical improvements"""
    start_time = datetime.now()

    def login_attempt():
        logger.info(f"=== ENHANCED LOGIN ATTEMPT FOR: {username} (from_post: {from_post}) ===")

        page.goto('https://www.facebook.com')
        human_like_delay(1, 3)

        if check_login_status(page):
            logger.info("Already logged in")
            return True

        # Pass the from_post flag to the challenge handler
        # If from_post is True, handle_facebook_security_challenges will return False
        # if a challenge is detected, causing the login loop to continue or fail.
        challenge_handled_or_detected = handle_facebook_security_challenges(page, username, from_post=from_post)

        if from_post and challenge_handled_or_detected:
            # If from post-processing AND a challenge was detected (meaning login will fail),
            # mark it as failed immediately and exit this attempt.
            logger.info(f"Challenge detected for {username} during post-processing attempt. Marking as failed.")
            session.mark_login_attempt(username, False)
            # Raise an exception or return False to stop this login attempt
            raise LoginFailedException("Security challenge encountered during post-processing.")
            # OR: return False

        elif not from_post and challenge_handled_or_detected:
             # If challenge was handled interactively (and we are NOT from_post),
             # proceed to check login status after a delay.
            human_like_delay(2, 5)
            if check_login_status(page):
                return True
        
        # --- Check for login form ---
        # Use a try-except block in case the element is not found within timeout
        try:
            page.wait_for_selector('input[name="email"]', timeout=config.get('timeouts.element_wait', 10) * 1000)
        except:
             # If form not found *and* we are from_post, treat as failure immediately
             if from_post:
                 logger.info("Login form not found during post-processing, marking as failed.")
                 raise LoginFailedException("Login form not found during post-processing")
             else:
                 raise LoginFailedException("Login form not found")


        page.fill('input[name="email"]', username)
        human_like_delay(0.5, 1.5)

        page.fill('input[name="pass"]', password)
        human_like_delay(0.5, 1.5)

        page.click('button[name="login"]')
        # Use networkidle cautiously, domcontentloaded might be faster sometimes
        page.wait_for_load_state('networkidle', timeout=config.get('timeouts.page_load', 30) * 1000)
        human_like_delay(2, 4)

        max_wait = config.get('timeouts.login_max_wait', 120)
        waited = 0
        check_interval = 3

        while waited < max_wait:
            # Check for challenges again after login click
            # Pass from_post flag
            if handle_facebook_security_challenges(page, username, from_post=from_post):
                # If challenge was handled (and we are NOT from_post), wait and check
                if not from_post:
                    human_like_delay(2, 5)
                # If from_post, we already decided it's a failure inside handle_facebook_security_challenges

            if check_login_status(page):
                return True

            # Check for login errors
            try:
                error_locator = page.locator('div[role="alert"]')
                if error_locator.is_visible(timeout=1000):
                    error_text = error_locator.text_content().strip()
                    raise LoginFailedException(f"Login error: {error_text}")
            except Exception as e:
                # If checking for error fails, it's probably not visible, continue loop
                if "Timeout" not in str(e):
                    logger.debug(f"Error checking for login alert: {e}")

            time.sleep(check_interval)
            waited += check_interval

        # If we reach here, it's a timeout
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
        else:
            # This case might not be reached if exceptions are always raised on failure
            # but good practice to handle.
            logger.error(f"❌ LOGIN FAILED (no exception raised) in {duration:.2f}s")
            session.mark_login_attempt(username, False)
            return False

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)
        logger.error(f"❌ LOGIN FAILED in {duration:.2f}s: {error_msg}")
        session.mark_login_attempt(username, False)
        # Return False to indicate failure to the caller
        return False
