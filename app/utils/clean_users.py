#!/usr/bin/env python3
"""
Script to safely clean all users and associated data from the database.
This script will remove all User entries, cascading deletes to job applications, searches, scraped jobs, resume analyses, friendships, friend requests, notifications, and shared applications.

Usage:
    python clean_users.py

This utility is intended for maintenance purposes, allowing administrators to clear out all user-related data.
It is safe to run multiple times and provides debug output for transparency.
"""

from app import create_app, db
from app.models import User
from datetime import datetime

def clean_users(debug=False):
    """
    Safely remove all users and associated data from the database.

    Args:
        debug (bool): If True, prints detailed debug information during execution.

    Returns:
        int: The number of User entries deleted from the database.

    Raises:
        Exception: If an error occurs during the deletion process, it is caught and logged.

    This function ensures that all User entries and their related data are deleted.
    It uses the Flask application context to access the database session and commits changes atomically.
    """
    try:
        with create_app().app_context():
            total_users = User.query.count()
            if debug:
                print(f"[INFO] Found {total_users} users in the database")
            if total_users == 0:
                if debug:
                    print("[INFO] No users to clean")
                return 0
            if debug:
                print("[INFO] Starting deletion of all users and associated data...")
            User.query.delete()
            db.session.commit()
            remaining_users = User.query.count()
            if remaining_users == 0:
                if debug:
                    print(f"[SUCCESS] Successfully deleted {total_users} users and all associated data")
                return total_users
            else:
                if debug:
                    print(f"[WARNING] {remaining_users} users remain in the database")
                return total_users - remaining_users
    except Exception as e:
        if debug:
            print(f"[ERROR] An error occurred while cleaning users: {str(e)}")
        db.session.rollback()
        return 0

def main():
    print(f"\n[INFO] Starting user cleanup at {datetime.now()}")
    print("-" * 50)
    try:
        deleted_count = clean_users(debug=True)
        print("-" * 50)
        print(f"[COMPLETE] Cleanup finished at {datetime.now()}")
        print(f"[SUMMARY] Deleted {deleted_count} users and all associated data")
    except Exception as e:
        print("\n[ERROR] Fatal error occurred:")
        print(str(e))
        print("\nPlease check your database connection and try again.")
        return 1
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 