from app import app, db
from models import User, PrivateMessage, GroupChat, GroupMessage, GroupMember, Notification, ChatReaction, ChatPoll, UserStatus
from werkzeug.security import generate_password_hash
import os

def reset_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join('static', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            password=generate_password_hash("admin123"),
            is_admin=True,
            language="en",
            notifications_enabled=True,
            auto_translate=False
        )
        db.session.add(admin)
        
        # Create test user
        user = User(
            username="test",
            email="test@example.com",
            password=generate_password_hash("test123"),
            language="en",
            notifications_enabled=True,
            auto_translate=False
        )
        db.session.add(user)
        
        try:
            db.session.commit()
            print("Database reset complete!")
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    reset_db() 