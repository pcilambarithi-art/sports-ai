import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.init_db import init_db
from app.ml.model_service import model_service
from app.routers import (
    assistant_dashboard,
    auth,
    injury,
    ml_predictions,
    performance,
    skills_gamification,
    strategy,
    telemetry,
    training,
    users,
    video,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("apexpulse")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Initializing database tables and static badge catalog...")
    init_db()
    logger.info("Loading model metadata and 70k dataset benchmarks...")
    model_service.initialize_metadata_and_benchmarks()
    if settings.AUTO_LOAD_MODEL:
        logger.info("Starting background loader for existing trained model at %s", settings.model_path)
        model_service.start_background_load()
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Production AI-Powered Sports Coaching System integrating the user's existing trained "
        "ExtraTreesRegressor calorie prediction model (D:\\V3) with OpenCV video analysis, "
        "personalized training programs, workload injury-risk monitoring, game strategy optimization, "
        "real-time telemetry, skill scoring, gamification, and a data-grounded virtual coaching assistant."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
    return response


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "database_dialect": settings.DATABASE_URL.split("://")[0],
        "ml_model_status": model_service.status,
        "ml_model_ready": model_service.status == "ready",
    }


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ml_predictions.router)
app.include_router(performance.router)
app.include_router(training.router)
app.include_router(injury.router)
app.include_router(strategy.router)
app.include_router(telemetry.router)
app.include_router(video.router)
app.include_router(skills_gamification.router)
app.include_router(assistant_dashboard.router)
