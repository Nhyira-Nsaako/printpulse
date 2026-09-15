import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.mqtt import mqtt_listener
from app.routers import auth, faults, dashboard


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # -------------------------------------------------------------------------
    # STARTUP
    # -------------------------------------------------------------------------

    logger.info("Application starting...")

    logger.info("Starting MQTT listener...")
    mqtt_task = asyncio.create_task(mqtt_listener())

    yield

    # -------------------------------------------------------------------------
    # SHUTDOWN
    # -------------------------------------------------------------------------

    logger.info("Shutting down MQTT listener...")

    mqtt_task.cancel()

    try:
        await mqtt_task
    except asyncio.CancelledError:
        logger.info("MQTT listener cancelled.")

    await engine.dispose()

    logger.info("Shutdown complete.")


app = FastAPI(
    title="PrintPulse API",
    description="Backend for the PrintPulse FDM 3D Printer Predictive Maintenance System.",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(faults.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "PrintPulse API",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
    }
