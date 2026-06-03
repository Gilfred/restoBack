from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.database import create_db_and_tables
from app.seed import seed_data
from app.routes.auth.google import router as google_auth_router
from app.routes.auth.email import router as email_auth_router
from app.routes.restaurant import router as restaurant_router
from app.routes.role import router as role_router
from app.routes.permission import router as permission_router
import os

#create FastAPI app
app = FastAPI(
    title= "Application de gestion des activités ",
    description= "Application d'organisation et de gestion des Bar, Restaurant et Dépôt de livraison boisson",
    version= "1.0.0",
    docs_url="/docs",
    redoc_url="/redocs",
)

# Add SessionMiddleware for Authlib
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your-secret-key"))

# Include routers
app.include_router(google_auth_router, prefix="/auth", tags=["google-authentication"])
app.include_router(email_auth_router, prefix="/auth", tags=["email-authentication"])
app.include_router(restaurant_router, prefix="/restaurants", tags=["restaurants"])
app.include_router(role_router, prefix="/roles", tags=["roles"])
app.include_router(permission_router, prefix="/permissions", tags=["permissions"])

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_data()

@app.get("/")
def home():
    return {"message": "Hello FastAPI", "status": "Database initialized and seeded"}
