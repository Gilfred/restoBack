from sqlalchemy.orm import Session
import uuid
from app.models.associations import UserRole, RolePermission

def get_user_roles(db: Session):
    return db.query(UserRole).all()

def get_role_permissions(db: Session):
    return db.query(RolePermission).all()

def add_user_role(db: Session, user_id: uuid.UUID, role_id: uuid.UUID):
    user_role = UserRole(userId=user_id, roleId=role_id)
    db.add(user_role)
    db.commit()
    db.refresh(user_role)
    return user_role

def remove_user_role(db: Session, user_id: uuid.UUID, role_id: uuid.UUID):
    user_role = db.query(UserRole).filter(
        UserRole.userId == user_id,
        UserRole.roleId == role_id
    ).first()
    if user_role:
        db.delete(user_role)
        db.commit()
        return True
    return False

def add_role_permission(db: Session, role_id: uuid.UUID, permission_id: uuid.UUID):
    role_perm = RolePermission(roleId=role_id, permissionId=permission_id)
    db.add(role_perm)
    db.commit()
    db.refresh(role_perm)
    return role_perm

def remove_role_permission(db: Session, role_id: uuid.UUID, permission_id: uuid.UUID):
    role_perm = db.query(RolePermission).filter(
        RolePermission.roleId == role_id,
        RolePermission.permissionId == permission_id
    ).first()
    if role_perm:
        db.delete(role_perm)
        db.commit()
        return True
    return False
