import time
import random
from configuration import config

def human_like_delay(min_delay=2, max_delay=8):
    """Add human-like delays to avoid detection"""
    delay = random.uniform(min_delay, max_delay)
    print(f"Human-like delay: {delay:.2f} seconds")
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
            print(f"Attempt {attempt + 1}/{max_retries}")
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"All {max_retries} attempts failed. Final error: {str(e)}")
                raise e

            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
            print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.2f}s...")
            time.sleep(delay)
