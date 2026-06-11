from sqlalchemy.orm import Session
from app.models.associations import UserRole, RolePermission
from app.models.user import User
from app.models.role import Role
from typing import List
from uuid import UUID

def get_user_roles(db: Session):
    return db.query(UserRole).all()

def get_role_permissions(db: Session):
    return db.query(RolePermission).all()

def update_user_roles(db: Session, user_id: UUID, role_ids: List[UUID]):
    from sqlalchemy.orm import joinedload
    user = db.query(User).options(
        joinedload(User.roles).joinedload(Role.permissions)
    ).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Get the roles from the database
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    
    # Update the user's roles
    user.roles = roles
    db.commit()
    db.refresh(user)
    return user
