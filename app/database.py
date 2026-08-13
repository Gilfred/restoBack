from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.core.config import settings

# Use the database URL from settings which handles .env and defaults
DATABASE_URL = settings.DATABASE_URL_POSTGRES

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL_POSTGRES is not set in settings. "
        "Please check your .env file or environment variables."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def create_db_and_tables():
    Base.metadata.create_all(engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()