from sqlalchemy.orm import Session, joinedload
from app.models.user import User
from app.models.account import Account
from app.models.session import Session as UserSession
from app.models.verification import Verification
from datetime import datetime, timedelta, timezone
import uuid
import secrets
import hashlib
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from fastapi import Response, HTTPException, status

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

def hash_refresh_token(token: str) -> str:
    """Generate SHA-256 hash of refresh token for safe storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def generate_refresh_token() -> str:
    """Generate a cryptographically secure random refresh token."""
    return secrets.token_urlsafe(48)

def create_user_session(
    db: Session,
    user_id: uuid.UUID,
    expires_delta: timedelta = None,
    raw_refresh_token: str = None
):
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        # Expiration absolue de la session (7 jours par défaut)
        expire = now + timedelta(days=settings.SESSION_ABSOLUTE_EXPIRE_DAYS)

    token = str(uuid.uuid4())
    refresh_hash = hash_refresh_token(raw_refresh_token) if raw_refresh_token else None

    db_session = UserSession(
        userId=user_id,
        token=token,
        expiresAt=expire,
        lastActivity=now,
        isRevoked=False,
        refreshTokenHash=refresh_hash
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
        UserSession.isRevoked == False,
        (UserSession.expiresAt == None) | (UserSession.expiresAt > datetime.now(timezone.utc))
    ).first()

def get_session_by_id(db: Session, session_id: uuid.UUID):
    return db.query(UserSession).options(
        joinedload(UserSession.user).joinedload(User.roles)
    ).filter(
        UserSession.id == session_id
    ).first()

def is_session_inactive(session: UserSession, now: datetime = None) -> bool:
    """
    Vérifie si la session a dépassé la durée maximale d'inactivité
    basée sur session.lastActivity et SESSION_INACTIVITY_TIMEOUT_MINUTES.
    """
    if not session or not session.lastActivity:
        return True
    if now is None:
        now = datetime.now(timezone.utc)

    last_act = session.lastActivity
    # Gérer la timezone si nécessaire
    if last_act.tzinfo is None:
        last_act = last_act.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    inactivity_limit = timedelta(minutes=settings.SESSION_INACTIVITY_TIMEOUT_MINUTES)
    return (now - last_act) > inactivity_limit

def is_session_expired(session: UserSession, now: datetime = None) -> bool:
    """
    Vérifie si la session est révoquée, a dépassé son expiration absolue
    ou si elle a expiré par inactivité.
    """
    if not session or session.isRevoked:
        return True
    if now is None:
        now = datetime.now(timezone.utc)

    # Expiration absolue
    if session.expiresAt is not None:
        exp = session.expiresAt
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        if now > exp:
            return True

    # Expiration par inactivité
    return is_session_inactive(session, now)

def update_session_activity(db: Session, session: UserSession, request_time: datetime = None):
    """
    Met à jour la dernière activité de la session si le délai minimal (ex: 60s)
    est écoulé depuis la dernière écriture en base, afin de limiter la charge SQL.
    """
    if not session or session.isRevoked:
        return

    if request_time is None:
        request_time = datetime.now(timezone.utc)

    last_act = session.lastActivity
    if last_act is not None:
        if last_act.tzinfo is None:
            last_act = last_act.replace(tzinfo=timezone.utc)
        if request_time.tzinfo is None:
            request_time = request_time.replace(tzinfo=timezone.utc)

        elapsed = (request_time - last_act).total_seconds()
        if elapsed < settings.SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS:
            return

    session.lastActivity = request_time
    db.commit()

def delete_session(db: Session, token: str):
    session = db.query(UserSession).filter(UserSession.token == token).first()
    if session:
        session.isRevoked = True
        db.delete(session)
        db.commit()
    return True

def revoke_session_by_id(db: Session, session_id: uuid.UUID):
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session:
        session.isRevoked = True
        db.commit()
    return True

def delete_all_user_sessions(db: Session, user_id: uuid.UUID):
    db.query(UserSession).filter(UserSession.userId == user_id).delete()
    db.commit()
    return True

def login_user(db: Session, user, response: Response):
    # Génération du refresh token cryptographique
    raw_refresh_token = generate_refresh_token()

    # Création de la session en base
    # (Remarque: suppression des sessions antérieures ou conservation multi-device)
    # Pour respecter la compatibilité existante :
    delete_all_user_sessions(db, user.id)
    session = create_user_session(db, user_id=user.id, raw_refresh_token=raw_refresh_token)

    # JWT contenant l'ID utilisateur et l'ID de session (sid)
    access_token = create_access_token(subject=user.id, sid=session.id)

    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    # Cookie sécurisé HttpOnly pour le refresh token
    refresh_max_age = settings.SESSION_ABSOLUTE_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=refresh_max_age,
        path="/"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": raw_refresh_token
    }

def refresh_user_token(db: Session, refresh_token: str, response: Response = None):
    """
    Renouvelle l'access token à partir d'un refresh token valide.
    Condition impérative :
    - La session ne doit pas être révoquée ni expirée.
    - La session NE DOIT PAS être inactive depuis > 30 minutes.
    - LE REFRESH TOKEN NE MET JAMAIS À JOUR `lastActivity`.
    - Rotation du refresh token : l'ancien est invalidé, un nouveau est généré.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_hash = hash_refresh_token(refresh_token)
    session = db.query(UserSession).options(
        joinedload(UserSession.user).joinedload(User.roles)
    ).filter(UserSession.refreshTokenHash == token_hash).first()

    if not session:
        # Risque potentiel de réutilisation ou token invalide
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session introuvable ou jeton invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if session.isRevoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session révoquée",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.now(timezone.utc)

    # 1. Vérification de l'expiration absolue
    if session.expiresAt is not None:
        exp = session.expiresAt
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now > exp:
            session.isRevoked = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expirée",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 2. Vérification stricte de l'inactivité :
    # Si plus de 30 minutes d'inactivité réelle, refuser le renouvellement !
    if is_session_inactive(session, now):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée pour inactivité",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Rotation du refresh token
    new_raw_refresh_token = generate_refresh_token()
    session.refreshTokenHash = hash_refresh_token(new_raw_refresh_token)
    # ATTENTION : on ne modifie PAS session.lastActivity ici !
    db.commit()
    db.refresh(session)

    # 4. Génération du nouvel access token
    new_access_token = create_access_token(subject=session.userId, sid=session.id)

    if response:
        response.set_cookie(
            key="session_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/"
        )
        refresh_max_age = settings.SESSION_ABSOLUTE_EXPIRE_DAYS * 24 * 60 * 60
        response.set_cookie(
            key="refresh_token",
            value=new_raw_refresh_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=refresh_max_age,
            path="/"
        )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "refresh_token": new_raw_refresh_token
    }

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
