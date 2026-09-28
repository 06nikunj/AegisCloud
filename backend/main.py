import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.routes import auth, dashboard

logger = logging.getLogger("aegiscloud")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        logger.info("Connected to MongoDB (%s)", settings.MONGO_DB)
    except Exception as exc:  # keep the API up so /health can report the problem
        logger.error("MongoDB connection failed: %s", exc)
    yield
    await close_db()


app = FastAPI(title=f"{settings.APP_NAME} API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])


@app.get("/health", tags=["system"])
async def health():
    from app.database import client

    try:
        await client.admin.command("ping")
        db_status = "up"
    except Exception:
        db_status = "down"
    return {"app": settings.APP_NAME, "status": "ok", "database": db_status}