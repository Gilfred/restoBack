from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10 # * 24 * 2   2 days
    SESSION_INACTIVITY_TIMEOUT_MINUTES: int = 30
    SESSION_ABSOLUTE_EXPIRE_DAYS: int = 7
    SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS: int = 60

    # DB
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DATABASE_URL_POSTGRES: str
    
    # Email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_SERVER: str = "smtp-relay.brevo.com"
    MAIL_PORT: int = 2525
    MAIL_TLS: bool = True
    MAIL_FROM: str
    MAIL_FROM_NAME: str = "Gilexis"
    
    # Frontend
    FRONTEND_URL: str
    
    SEED_SUPERADMIN_NAME: str
    SEED_SUPERADMIN_EMAIL: str
    SEED_SUPERADMIN_PASSWORD: str

    # Cloudinary Integration
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str


settings = Settings()
