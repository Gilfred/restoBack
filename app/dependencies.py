from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import uuid
from typing import List
from joserfc import jwt
from joserfc.jwk import OctKey
from joserfc.errors import JoseError
from sqlalchemy.orm import Session
from app.database import get_session
from app.core.config import settings
from app.core.security import ALGORITHM
from app.services import auth_service
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

def get_current_user(
    request: Request,
    db: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    # Try to get token from header (via oauth2_scheme) or cookie
    if not token:
        token = request.cookies.get("session_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        key = OctKey.import_key(settings.SECRET_KEY)
        token_obj = jwt.decode(token, key, algorithms=[ALGORITHM])
        claims = token_obj.claims
        user_id_str: str = claims.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = uuid.UUID(user_id_str)
    except (JoseError, ValueError):
        # Fallback to session token check for backward compatibility (if needed)
        # Or just raise unauthorized
        session = auth_service.get_session_by_token(db, token)
        if session:
            return session.user

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user has an active session in DB
    # This allows logout to work by deleting sessions
    active_session = db.query(auth_service.UserSession).filter(
        auth_service.UserSession.userId == user.id
    ).first()
    if not active_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée ou déconnectée",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def require_superadmin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> User:
    # Robust check: ensure roles are loaded, even if relationship was lazy
    if not any(role.name.upper() == "SUPERADMIN" for role in current_user.roles if role.name):
        # Fallback: check database directly to be absolutely sure
        from app.models.associations import UserRole
        from app.models.role import Role

        is_superadmin = db.query(Role).join(UserRole).filter(
            UserRole.userId == current_user.id,
            Role.name == "SUPERADMIN"
        ).first() is not None

        if not is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul le superAdmin peut effectuer cette action"
            )
    return current_user

def require_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> User:
    """Check if the user is a restaurant ADMIN or a SUPERADMIN."""
    is_admin = any(role.name.upper() in ["ADMIN", "SUPERADMIN"] for role in current_user.roles if role.name)

    if not is_admin:
        # Fallback: check if they are an owner of any restaurant
        from app.models.restaurant import Restaurant
        is_owner = db.query(Restaurant).filter(Restaurant.ownerId == current_user.id).first() is not None
        if is_owner:
            is_admin = True

    if not is_admin:
        # Fallback 2: check database directly for roles
        from app.models.associations import UserRole
        from app.models.role import Role

        is_admin = db.query(Role).join(UserRole).filter(
            UserRole.userId == current_user.id,
            Role.name.in_(["ADMIN", "SUPERADMIN"])
        ).first() is not None

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé: rôle ADMIN ou SUPERADMIN requis"
        )
    return current_user

def restrict_staff_modification(
    target_user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> User:
    """
    Ensure that WAITER and MANAGER_CASHIER cannot modify their own roles/permissions
    or anyone else's. Only ADMIN or SUPERADMIN can perform these actions.
    """
    # SUPERADMIN can do anything
    if any(role.name.upper() == "SUPERADMIN" for role in current_user.roles if role.name):
        return current_user

    # ADMIN can modify staff in their restaurant, but not themselves or other ADMINs/SUPERADMINs
    is_admin = any(role.name.upper() == "ADMIN" for role in current_user.roles if role.name)
    if is_admin:
        # Check if target user belongs to the same restaurant
        target_user = db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Utilisateur cible non trouvé")

        # ADMIN cannot modify themselves or other ADMINs (only SUPERADMIN can manage other ADMINs)
        is_target_admin = any(role.name.upper() in ["ADMIN", "SUPERADMIN"] for role in target_user.roles if role.name)
        if is_target_admin:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Un ADMIN ne peut pas modifier ses propres rôles/permissions ou ceux d'un autre ADMIN"
            )

        if target_user.restaurantId != current_user.restaurantId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez gérer que le personnel de votre propre restaurant"
            )

        return current_user

    # If not ADMIN or SUPERADMIN, deny access
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Vous n'avez pas la permission de modifier les rôles ou permissions"
    )

def check_permissions(*required_permissions: str):
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_session)
    ) -> User:
        # SUPERADMIN has all permissions
        if any(role.name.upper() == "SUPERADMIN" for role in current_user.roles if role.name):
            return current_user

        # OWNER fallback: Restaurant owners have all permissions for their restaurant
        from app.models.restaurant import Restaurant
        is_owner = db.query(Restaurant).filter(Restaurant.ownerId == current_user.id).first() is not None
        if is_owner:
            return current_user

        # Get all permissions for the user's roles
        user_permissions = set()
        for role in current_user.roles:
            for perm in role.permissions:
                user_permissions.add(perm.name)

        # Fallback: check database directly if needed (in case of lazy loading)
        if not all(p in user_permissions for p in required_permissions):
            from app.models.associations import RolePermission, UserRole
            from app.models.permission import Permission
            from app.models.role import Role

            db_permissions = db.query(Permission.name).join(RolePermission).join(Role).join(UserRole).filter(
                UserRole.userId == current_user.id
            ).all()
            user_permissions.update([p[0] for p in db_permissions])

        if not all(p in user_permissions for p in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission manquante: {', '.join(required_permissions)}"
            )
        return current_user
    return permission_checker

def get_user_restaurant_id(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> uuid.UUID:
    """Retrieve the restaurant ID associated with the current user (owner or active staff)."""
    from app.services import restaurant_user_service
    from app.enums import UserRestaurantStatus
    from app.models.restaurant_user import RestaurantUser

    ru = restaurant_user_service.get_my_restaurant(db, current_user.id)
    if not ru:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="L'utilisateur n'est associé à aucun restaurant"
        )

    if isinstance(ru, dict):
        # Case for owners (returned as dict by get_my_restaurant)
        if ru.get("status") != UserRestaurantStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Le restaurant n'est pas actif"
            )
        restaurant = ru.get("restaurant")
        if not restaurant:
            raise HTTPException(status_code=500, detail="Données du restaurant manquantes")
        return restaurant.id

    if isinstance(ru, RestaurantUser):
        # Case for staff (returned as RestaurantUser object)
        if ru.status != UserRestaurantStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Votre accès au restaurant n'est pas encore actif ou a été révoqué"
            )
        return ru.restaurantId

    raise HTTPException(status_code=500, detail="Type de données restaurant inattendu")
