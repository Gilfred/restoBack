from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import engine, create_db_and_tables
from app.models import Role, Permission, User, MethodePayment
from app.enums import MethodePaiementEnum
from app.core.security import get_password_hash
from app.core.config import settings

def seed_data():
    with Session(engine) as session:
        # 1. Create Permissions
        permissions_data = [
            ("manage_restaurants", "Can activate/deactivate restaurants"),
            ("manage_users", "Can manage all users"),
            ("view_all_reports", "Can view reports from all restaurants"),
            ("create_orders", "Permet de créer de nouvelles commandes"),
            ("update_orders", "Permet de modifier des commandes existantes"),
            ("view_orders", "Permet de consulter la liste et les détails des commandes"),
            ("view_menu", "Permet de consulter le menu du restaurant"),
            ("process_payments", "Permet d'enregistrer les paiements des clients"),
            ("view_restaurant_reports", "Permet de consulter les rapports de performance du restaurant"),
            ("manage_staff", "Permet de gérer les employés du restaurant"),
        ]
        for name, desc in permissions_data:
            existing = session.execute(select(Permission).where(Permission.name == name)).scalars().first()
            if not existing:
                session.add(Permission(name=name, description=desc))
            else:
                existing.description = desc
        session.commit()

        # 2. Create Roles
        roles_data = [
            ("SUPERADMIN", "Super Administrator with full access"),
            ("ADMIN", "Propriétaire/Administrateur d'un restaurant"),
            ("WAITER", "Serveur / Serveuse du restaurant"),
            ("MANAGER_CASHIER", "Gérant ou Caissier du restaurant"),
        ]

        for name, desc in roles_data:
            role = session.execute(select(Role).where(func.upper(Role.name) == name.upper())).scalars().first()
            if not role:
                role = Role(name=name, description=desc)
                session.add(role)
            else:
                role.description = desc
        session.commit()

        # 3. Associate Permissions to Roles
        all_permissions = {p.name: p for p in session.execute(select(Permission)).scalars().all()}

        role_permissions_mapping = {
            "SUPERADMIN": list(all_permissions.keys()),
            "ADMIN": [
                "manage_staff", "create_orders", "update_orders",
                "view_orders", "view_menu", "process_payments", "view_restaurant_reports"
            ],
            "WAITER": ["create_orders", "update_orders", "view_orders", "view_menu"],
            "MANAGER_CASHIER": ["view_orders", "process_payments", "view_restaurant_reports"]
        }

        for role_name, perms in role_permissions_mapping.items():
            role = session.execute(select(Role).where(func.upper(Role.name) == role_name.upper())).scalars().first()
            if role:
                target_perms = [all_permissions[p_name] for p_name in perms if p_name in all_permissions]
                role.permissions = target_perms

        session.commit()

        # 4. Create/Update Superadmin User
        superadmin_user = session.execute(
                select(User).where(
                    func.lower(User.email) == settings.SEED_SUPERADMIN_EMAIL.lower()
                )
            ).scalars().first()
        if not superadmin_user:
            superadmin_user = User(
                name=settings.SEED_SUPERADMIN_NAME,
                email=settings.SEED_SUPERADMIN_EMAIL,
                password=get_password_hash(settings.SEED_SUPERADMIN_PASSWORD),
                isActive=True
            )
            session.add(superadmin_user)

        superadmin_role = session.execute(select(Role).where(func.upper(Role.name) == "SUPERADMIN")).scalars().first()
        if superadmin_role and superadmin_role not in superadmin_user.roles:
            superadmin_user.roles.append(superadmin_role)

        session.commit()

        # 5. Create Payment Methods
        for method in MethodePaiementEnum:
            existing = session.execute(select(MethodePayment).where(MethodePayment.nomMethode == method)).scalars().first()
            if not existing:
                session.add(MethodePayment(nomMethode=method))
        session.commit()

        print("Seeding completed successfully.")

if __name__ == "__main__":
    # Ensure tables are created before seeding
    create_db_and_tables()
    seed_data()
