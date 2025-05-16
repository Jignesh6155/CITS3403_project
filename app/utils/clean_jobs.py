#!/usr/bin/env python3
"""
Script to safely clean job listings from the database.
This script will remove all ScrapedJob entries while preserving other data.

Usage:
    python clean_jobs.py

This utility is intended for maintenance purposes, allowing administrators to clear out all scraped job listings
without affecting other database records. It is safe to run multiple times and provides debug output for transparency.
"""

from app import app, db
from app.models import ScrapedJob
from datetime import datetime


def clean_jobs(debug=False):
    """
    Safely remove all scraped job listings from the database.

    Args:
        debug (bool): If True, prints detailed debug information during execution.

    Returns:
        int: The number of ScrapedJob entries deleted from the database.

    Raises:
        Exception: If an error occurs during the deletion process, it is caught and logged.

    This function ensures that only ScrapedJob entries are deleted, leaving other data intact.
    It uses the Flask application context to access the database session and commits changes atomically.
    """
    try:
        # Ensure all database operations occur within the Flask application context
        with app.app_context():
            # Get the total number of ScrapedJob entries before deletion
            total_jobs = ScrapedJob.query.count()
            
            if debug:
                print(f"[INFO] Found {total_jobs} job listings in the database")
            
            if total_jobs == 0:
                # No jobs to delete; exit early
                if debug:
                    print("[INFO] No job listings to clean")
                return 0
            
            # Proceed to delete all ScrapedJob entries
            if debug:
                print("[INFO] Starting deletion...")
            ScrapedJob.query.delete()
            
            # Commit the transaction to persist changes
            db.session.commit()
            
            # Verify that all jobs have been deleted
            remaining_jobs = ScrapedJob.query.count()
            if remaining_jobs == 0:
                if debug:
                    print(f"[SUCCESS] Successfully deleted {total_jobs} job listings")
                return total_jobs
            else:
                # Some jobs remain; partial deletion occurred
                if debug:
                    print(f"[WARNING] {remaining_jobs} jobs remain in the database")
                return total_jobs - remaining_jobs
                
    except Exception as e:
        # Log the error and rollback any uncommitted changes to maintain database integrity
        if debug:
            print(f"[ERROR] An error occurred while cleaning jobs: {str(e)}")
        db.session.rollback()
        return 0


def main():
    """
    Entry point for the cleaning script. Handles user interaction and error reporting.

    Returns:
        int: Exit code (0 for success, 1 for failure)

    This function provides a user-friendly interface for running the cleaning operation,
    including timestamps and summary output. It also handles fatal errors gracefully.
    """
    print(f"\n[INFO] Starting job cleanup at {datetime.now()}")
    print("-" * 50)
    
    try:
        # Run the cleaning operation with debug output enabled
        deleted_count = clean_jobs(debug=True)
        print("-" * 50)
        print(f"[COMPLETE] Cleanup finished at {datetime.now()}")
        print(f"[SUMMARY] Deleted {deleted_count} job listings")
        
    except Exception as e:
        # Catch any unexpected fatal errors and provide guidance
        print("\n[ERROR] Fatal error occurred:")
        print(str(e))
        print("\nPlease check your database connection and try again.")
        return 1
    
    return 0


if __name__ == "__main__":
    # Allow the script to be run directly from the command line
    import sys
    sys.exit(main()) 