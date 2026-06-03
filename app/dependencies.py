from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from joserfc import jwt
from joserfc.jwk import OctKey
from joserfc.errors import JoseError
from sqlalchemy.orm import Session
from app.database import get_session
from app.core.config import settings
from app.core.security import ALGORITHM
from app.services import auth_service
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

def get_current_user(
    request: Request,
    db: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    # Try to get token from header (via oauth2_scheme) or cookie
    if not token:
        token = request.cookies.get("session_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        key = OctKey.import_key(settings.SECRET_KEY)
        token_obj = jwt.decode(token, key, algorithms=[ALGORITHM])
        claims = token_obj.claims
        user_id: str = claims.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JoseError:
        # Fallback to session token check for backward compatibility (if needed)
        # Or just raise unauthorized
        session = auth_service.get_session_by_token(db, token)
        if session:
            return session.user

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
