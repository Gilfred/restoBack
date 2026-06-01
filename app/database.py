from sqlmodel import create_engine, Session
from app.models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

def create_db_and_tables():
    Base.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
