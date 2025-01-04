from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_superadmin():
    with app.app_context():
        # Check if superadmin exists
        superadmin = User.query.filter_by(email='superadmin@chatapp.com').first()
        if not superadmin:
            superadmin = User(
                username='superadmin',
                email='superadmin@chatapp.com',
                password=generate_password_hash('SuperAdmin@2024'),
                is_admin=True,
                is_superadmin=True
            )
            db.session.add(superadmin)
            db.session.commit()
            print("Superadmin created successfully!")
            print("Email: superadmin@chatapp.com")
            print("Password: SuperAdmin@2024")
        else:
            print("Superadmin already exists!")

if __name__ == "__main__":
    create_superadmin() 