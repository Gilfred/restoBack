from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

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
