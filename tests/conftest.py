import os

# Set dummy environment variables before any app imports
os.environ["SECRET_KEY"] = "dummy_secret_key"
os.environ["DB_USER"] = "dummy"
os.environ["DB_PASSWORD"] = "dummy"
os.environ["DB_HOST"] = "dummy"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "dummy"
os.environ["DATABASE_URL_POSTGRES"] = "postgresql://dummy:dummy@localhost:5432/dummy"
os.environ["SEED_SUPERADMIN_NAME"] = "dummy"
os.environ["SEED_SUPERADMIN_EMAIL"] = "dummy"
os.environ["SEED_SUPERADMIN_PASSWORD"] = "dummy"
os.environ["MAIL_USERNAME"] = "dummy"
os.environ["MAIL_PASSWORD"] = "dummy"
os.environ["MAIL_FROM"] = "dummy@example.com"
os.environ["FRONTEND_URL"] = "http://localhost:3000"
