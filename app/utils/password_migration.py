from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash

"""
Script to migrate user passwords to a secure hashed format.

This script iterates through all users in the database and ensures their passwords are securely hashed
using Werkzeug's password hashing utilities. It only hashes passwords that are not already hashed (as indicated
by the 'pbkdf2:' prefix), preventing double-hashing. This is intended for one-time migrations or upgrades
of legacy plaintext password storage to a secure format. This was kept in case of future migrations.

Usage:
    python password_migration.py
"""

app = create_app()
with app.app_context():
    # Retrieve all user records from the database
    users = User.query.all()
    for user in users:
        # Only hash the password if it is not already hashed.
        # The check is based on the standard prefix used by Werkzeug's PBKDF2 hashes.
        if not user.password.startswith('pbkdf2:'):
            user.password = generate_password_hash(user.password)
    # Commit all changes to the database in a single transaction
    db.session.commit()