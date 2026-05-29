from fastapi import FastAPI
from app.database import create_db_and_tables
from app.seed import seed_data

#create FastAPI app
app = FastAPI(
    title= "Application de gestion des activités ",
    description= "Application d'organisation et de gestion des Bar, Restaurant et Dépôt de livraison boisson",
    version= "1.0.0",
    docs_url="/docs",
    redoc_url="/redocs",
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_data()

@app.get("/")
def home():
    return {"message": "Hello FastAPI", "status": "Database initialized and seeded"}
