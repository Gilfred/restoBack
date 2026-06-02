from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # We raise an informative error rather than hardcoding a default with credentials.
    raise ValueError(
        "DATABASE_URL is not set. Please set the environment variable, "
        "for example: export DATABASE_URL=postgresql://user:password@localhost:5432/dbname"
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    Base.metadata.create_all(engine)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
