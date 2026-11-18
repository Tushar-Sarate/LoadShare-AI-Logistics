from app.database import SessionLocal
from app.models.user import User
from app.security.password import hash_password

EMAIL = "admin@loadshare.com"
PASSWORD = "Admin@12345"

db = SessionLocal()

if not db.query(User).filter(User.email == EMAIL).first():
    db.add(
        User(
            full_name="Admin",
            email=EMAIL,
            hashed_password=hash_password(PASSWORD),
            role="admin"
        )
    )
    db.commit()
    print("Admin created")
else:
    print("Admin already exists")

db.close()