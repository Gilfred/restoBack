from sqlmodel import Session, select
from app.models.user import User
from app.models.account import Account
from app.models.session import Session as UserSession
from app.models.verification import Verification
from datetime import datetime, timedelta, timezone
import uuid
from app.core.security import get_password_hash, verify_password

def get_or_create_user_google(db: Session, email: str, name: str, picture: str, provider_account_id: str):
    user = db.exec(select(User).where(User.email == email)).first()
    
    if not user:
        user = User(
            email=email,
            name=name,
            image=picture,
            password="",  # No password for Google users
            emailVerified=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Check if Account already exists
    account = db.exec(
        select(Account).where(
            Account.provider == "google",
            Account.providerAccountId == provider_account_id
        )
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

def create_user(db: Session, user_data):
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        name=user_data.name,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.execute(select(User).where(User.email == email)).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_user_session(db: Session, user_id: uuid.UUID, expires_delta: timedelta = None):
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    token = str(uuid.uuid4())
    db_session = UserSession(
        userId=user_id,
        token=token,
        expiresAt=expire
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session_by_token(db: Session, token: str):
    return db.exec(
        select(UserSession).where(
            UserSession.token == token,
            UserSession.expiresAt > datetime.now(timezone.utc)
        )
    ).first()

def delete_session(db: Session, token: str):
    session = db.exec(select(UserSession).where(UserSession.token == token)).first()
    if session:
        db.delete(session)
        db.commit()
    return True

def create_password_reset_token(db: Session, email: str):
    token = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    
    verification = Verification(
        identifier=email,
        value=token,
        expiresAt=expire
    )
    db.add(verification)
    db.commit()
    return token

def reset_password(db: Session, token: str, new_password: str):
    verification = db.exec(
        select(Verification).where(
            Verification.value == token,
            Verification.expiresAt > datetime.now(timezone.utc)
        )
    ).first()
    
    if not verification:
        return False
    
    user = get_user_by_email(db, verification.identifier)
    if not user:
        return False
    
    user.password = get_password_hash(new_password)
    db.delete(verification)
    db.commit()
    return True
