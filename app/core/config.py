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
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_FROM: str
    MAIL_FROM_NAME: str = "Gilexis"
    
    # Frontend
    FRONTEND_URL: str
    
    SEED_SUPERADMIN_NAME: str
    SEED_SUPERADMIN_EMAIL: str
    SEED_SUPERADMIN_PASSWORD: str


settings = Settings()
