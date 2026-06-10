from fastapi import APIRouter, Depends, Request
from app.providers.google import oauth
from app.services.auth_service import get_or_create_user_google, create_user_session
from app.database import get_session
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import create_access_token
from fastapi import Response

router = APIRouter()

@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, response: Response, db: Session = Depends(get_session)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    if user_info:
        user = get_or_create_user_google(
            db,
            email=user_info['email'],
            name=user_info['name'],
            picture=user_info['picture'],
            provider_account_id=user_info['sub']
        )
        access_token = create_access_token(subject=user.id)

        # Create a session for consistency and logout support
        from app.services.auth_service import delete_all_user_sessions
        delete_all_user_sessions(db, user.id)
        create_user_session(db, user_id=user.id)

        response.set_cookie(
            key="session_token",
            value=access_token,
            httponly=True,
            max_age=7 * 24 * 60 * 60,
            expires=7 * 24 * 60 * 60,
            samesite="lax",
            secure=False,
        )

        return {
            "status": "success",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"email": user.email, "name": user.name}
        }
    
    return {"status": "error", "message": "Failed to fetch user info"}
