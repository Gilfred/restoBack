from fastapi import APIRouter, Depends, Request
from app.providers.google import oauth
from app.services.auth_service import get_or_create_user_google
from app.database import get_session
from sqlalchemy.orm import Session
from app.core.config import settings

router = APIRouter()

@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_session)):
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
        # Here you would typically create a session or JWT for the user
        # For now, let's just return the user info or a success message
        return {"status": "success", "user": {"email": user.email, "name": user.name}}

    return {"status": "error", "message": "Failed to fetch user info"}
