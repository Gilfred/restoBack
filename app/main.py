from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.database import create_db_and_tables
from app.seed import seed_data
from app.routes.auth.google import router as google_auth_router
from app.routes.auth.email import router as email_auth_router
from app.routes.restaurant import router as restaurant_router
from app.routes.restaurant_user import router as restaurant_user_router
from app.routes.role import router as role_router
from app.routes.permission import router as permission_router
from app.routes.condiment import router as condiment_router
from app.routes.appro_cuisine import router as appro_cuisine_router
from app.routes.appro_boisson import router as appro_boisson_router
from app.routes.boisson import router as boisson_router
from app.routes.commande import router as commande_router
from app.routes.unite import router as unite_router
from app.routes.casier import router as casier_router
from app.routes.commande_article import router as commande_article_router
from app.routes.associations import router as associations_router
import os

#create FastAPI app
app = FastAPI(
    title= "Gilexis Business Suite ",
    description= "Application d'organisation et de gestion des Bar, Restaurant et Dépôt de livraison boisson",
    version= "1.0.0",
    docs_url="/docs",
    redoc_url="/redocs",
)

# Add SessionMiddleware for Authlib
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key"),
    same_site="lax",    #PERMET au cookie d'être envoyé depuis la redirection de Google
    secure=True,        # OBLIGATOIRE car Render utilise le HTTPS
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:5173",
        # "http://127.0.0.1:5173",
        "https://grandresto.gilexist.workers.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(google_auth_router, prefix="/auth", tags=["google-authentication"])
app.include_router(email_auth_router, prefix="/auth", tags=["email-authentication"])
app.include_router(restaurant_router, prefix="/restaurants", tags=["restaurants"])
app.include_router(restaurant_user_router, prefix="/restaurant-users", tags=["restaurant-users"])
app.include_router(role_router, prefix="/roles", tags=["roles"])
app.include_router(permission_router, prefix="/permissions", tags=["permissions"])
app.include_router(condiment_router, prefix="/condiments", tags=["condiments"])
app.include_router(appro_cuisine_router, prefix="/appro-cuisine", tags=["appro-cuisine"])
app.include_router(appro_boisson_router, prefix="/appro-boisson", tags=["appro-boisson"])
app.include_router(boisson_router, prefix="/boissons", tags=["boissons"])
app.include_router(commande_router, prefix="/commandes", tags=["commandes"])
app.include_router(unite_router, prefix="/unites", tags=["unites"])
app.include_router(casier_router, prefix="/casiers", tags=["casiers"])
app.include_router(commande_article_router, prefix="/commande-articles", tags=["commande-articles"])
app.include_router(associations_router, prefix="/associations", tags=["associations"])

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_data()

@app.get("/")
def home():
    return {"message": "Bienvenus sur Gilexis Business", 
            "status": "Database initialized and seeded",
            "documetation":"docs",
            "version": "1.0.0",
            'alternative':"redocs"
            }
