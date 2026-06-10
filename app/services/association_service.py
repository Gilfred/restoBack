from sqlalchemy.orm import Session
from app.models.associations import UserRole, RolePermission

def get_user_roles(db: Session):
    return db.query(UserRole).all()

def get_role_permissions(db: Session):
    return db.query(RolePermission).all()
