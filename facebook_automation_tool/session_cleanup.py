#!/usr/bin/env python3
"""
Session Cleanup Script for Facebook Automation Tool

This standalone script allows you to delete session data for specific account IDs.
It can remove account IDs from login attempts, successful logins, failed logins,
and processed posts tracking.

Usage:
    python session_cleanup.py --account-ids 61571930150364 61571919171009
    python session_cleanup.py --account-ids 61571930150364 --dry-run
    python session_cleanup.py --reset-all
    python session_cleanup.py --show-current
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Set

# Import session management
sys.path.append(os.path.dirname(__file__))
from session_management import SessionState

class SessionCleanupTool:
    """Tool for cleaning up session data for specific account IDs"""
    
    def __init__(self, session_file=None):
        self.session = SessionState(session_file)
        self.original_state = self.session.state.copy()
    
    def show_current_session(self) -> None:
        """Display current session state"""
        print("\n" + "="*80)
        print("📊 CURRENT SESSION STATE")
        print("="*80)
        
        state = self.session.state
        
        print(f"Session ID: {state.get('session_id', 'Unknown')}")
        print(f"Started: {state.get('start_time', 'Unknown')}")
        print(f"Last Updated: {state.get('last_update', 'Unknown')}")
        print(f"Current Account: {state.get('current_account', 'None')}")
        
        print(f"\n📋 LOGIN ATTEMPTS ({len(state.get('login_attempts', []))}):")
        for account_id in state.get('login_attempts', []):
            print(f"  {account_id}")
        
        print(f"\n✅ SUCCESSFUL LOGINS ({len(state.get('successful_logins', []))}):")
        for account_id in state.get('successful_logins', []):
            print(f"  {account_id}")
        
        print(f"\n❌ FAILED LOGINS ({len(state.get('failed_logins', []))}):")
        for account_id in state.get('failed_logins', []):
            print(f"  {account_id}")
        
        print(f"\n�� PROCESSED POSTS ({len(state.get('processed_posts', []))}):")
        for entry in state.get('processed_posts', []):
            account_id = entry.get('account_id', 'Unknown')
            post_url = entry.get('post_url', 'Unknown')
            print(f"  {account_id} -> {post_url}")
        
        print("="*80)
    
    def remove_account_ids(self, account_ids: List[str], dry_run: bool = False) -> Dict[str, int]:
        """Remove specific account IDs from all session tracking lists"""
        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
        
        removed_counts = {
            'login_attempts': 0,
            'successful_logins': 0,
            'failed_logins': 0,
            'processed_posts': 0,
            'current_account_reset': 0
        }
        
        account_ids_set = set(account_ids)
        
        # Remove from login_attempts
        original_attempts = self.session.state.get('login_attempts', [])
        self.session.state['login_attempts'] = [
            acc_id for acc_id in original_attempts 
            if acc_id not in account_ids_set
        ]
        removed_counts['login_attempts'] = len(original_attempts) - len(self.session.state['login_attempts'])
        
        # Remove from successful_logins
        original_successful = self.session.state.get('successful_logins', [])
        self.session.state['successful_logins'] = [
            acc_id for acc_id in original_successful 
            if acc_id not in account_ids_set
        ]
        removed_counts['successful_logins'] = len(original_successful) - len(self.session.state['successful_logins'])
        
        # Remove from failed_logins
        original_failed = self.session.state.get('failed_logins', [])
        self.session.state['failed_logins'] = [
            acc_id for acc_id in original_failed 
            if acc_id not in account_ids_set
        ]
        removed_counts['failed_logins'] = len(original_failed) - len(self.session.state['failed_logins'])
        
        # Remove from processed_posts
        original_posts = self.session.state.get('processed_posts', [])
        self.session.state['processed_posts'] = [
            entry for entry in original_posts 
            if entry.get('account_id') not in account_ids_set
        ]
        removed_counts['processed_posts'] = len(original_posts) - len(self.session.state['processed_posts'])
        
        # Reset current_account if it's in the list to be removed
        current_account = self.session.state.get('current_account')
        if current_account in account_ids_set:
            self.session.state['current_account'] = None
            removed_counts['current_account_reset'] = 1
        
        # Update last_update timestamp
        self.session.state['last_update'] = datetime.now().isoformat()
        
        if not dry_run:
            self.session.save_state()
            print("✅ Session data updated and saved")
        else:
            print("🔍 Dry run completed - no changes saved")
        
        return removed_counts
    
    def reset_all_session_data(self, dry_run: bool = False) -> None:
        """Reset all session data to initial state"""
        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
        
        original_state = self.session.state.copy()
        
        # Reset to initial state
        self.session.reset_session()
        
        if dry_run:
            print("🔍 Dry run completed - would reset all session data")
            # Restore original state for dry run
            self.session.state = original_state
        else:
            print("✅ All session data has been reset")
    
    def validate_account_ids(self, account_ids: List[str]) -> List[str]:
        """Validate and return valid account IDs"""
        valid_ids = []
        invalid_ids = []
        
        for account_id in account_ids:
            # Basic validation - should be numeric and reasonable length
            if account_id.isdigit() and 10 <= len(account_id) <= 20:
                valid_ids.append(account_id)
            else:
                invalid_ids.append(account_id)
        
        if invalid_ids:
            print(f"⚠️ Warning: Invalid account IDs detected: {invalid_ids}")
            print("   Account IDs should be numeric and 10-20 digits long")
        
        return valid_ids
    
    def print_removal_summary(self, account_ids: List[str], removed_counts: Dict[str, int]) -> None:
        """Print a summary of what was removed"""
        print("\n" + "="*60)
        print("🗑️ REMOVAL SUMMARY")
        print("="*60)
        
        print(f"Account IDs processed: {len(account_ids)}")
        print(f"  {', '.join(account_ids)}")
        
        print(f"\nRemovals:")
        print(f"  Login Attempts: {removed_counts['login_attempts']}")
        print(f"  Successful Logins: {removed_counts['successful_logins']}")
        print(f"  Failed Logins: {removed_counts['failed_logins']}")
        print(f"  Processed Posts: {removed_counts['processed_posts']}")
        print(f"  Current Account Reset: {removed_counts['current_account_reset']}")
        
        total_removals = sum(removed_counts.values())
        if total_removals > 0:
            print(f"\n✅ Total entries removed: {total_removals}")
        else:
            print(f"\nℹ️ No session data found for the specified account IDs")
        
        print("="*60)


def main():
    """Main function to handle command line arguments and execute cleanup"""
    parser = argparse.ArgumentParser(
        description="Session Cleanup Tool for Facebook Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python session_cleanup.py --account-ids 61571930150364 61571919171009
  python session_cleanup.py --account-ids 61571930150364 --dry-run
  python session_cleanup.py --reset-all
  python session_cleanup.py --show-current
        """
    )
    
    parser.add_argument(
        '--account-ids', 
        nargs='+', 
        help='Account IDs to remove from session data'
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what would be removed without making changes'
    )
    
    parser.add_argument(
        '--reset-all', 
        action='store_true',
        help='Reset all session data to initial state'
    )
    
    parser.add_argument(
        '--show-current', 
        action='store_true',
        help='Show current session state without making changes'
    )
    
    parser.add_argument(
        '--session-file',
        help='Path to custom session file (default: data/session_state.json)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.account_ids, args.reset_all, args.show_current]):
        parser.error("Please specify one of: --account-ids, --reset-all, or --show-current")
    
    if args.account_ids and args.reset_all:
        parser.error("Cannot use --account-ids and --reset-all together")
    
    # Initialize cleanup tool
    cleanup_tool = SessionCleanupTool(args.session_file)
    
    print("�� SESSION CLEANUP TOOL")
    print("="*50)
    
    try:
        if args.show_current:
            # Show current session state
            cleanup_tool.show_current_session()
            
        elif args.reset_all:
            # Reset all session data
            print("⚠️ WARNING: This will reset ALL session data!")
            if not args.dry_run:
                confirm = input("Are you sure? (yes/no): ").lower().strip()
                if confirm != 'yes':
                    print("❌ Operation cancelled")
                    return
            
            cleanup_tool.reset_all_session_data(dry_run=args.dry_run)
            
        elif args.account_ids:
            # Remove specific account IDs
            print(f"Processing {len(args.account_ids)} account IDs...")
            
            # Validate account IDs
            valid_ids = cleanup_tool.validate_account_ids(args.account_ids)
            
            if not valid_ids:
                print("❌ No valid account IDs provided")
                return
            
            # Show current state before removal
            if not args.dry_run:
                print("\n📊 Current session state before removal:")
                cleanup_tool.show_current_session()
            
            # Remove account IDs
            removed_counts = cleanup_tool.remove_account_ids(valid_ids, dry_run=args.dry_run)
            
            # Print summary
            cleanup_tool.print_removal_summary(valid_ids, removed_counts)
            
            # Show updated state after removal
            if not args.dry_run:
                print("\n📊 Updated session state after removal:")
                cleanup_tool.show_current_session()
        
        print("\n✅ Session cleanup completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error during session cleanup: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 