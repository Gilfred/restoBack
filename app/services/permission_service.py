from sqlalchemy.orm import Session
from app.models.permission import Permission

def get_permissions(db: Session):
    return db.query(Permission).all()
