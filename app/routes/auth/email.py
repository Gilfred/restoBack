from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_session
from app.schemas.auth import (
    UserCreate,
    UserResponse,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
)
from app.services import auth_service, email_service
from app.dependencies import get_current_user
from app.core.config import settings
router = APIRouter()
import logging
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=UserResponse)
def signup(
    user_data: UserCreate,
    db: Session = Depends(get_session)
):
    db_user = auth_service.get_user_by_email(
        db,
        email=user_data.email
    )

    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    return auth_service.create_user(
        db=db,
        user_data=user_data
    )

@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_session)
):
    user = auth_service.authenticate_user(
        db,
        login_data.email,
        login_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return auth_service.login_user(
        db,
        user,
        response
    )

@router.post("/token", include_in_schema=False)
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session)
):
    user = auth_service.authenticate_user(
        db,
        form_data.username,
        form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return auth_service.login_user(
        db,
        user,
        response
    )

@router.post("/logout")
def logout(
    response: Response,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_session)
):
    auth_service.delete_all_user_sessions(
        db,
        current_user.id
    )
    response.delete_cookie("session_token")

    return {
        "message": "Successfully logged out"
    }

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user=Depends(get_current_user)
):
    return current_user

@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_session)
):
    user = auth_service.get_user_by_email(
        db,
        data.email
    )

    # Ne pas révéler si l'adresse email existe ou non.
    if not user:
        return {
            "message": (
                "If an account exists with this email, "
                "a reset link has been sent."
            )
        }

    token = auth_service.create_password_reset_token(
        db,
        data.email
    )

    reset_link = (
        f"{settings.FRONTEND_URL}/reset-password?token={token}"
    )

    try:
        await email_service.send_password_reset_email(
            email=data.email,
            reset_link=reset_link,
        )

    except Exception:
        logger.exception("Failed to send password reset email")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send password reset email"
        )

    return {
        "message": (
            "If an account exists with this email, "
            "a reset link has been sent."
        )
    }

@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_session)
):
    success = auth_service.reset_password(
        db,
        data.token,
        data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    return {
        "message": "Password successfully reset"
    }