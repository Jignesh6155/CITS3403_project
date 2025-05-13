from app import app
from app.models import db
from sqlalchemy import text
from datetime import datetime

def add_friendship_columns():
    with app.app_context():
        # Add is_favorite column (ignore error if it already exists)
        try:
            db.session.execute(text('ALTER TABLE friendships ADD COLUMN is_favorite BOOLEAN DEFAULT FALSE'))
        except Exception as e:
            print('is_favorite column may already exist:', e)
        
        # Add last_interaction column as nullable
        try:
            db.session.execute(text('ALTER TABLE friendships ADD COLUMN last_interaction DATETIME'))
        except Exception as e:
            print('last_interaction column may already exist:', e)
        
        # Set last_interaction to now for all existing rows
        now = datetime.utcnow().isoformat(sep=' ')
        db.session.execute(text(f"UPDATE friendships SET last_interaction = '{now}' WHERE last_interaction IS NULL"))
        db.session.commit()

if __name__ == '__main__':
    add_friendship_columns() 