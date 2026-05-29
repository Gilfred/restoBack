from sqlalchemy.orm import Session
from app.models.user import User
from app.models.account import Account
from datetime import datetime

def get_or_create_user_google(db: Session, email: str, name: str, picture: str, provider_account_id: str):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            email=email,
            name=name,
            image=picture,
            password="",  # No password for Google users
            emailVerified=datetime.now()
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Check if Account already exists
    account = db.query(Account).filter(
        Account.provider == "google",
        Account.providerAccountId == provider_account_id
    ).first()

    if not account:
        account = Account(
            provider="google",
            providerAccountId=provider_account_id,
            userId=user.id
        )
        db.add(account)
        db.commit()

    return user
