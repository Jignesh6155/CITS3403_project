"""Add closing_date column to scraped_job table

This migration adds a closing_date column to store the actual closing date
calculated from the 'closing_in' text.
"""

from app import app, db
from datetime import datetime, timedelta
import pytz
import re

def upgrade():
    # Add the column
    with app.app_context():
        db.engine.execute('ALTER TABLE scraped_job ADD COLUMN closing_date DATETIME')
        
        # Update existing records
        from app.models import ScrapedJob
        perth_tz = pytz.timezone('Australia/Perth')
        
        for job in ScrapedJob.query.all():
            if job.closing_in:
                days_match = re.search(r'(\d+)\s*days?', job.closing_in.lower())
                if days_match:
                    days = int(days_match.group(1))
                    now = datetime.now(perth_tz)
                    job.closing_date = now + timedelta(days=days)
                    job.closing_in = f"Closing in {days} days"
        
        db.session.commit()

def downgrade():
    # Remove the column
    with app.app_context():
        db.engine.execute('ALTER TABLE scraped_job DROP COLUMN closing_date') 