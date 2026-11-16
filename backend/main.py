"""AegisCloud API entry point: app setup, middleware, routers, /health and /metrics."""

import logging
import shutil
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app import database
from app.config import DEFAULT_JWT_SECRET, settings
from app.routes import ai, alerts, auth, dashboard, reports, scan
from app.services.demo_user import ensure_demo_user
from app.utils.metrics import HTTP_LATENCY, HTTP_REQUESTS, refresh_gauges

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s: %(message)s")
logger = logging.getLogger("aegiscloud")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to MongoDB, create the allowed account, and close the connection on shutdown.

    A failed connection is logged but doesn't stop the API, so /health can report it.
    """
    if settings.JWT_SECRET == DEFAULT_JWT_SECRET:
        logger.warning("JWT_SECRET is the default value. Set a real secret in backend/.env before deploying.")
    try:
        await database.init_db()
        await ensure_demo_user()
        logger.info("Connected to MongoDB (%s) and allowed account ready", settings.MONGO_DB)
    except Exception as exc:
        logger.error("Startup database step failed: %s", exc)
    yield
    await database.close_db()


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="Container vulnerability scanning, runtime threat detection and AI analysis.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Record request count and latency for Prometheus, labelled by route template (not raw URL)."""
    started = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = getattr(route, "path", "unmatched")
    if path != "/metrics":
        HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        HTTP_LATENCY.labels(request.method, path).observe(time.perf_counter() - started)
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Return validation errors as one readable string so the UI can show them directly."""
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(part) for part in first.get("loc", []) if part not in ("body", "query"))
    message = first.get("msg", "Invalid request")
    return JSONResponse(status_code=422, content={"detail": f"{field}: {message}" if field else message})


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(scan.router, prefix="/api/scan", tags=["scan"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])


@app.get("/health", tags=["system"])
async def health():
    """Liveness check: is the API up, can it reach MongoDB, and is Trivy installed?"""
    try:
        await database.client.admin.command("ping")
        db_status = "up"
    except Exception:
        db_status = "down"
    return {
        "app": settings.APP_NAME,
        "status": "ok",
        "database": db_status,
        "trivy": "installed" if shutil.which("trivy") else "missing",
    }


@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus scrape endpoint (unauthenticated, as scrapers expect)."""
    try:
        await refresh_gauges()
    except Exception:
        logger.warning("Could not refresh database gauges for /metrics", exc_info=True)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)