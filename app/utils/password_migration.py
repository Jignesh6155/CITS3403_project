from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    users = User.query.all()
    for user in users:
        # Only hash if not already hashed (very basic check)
        if not user.password.startswith('pbkdf2:'):
            user.password = generate_password_hash(user.password)
    db.session.commit()