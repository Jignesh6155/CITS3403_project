#!/usr/bin/env python3
"""
Script to safely clean job listings from the database.
This script will remove all ScrapedJob entries while preserving other data.

run with: python clean_jobs.py
"""

from app import app, db
from app.models import ScrapedJob
from datetime import datetime

def clean_jobs(debug=False):
    """
    Safely remove all scraped job listings from the database.
    Returns the number of entries deleted.
    """
    try:
        # Create application context
        with app.app_context():
            # Get total count before deletion
            total_jobs = ScrapedJob.query.count()
            
            if debug:
                print(f"[INFO] Found {total_jobs} job listings in the database")
            
            if total_jobs == 0:
                if debug:
                    print("[INFO] No job listings to clean")
                return 0
            
            # Delete all scraped jobs
            if debug:
                print("[INFO] Starting deletion...")
            ScrapedJob.query.delete()
            
            # Commit the changes
            db.session.commit()
            
            # Verify deletion
            remaining_jobs = ScrapedJob.query.count()
            if remaining_jobs == 0:
                if debug:
                    print(f"[SUCCESS] Successfully deleted {total_jobs} job listings")
                return total_jobs
            else:
                if debug:
                    print(f"[WARNING] {remaining_jobs} jobs remain in the database")
                return total_jobs - remaining_jobs
                
    except Exception as e:
        if debug:
            print(f"[ERROR] An error occurred while cleaning jobs: {str(e)}")
        # Rollback any changes if there was an error
        db.session.rollback()
        return 0

def main():
    """
    Main function to run the cleaning script.
    """
    print(f"\n[INFO] Starting job cleanup at {datetime.now()}")
    print("-" * 50)
    
    try:
        deleted_count = clean_jobs(debug=True)
        print("-" * 50)
        print(f"[COMPLETE] Cleanup finished at {datetime.now()}")
        print(f"[SUMMARY] Deleted {deleted_count} job listings")
        
    except Exception as e:
        print("\n[ERROR] Fatal error occurred:")
        print(str(e))
        print("\nPlease check your database connection and try again.")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 