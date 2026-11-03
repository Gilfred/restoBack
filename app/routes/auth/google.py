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

    frontend_url = settings.FRONTEND_URL.rstrip("/")

    if not user_info:
        return RedirectResponse(
            url=f"{frontend_url}/login?error=google_auth_failed"
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

    from app.services.auth_service import generate_refresh_token
    raw_refresh_token = generate_refresh_token()

    # Une seule session active
    delete_all_user_sessions(db, user.id)
    session = create_user_session(db, user_id=user.id, raw_refresh_token=raw_refresh_token)

    # Génération du JWT avec sid
    access_token = create_access_token(subject=user.id, sid=session.id)

    # Redirection vers le frontend avec access_token dans l'URL
    redirect_url = f"{frontend_url}/auth/callback?access_token={access_token}"
    redirect_response = RedirectResponse(
        url=redirect_url,
        status_code=302,
    )

    # Cookie HttpOnly pour l'access token
    redirect_response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        secure=True,       #True en production (HTTPS)
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    # Cookie HttpOnly pour le refresh token
    refresh_max_age = settings.SESSION_ABSOLUTE_EXPIRE_DAYS * 24 * 60 * 60
    redirect_response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=refresh_max_age,
        expires=refresh_max_age,
        path="/"
    )

    return redirect_response