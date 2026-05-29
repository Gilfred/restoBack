from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.database import create_db_and_tables
from app.seed import seed_data
from app.routes.auth.google import router as auth_router
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
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_data()

@app.get("/")
def home():
    return {"message": "Hello FastAPI", "status": "Database initialized and seeded"}
