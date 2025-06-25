import os
import json
from datetime import datetime
from logging_module import logger

class PostURLManager:
    """Manage post URLs and user interactions"""

    def __init__(self, config_file="post_urls.json"):
        self.config_file = config_file
        self.current_urls = []
        self.load_urls()

    def load_urls(self):
        """Load saved post URLs from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.current_urls = data.get('urls', [])
                logger.info(f"Loaded {len(self.current_urls)} saved post URLs")
            except Exception as e:
                logger.warning(f"Error loading post URLs: {e}")
                self.current_urls = []
        else:
            # Default post URL
            self.current_urls = ["https://www.facebook.com/share/p/1ZQbJMQ2wW/"]

    def save_urls(self):
        """Save current post URLs to file"""
        try:
            data = {
                'urls': self.current_urls,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.current_urls)} post URLs")
        except Exception as e:
            logger.error(f"Error saving post URLs: {e}")

    def add_url(self, url):
        """Add a new post URL"""
        if url and url not in self.current_urls:
            self.current_urls.append(url)
            self.save_urls()
            return True
        return False

    def remove_url(self, url):
        """Remove a post URL"""
        if url in self.current_urls:
            self.current_urls.remove(url)
            self.save_urls()
            return True
        return False

    def get_urls(self):
        """Get current post URLs"""
        return self.current_urls.copy()

    def clear_urls(self):
        """Clear all post URLs"""
        self.current_urls = []
        self.save_urls()

    def interactive_url_management(self):
        """Interactive post URL management"""
        while True:
            print("\n" + "="*60)
            print("📝 POST URL MANAGEMENT")
            print("="*60)

            if self.current_urls:
                print("Current Post URLs:")
                for i, url in enumerate(self.current_urls, 1):
                    print(f"  {i}. {url}")
            else:
                print("No post URLs configured.")

            print("\nOptions:")
            print("1. Add new post URL")
            print("2. Remove post URL")
            print("3. Clear all URLs")
            print("4. Continue with current URLs")
            print("5. Exit program")

            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == "1":
                url = input("Enter new post URL: ").strip()
                if url:
                    if self.add_url(url):
                        print(f"✅ Added: {url}")
                    else:
                        print("⚠️ URL already exists or invalid")
                else:
                    print("❌ Invalid URL")

            elif choice == "2":
                if not self.current_urls:
                    print("❌ No URLs to remove")
                    continue

                print("Select URL to remove:")
                for i, url in enumerate(self.current_urls, 1):
                    print(f"  {i}. {url}")

                try:
                    idx = int(input("Enter number: ").strip()) - 1
                    if 0 <= idx < len(self.current_urls):
                        removed_url = self.current_urls[idx]
                        self.remove_url(removed_url)
                        print(f"✅ Removed: {removed_url}")
                    else:
                        print("❌ Invalid selection")
                except ValueError:
                    print("❌ Invalid input")

            elif choice == "3":
                confirm = input("Clear all URLs? (yes/no): ").strip().lower()
                if confirm in ['yes', 'y']:
                    self.clear_urls()
                    print("✅ All URLs cleared")

            elif choice == "4":
                if not self.current_urls:
                    print("❌ No URLs configured. Please add at least one URL.")
                    continue
                print("✅ Continuing with current URLs")
                break

            elif choice == "5":
                print("👋 Exiting program")
                return False

            else:
                print("❌ Invalid choice")

        return True
