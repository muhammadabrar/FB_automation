import logging
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright
from configuration import config
from logging_module import logger
from utils import human_like_delay, retry_with_backoff

def wait_for_modal_stability(page, post_container, max_wait=5):
    """Wait for modal to be stable and fully loaded"""
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            if post_container.is_visible() and not page.locator('.loading, .spinner, [aria-label*="Loading"]').is_visible():
                return True
            time.sleep(0.5)
        except:
            time.sleep(0.5)
    return False

def disable_background_scroll(page):
    """Disable scrolling on background page"""
    try:
        page.evaluate("document.body.style.overflow = 'hidden'")
        page.evaluate("document.documentElement.style.overflow = 'hidden'")
    except:
        pass

def enhanced_like_comment_post(page, post_url, account):
    """Enhanced post interaction with modal focus and all improvements"""
    start_time = datetime.now()

    try:
        logger.info(f"=== ENHANCED POST INTERACTION FOR: {account} ===")
        logger.info(f"🎯 Target URL: {post_url}")

        page.goto(post_url)
        human_like_delay(config.get('delays.page_load', 3), config.get('delays.page_load', 3) + 2)

        disable_background_scroll(page)

        modal_selectors = [
            '[role="dialog"]',
            '[aria-modal="true"]',
            'div[data-pagelet="MediaViewerPhoto"]',
            'div[data-pagelet="MediaViewerVideo"]',
            '.uiLayer',
            '[data-testid="post_message"]'
        ]

        post_container = None
        for selector in modal_selectors:
            try:
                if page.locator(selector).first.is_visible(timeout=2000):
                    post_container = page.locator(selector).first
                    logger.info(f"✅ Found post container with selector: {selector}")
                    break
            except:
                continue

        if not post_container:
            post_container = page.locator('body')
            logger.info("⚠️ Using body as fallback container")
        else:
            if wait_for_modal_stability(page, post_container):
                logger.info("✅ Modal is stable and ready for interaction")
            else:
                logger.warning("⚠️ Modal may still be loading, proceeding anyway")

        def like_attempt():
            like_selectors = [
                '[role="dialog"] [aria-label="Like"][role="button"]',
                '[aria-modal="true"] [aria-label="Like"][role="button"]',
                '[aria-label="Like"][role="button"]',
                'div[role="button"]:has-text("Like")',
                '[data-testid="fb-ufi-likelink"]',
                'span:text-is("Like")',
                '[aria-label*="like" i][role="button"]',
                'div[role="button"] span:text-matches("Like", "i")'
            ]

            for selector in like_selectors:
                try:
                    like_element = post_container.locator(selector).first
                    if like_element.is_visible(timeout=1000):
                        like_element.scroll_into_view_if_needed()
                        human_like_delay(0.5, 1.5)

                        if like_element.is_visible():
                            like_element.click(force=True)
                            human_like_delay(0.3, 0.7)
                            logger.info(f"✅ Like successful with selector: {selector}")
                            return True
                except Exception as e:
                    logger.debug(f"Like attempt failed for {selector}: {str(e)}")
                    continue

            try:
                like_fallback = post_container.locator('text="Like"').first
                if like_fallback.is_visible(timeout=1000):
                    like_fallback.click(force=True)
                    logger.info("✅ Like successful with fallback method")
                    return True
            except:
                pass

            return False

        like_success = retry_with_backoff(like_attempt, max_retries=3)

        def comment_attempt():
            comment_text = random.choice(config.get('posts.comment_variations', ['Nice post!']))

            comment_selectors = [
                '[role="dialog"] [placeholder*="comment" i]',
                '[aria-modal="true"] [placeholder*="comment" i]',
                '[role="dialog"] div[contenteditable="true"]',
                '[aria-modal="true"] div[contenteditable="true"]',
                '[placeholder*="comment" i]',
                'div[contenteditable="true"]',
                '[aria-label*="comment" i]',
                'textarea[placeholder*="comment" i]',
                '[data-testid*="comment"]',
                '.UFIAddComment textarea',
                '.UFIAddComment div[contenteditable="true"]'
            ]

            for selector in comment_selectors:
                try:
                    comment_element = post_container.locator(selector).first
                    if comment_element.is_visible(timeout=2000):
                        comment_element.scroll_into_view_if_needed()
                        human_like_delay(0.5, 1.5)

                        if comment_element.is_visible():
                            comment_element.click(force=True)
                            human_like_delay(0.3, 0.7)

                            comment_element.fill("")
                            human_like_delay(0.2, 0.5)

                            for char in comment_text:
                                comment_element.type(char)
                                time.sleep(random.uniform(0.05, 0.15))

                            human_like_delay(0.5, 1.5)

                            try:
                                comment_element.press("Enter")
                            except:
                                submit_selectors = [
                                    'button:has-text("Post")',
                                    '[aria-label*="Post" i]',
                                    '[data-testid*="comment-submit"]'
                                ]
                                for submit_selector in submit_selectors:
                                    try:
                                        submit_btn = post_container.locator(submit_selector).first
                                        if submit_btn.is_visible(timeout=1000):
                                            submit_btn.click(force=True)
                                            break
                                    except:
                                        continue

                            human_like_delay(1, 2)
                            logger.info(f"✅ Comment successful: '{comment_text}' with selector: {selector}")
                            return True
                except Exception as e:
                    logger.debug(f"Comment attempt failed for {selector}: {str(e)}")
                    continue
            return False

        comment_success = retry_with_backoff(comment_attempt, max_retries=3)

        duration = (datetime.now() - start_time).total_seconds()

        if like_success or comment_success:
            actions = []
            if like_success:
                actions.append("liked")
            if comment_success:
                actions.append("commented")

            success_msg = f"Successfully {' and '.join(actions)} in {duration:.2f}s"
            logger.info(f"🎉 {success_msg}")
            return True
        else:
            error_msg = f"Failed all post interactions in {duration:.2f}s"
            logger.error(f"❌ {error_msg}")
            return False

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        error_msg = f"Post interaction error in {duration:.2f}s: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return False
