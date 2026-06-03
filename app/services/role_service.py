from sqlalchemy.orm import Session
from app.models.role import Role

def get_roles(db: Session):
    return db.query(Role).all()
