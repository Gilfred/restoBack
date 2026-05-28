from fastapi import FastAPI
from app.database import create_db_and_tables
from app.seed import seed_data

#create FastAPI app
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_data()

@app.get("/")
def home():
    return {"message": "Hello FastAPI", "status": "Database initialized and seeded"}
