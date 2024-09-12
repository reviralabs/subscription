from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import subscription
from app.api.routes import webhook
from app.core.config import settings
from app.db.database import init_db

app = FastAPI(title=settings.PROJECT_NAME)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(subscription.router, prefix="/api/v1")
app.include_router(webhook.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    await init_db()
