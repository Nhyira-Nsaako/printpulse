import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.mqtt import mqtt_listener
from app.routers import auth, faults, dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Creating database tables (if not exist)…")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Starting MQTT listener background task…")
    mqtt_task = asyncio.create_task(mqtt_listener())

    yield  # app is running

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Shutting down MQTT listener…")
    mqtt_task.cancel()
    try:
        await mqtt_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="PrintPulse API",
    description="Backend for the PrintPulse FDM 3D Printer Predictive Maintenance System.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Adjust origins for production deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(faults.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "PrintPulse API"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
