from playwright.sync_api import sync_playwright
import os
import shutil
import time

def setup_chrome_profile():
    # Use a persistent profile directory
    profile_dir = os.path.expanduser("~/chrome_automation_profile")
    
    # Create the directory if it doesn't exist
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    
    return profile_dir

def main():
    profile_dir = setup_chrome_profile()
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            profile_dir,
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--window-size=1920,1080",
            ]
        )
        
        try:
            page = browser.new_page()
            page.goto("https://www.facebook.com/share/p/1ZQbJMQ2wW/")
            
            # Wait for the dialog to appear and locate the Like button
            like_button = page.locator('//div[contains(@role,"dialog")]//div[contains(@aria-label,"Like")][.//span[text()= "Like"]]')
            
            # Wait for the element to be visible
            like_button.wait_for(state="visible", timeout=10000)
            
            # Scroll the element into view
            like_button.scroll_into_view_if_needed()
            time.sleep(3)
            # Click the Like button
            # like_button.click()
            #Leave a comment
            comment_input = page.locator('//div[contains(@role,"dialog")]//div[contains(@aria-label,"Leave a comment")][.//span[text()= "Comment"]]')
            # comment_input.click()
            time.sleep(3)

            comment_input.type(" Nice post")
            time.sleep(3)

            comment_input.press("Enter")
            time.sleep(3)
            #Write a comment…
            comment_input = page.locator('//div[contains(@role,"dialog")]//div[contains(@aria-label,"Write a comment…")]')

            # comment_input.press("Enter")
 
            time.sleep(10)
            # Wait for user input before closing
            input("Press Enter to close...")
            
        finally:
            browser.close()
            # Note: We're not deleting the profile directory anymore
            # This will maintain login state between runs

if __name__ == "__main__":
    main()
