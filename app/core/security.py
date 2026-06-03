from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from joserfc import jwt
from joserfc.jwk import OctKey
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    header = {"alg": ALGORITHM}
    payload = {"exp": int(expire.timestamp()), "sub": str(subject)}
    key = OctKey.import_key(settings.SECRET_KEY)
    return jwt.encode(header, payload, key)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
