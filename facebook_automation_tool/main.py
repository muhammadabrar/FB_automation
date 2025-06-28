from configuration import AutomationConfig
from logging_module import setup_logging, logger
from account_management import AccountManager
from post_url_management import PostURLManager
from session_management import SessionState
from facebook_automation import run_enhanced_facebook_automation, display_startup_banner, display_final_summary

def main():
    try:
        display_startup_banner()
        run_enhanced_facebook_automation()
        display_final_summary(SessionState(), AccountManager())
    except KeyboardInterrupt:
        logger.warning("⚠️ Script interrupted by user")
        print("\n⚠️ Script interrupted by user. Session state saved.")
        display_final_summary(SessionState(), AccountManager())
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}")
        print(f"\n💥 Fatal error occurred: {str(e)}")
        display_final_summary(SessionState(), AccountManager())
    finally:
        logger.info("🔚 Script finished")
        print("\n👋 Thank you for using Enhanced Facebook Automation Tool!")

if __name__ == "__main__":
    main()
