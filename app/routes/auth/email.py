from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.database import get_session
from app.schemas.auth import UserCreate, UserResponse, LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.services import auth_service
from datetime import timedelta

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_session)):
    db_user = auth_service.get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return auth_service.create_user(db=db, user_data=user_data)

@router.post("/login")
def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_session)
):
    user = auth_service.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    session = auth_service.create_user_session(db, user_id=user.id)
    
    # We can use both a cookie and return the token
    response.set_cookie(
        key="session_token",
        value=session.token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        expires=7 * 24 * 60 * 60,
        samesite="lax",
        secure=False, # Should be True in production with HTTPS
    )
    
    return {"access_token": session.token, "token_type": "bearer"}

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_session)
):
    token = request.cookies.get("session_token")
    if token:
        auth_service.delete_session(db, token)
    
    response.delete_cookie("session_token")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
def get_me(
    request: Request,
    db: Session = Depends(get_session)
):
    # Try to get token from header or cookie
    token = request.cookies.get("session_token")
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    session = auth_service.get_session_by_token(db, token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    
    return session.user

@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_session)
):
    user = auth_service.get_user_by_email(db, data.email)
    if not user:
        # We return 200 even if user doesn't exist for security reasons (prevent email enumeration)
        return {"message": "If an account exists with this email, a reset link has been sent."}
    
    auth_service.create_password_reset_token(db, data.email)
    
    # Here you would typically send an email
    return {
        "message": "If an account exists with this email, a reset link has been sent."
    }

@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_session)
):
    success = auth_service.reset_password(db, data.token, data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    return {"message": "Password successfully reset"}
