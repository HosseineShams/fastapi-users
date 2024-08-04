import os
from sqlalchemy.orm import Session
from .models import User, Base, engine
from .utils import get_password_hash
from dotenv import load_dotenv

load_dotenv()

def init_db():
    Base.metadata.create_all(bind=engine)
    db = Session(bind=engine)
    if not db.query(User).filter(User.username == os.getenv("ADMIN_USERNAME")).first():
        admin_user = User(
            username=os.getenv("ADMIN_USERNAME"),
            email=os.getenv("ADMIN_EMAIL"),
            password=get_password_hash(os.getenv("ADMIN_PASSWORD")),
            role="Admin"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Admin user created: {admin_user.username}")
    else:
        print("Admin user already exists.")
    db.close()

if __name__ == "__main__":
    init_db()
