from sqlalchemy.orm import Session, joinedload
from app.models.role import Role

def get_roles(db: Session):
    return db.query(Role).options(joinedload(Role.permissions)).all()
