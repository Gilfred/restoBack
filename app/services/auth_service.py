from sqlalchemy.orm import Session, joinedload
from app.models.user import User
from app.models.account import Account
from app.models.session import Session as UserSession
from app.models.verification import Verification
from datetime import datetime, timedelta, timezone
import uuid
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from fastapi import Response

def get_user_by_id(db: Session, user_id: uuid.UUID):
    from app.models.restaurant_user import RestaurantUser
    from app.models.role import Role
    return db.query(User).options(
        joinedload(User.roles),
        joinedload(User.restaurant_user).joinedload(RestaurantUser.role).joinedload(Role.permissions)
    ).filter(User.id == user_id).first()

def get_or_create_user_google(db: Session, email: str, name: str, picture: str, provider_account_id: str):
    user = db.query(User).filter(User.email == email).first()
    
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
    from app.models.restaurant_user import RestaurantUser
    from app.models.role import Role
    return db.query(User).options(
        joinedload(User.roles),
        joinedload(User.restaurant_user).joinedload(RestaurantUser.role).joinedload(Role.permissions)
    ).filter(User.email == email).first()

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
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
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
    return db.query(UserSession).options(
        joinedload(UserSession.user).joinedload(User.roles)
    ).filter(
        UserSession.token == token,
        UserSession.expiresAt > datetime.now(timezone.utc)
    ).first()

def delete_session(db: Session, token: str):
    session = db.query(UserSession).filter(UserSession.token == token).first()
    if session:
        db.delete(session)
        db.commit()
    return True

def delete_all_user_sessions(db: Session, user_id: uuid.UUID):
    db.query(UserSession).filter(UserSession.userId == user_id).delete()
    db.commit()
    return True

def login_user(db: Session, user, response: Response):
    access_token = create_access_token(subject=user.id)

    # Delete existing sessions to ensure only one active session (optional, but good for logout logic)
    delete_all_user_sessions(db, user.id)
    # Keep session for backward compatibility and to support logout
    create_user_session(db, user_id=user.id)

    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=600,
        path="/"
    )

    return {"access_token": access_token, "token_type": "bearer"}

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
    verification = db.query(Verification).filter(
        Verification.value == token,
        Verification.expiresAt > datetime.now(timezone.utc)
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
