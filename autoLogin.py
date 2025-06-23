from playwright.sync_api import sync_playwright
import time
import os

# List of accounts
accounts = [
    "61571921690396",
    "61571930150364",
    "61571919171009",
    "61571926700760",
    "61571935220014",
    "61571935400102",
    "61571904081856",
    "61571927300754",
    "61571911581360",
    "61571926640255",
    "61571901531759",
    "61571891241243",
    "61571899521939",
    "61571886532846",
    "61571884342832",
    "61571889202565",
    "61571897212046",
    "61571890582335",
    "61571887491939",
    "61571856654284",
    "61571841623734",
    "61571835535370",
    "61571838595221",
    "61571868832726",
    "61571834185398",
    "61571835265382",
    "61571832385501",
    "61571855934235",
    "61571826655829",
    "61571825304596",
    "61571845704643",
    "61571817805970",
    "61571814776015",
    "61571803016163",
    "61571829474477",
    "61571828155366",
    "61571821736056",
    "61571827644849",
    "61571817415937",
    "61571800916896",
    "61571827645402",
    "61571806946416",
    "61571817565334",
    "61571819755859",
    "61571930630584",
    "61571875163120",
    "61571876063336",
    "61571871683347",
    "61571869733113",
    "61571806736607"
]

password = "kkk888"

def setup_chrome_profile():
    # Use a persistent profile directory
    profile_dir = os.path.expanduser("~/chrome_automation_profile")
    
    # Create the directory if it doesn't exist
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    
    return profile_dir

def login_to_facebook(page, username, password):
    try:
        # Navigate to Facebook
        page.goto('https://www.facebook.com')
        
        # Wait for the email/phone input field and fill it
        page.fill('input[name="email"]', username)
        
        # Fill in the password
        page.fill('input[name="pass"]', password)
        
        # Click the login button
        page.click('button[name="login"]')
        
        # Wait for navigation
        page.wait_for_load_state('networkidle')
        
        # Check if login was successful
        if "login" not in page.url:
            print(f"Successfully logged in as {username}")
            return True
        else:
            print(f"Failed to login as {username}")
            return False
            
    except Exception as e:
        print(f"Error logging in as {username}: {str(e)}")
        return False

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
            
            for account in accounts:
                print(f"\nAttempting to login with account: {account}")
                login_to_facebook(page, account, password)
                input("Press Enter to continue to the next account...")
                
        finally:
            browser.close()

if __name__ == "__main__":
    main()
