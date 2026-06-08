from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import engine
from app.models import User
from app.core.security import get_password_hash, pwd_context

def fix_password():
    with Session(engine) as session:
        user = session.execute(select(User).where(User.email == "admin@example.com")).scalars().first()
        if user:
            # identify() returns the name of the scheme if it's a valid hash, or None if it's not
            scheme = pwd_context.identify(user.password)
            if scheme:
                print(f"Password for {user.email} is already hashed (scheme: {scheme}).")
            else:
                # Not a valid hash, so we hash it
                print(f"Hashing password for {user.email}...")
                user.password = get_password_hash(user.password)
                session.commit()
                print("Password updated successfully.")
        else:
            print("Superadmin user not found.")

if __name__ == "__main__":
    fix_password()
