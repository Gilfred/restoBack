from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import engine, create_db_and_tables
from app.models import Role, Permission, User, MethodePayment
from app.enums import MethodePaiementEnum
import datetime

def seed_data():
    with Session(engine) as session:
        # 1. Create Permissions
        permissions = [
            Permission(name="manage_restaurants", description="Can activate/deactivate restaurants"),
            Permission(name="manage_users", description="Can manage all users"),
            Permission(name="view_all_reports", description="Can view reports from all restaurants"),
        ]
        for p in permissions:
            existing = session.execute(select(Permission).where(Permission.name == p.name)).scalars().first()
            if not existing:
                session.add(p)
        session.commit()

        # 2. Create Roles
        superadmin_role = session.execute(select(Role).where(Role.name == "SUPERADMIN")).scalars().first()
        if not superadmin_role:
            superadmin_role = Role(name="SUPERADMIN", description="Super Administrator with full access")
            # Assign all permissions to superadmin
            all_perms = session.execute(select(Permission)).scalars().all()
            superadmin_role.permissions = list(all_perms)
            session.add(superadmin_role)

        admin_role = session.execute(select(Role).where(Role.name == "ADMIN")).scalars().first()
        if not admin_role:
            admin_role = Role(name="ADMIN", description="Restaurant Administrator")
            session.add(admin_role)

        session.commit()

        # 3. Create Superadmin User
        superadmin_user = session.execute(select(User).where(User.email == "admin@example.com")).scalars().first()
        if not superadmin_user:
            superadmin_user = User(
                name="Super Admin",
                email="admin@example.com",
                password="password123", # In a real app, hash this!
                isActive=True
            )
            superadmin_user.roles.append(superadmin_role)
            session.add(superadmin_user)
        session.commit()

        # 4. Create Payment Methods
        for method in MethodePaiementEnum:
            existing = session.execute(select(MethodePayment).where(MethodePayment.nomMethode == method)).scalars().first()
            if not existing:
                session.add(MethodePayment(nomMethode=method))
        session.commit()

        print("Seeding completed successfully.")

if __name__ == "__main__":
    # Ensure tables are created before seeding
    # create_db_and_tables()
    seed_data()
