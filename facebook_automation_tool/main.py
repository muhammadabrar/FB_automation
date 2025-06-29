from logging_module import logger
from account_management import AccountManager
from session_management import SessionState
from facebook_automation import run_enhanced_facebook_automation, display_startup_banner, display_final_summary

def main():
    """
    Main entry point for the Enhanced Facebook Automation Tool.

    This function handles the overall workflow of the automation, including
    displaying the startup banner, running the automation, displaying the
    final summary, and handling any exceptions that may occur during
    execution.

    If the script is interrupted by the user (e.g., via Ctrl+C), it will
    display the final summary and exit gracefully.

    If an exception occurs during execution, it will be logged and the
    script will exit with a non-zero status code.

    Finally, a message will be printed to the console to indicate that the
    script has finished executing.
    """
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
