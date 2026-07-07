from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.providers.google import oauth
from app.services.auth_service import (
    get_or_create_user_google,
    create_user_session,
    delete_all_user_sessions,
)
from app.database import get_session
from app.core.config import settings
from app.core.security import create_access_token

router = APIRouter()


@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_session),
):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    if not user_info:
        return RedirectResponse(
            url="http://localhost:5173/login?error=google_auth_failed"
        )

    # Création ou récupération de l'utilisateur
    user = get_or_create_user_google(
        db=db,
        email=user_info["email"],
        name=user_info["name"],
        picture=user_info["picture"],
        provider_account_id=user_info["sub"],
    )

    # Génération du JWT
    access_token = create_access_token(subject=user.id)

    # Une seule session active
    delete_all_user_sessions(db, user.id)
    create_user_session(db, user_id=user.id)

    # Redirection vers le frontend
    redirect_response = RedirectResponse(
        url="http://localhost:5173/auth/callback",
        status_code=302,
    )

    # Cookie HttpOnly
    redirect_response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        secure=False,       # Mettre True en production (HTTPS)
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        expires=7 * 24 * 60 * 60,
    )

    return redirect_response