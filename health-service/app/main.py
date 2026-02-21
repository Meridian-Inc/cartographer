import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import reload_env_overrides, settings
from .routers.health import router as health_router
from .services.health_checker import health_checker
from .services.usage_middleware import UsageTrackingMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown events"""
    # Startup: Start the background monitoring loop
    logger.info("Starting background health monitoring...")
    health_checker.start_monitoring()

    yield

    # Shutdown: Stop the background monitoring loop
    logger.info("Stopping background health monitoring...")
    health_checker.stop_monitoring()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cartographer Health Service",
        description="Health monitoring microservice for network devices",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if settings.disable_docs else "/docs",
        redoc_url=None if settings.disable_docs else "/redoc",
        openapi_url=None if settings.disable_docs else "/openapi.json",
    )

    # CORS middleware - read origins from settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Usage tracking middleware - reports endpoint usage to metrics service
    app.add_middleware(UsageTrackingMiddleware, service_name="health-service")

    # Include routers
    app.include_router(health_router, prefix="/api")

    @app.get("/")
    def root():
        return {
            "service": "Cartographer Health Service",
            "status": "running",
            "version": "0.1.0",
        }

    @app.get("/healthz")
    def healthz():
        """Health check endpoint for container orchestration"""
        return {"status": "healthy"}

    @app.post("/_internal/reload-env")
    async def reload_env(request: Request):
        """
        Hot-reload environment-specific settings without restarting.

        Called by the deploy swap script during blue/green swaps.
        Only accessible from within the Docker network.
        """
        body = await request.json()
        updated = reload_env_overrides(body)
        return {"status": "ok", "updated": updated}

    return app


app = create_app()
