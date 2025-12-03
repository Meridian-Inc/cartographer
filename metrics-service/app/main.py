"""
Cartographer Metrics Service

A microservice for publishing consistent network topology metrics
to Redis pub/sub for consumption by other services.

This service:
- Aggregates data from the health service and backend
- Generates comprehensive network topology snapshots
- Publishes metrics to Redis channels
- Provides WebSocket endpoint for real-time updates
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.metrics import router as metrics_router
from .services.redis_publisher import redis_publisher
from .services.metrics_aggregator import metrics_aggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    
    On startup:
    - Connect to Redis
    - Start the background metrics publishing loop
    
    On shutdown:
    - Stop publishing
    - Disconnect from Redis
    """
    # Startup
    logger.info("Starting Cartographer Metrics Service...")
    
    # Connect to Redis
    redis_connected = await redis_publisher.connect()
    if redis_connected:
        logger.info("Connected to Redis successfully")
    else:
        logger.warning("Failed to connect to Redis - will retry on publish")
    
    # Start background publishing
    metrics_aggregator.start_publishing()
    logger.info("Background metrics publishing started")
    
    # Generate initial snapshot
    try:
        initial_snapshot = await metrics_aggregator.generate_snapshot()
        if initial_snapshot:
            logger.info(f"Initial snapshot generated with {initial_snapshot.total_nodes} nodes")
            if redis_connected:
                await redis_publisher.store_last_snapshot(initial_snapshot)
    except Exception as e:
        logger.warning(f"Failed to generate initial snapshot: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Cartographer Metrics Service...")
    
    # Stop publishing
    metrics_aggregator.stop_publishing()
    logger.info("Background publishing stopped")
    
    # Disconnect from Redis
    await redis_publisher.disconnect()
    logger.info("Disconnected from Redis")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Cartographer Metrics Service",
        description="""
Network topology metrics publishing service for Cartographer.

This service aggregates network topology and health data from multiple sources
and publishes comprehensive metrics to Redis pub/sub channels for consumption
by other services and real-time dashboards.

## Features

- **Topology Snapshots**: Complete network topology with node metrics
- **Health Status**: Device health, uptime, and connectivity information
- **ISP Metrics**: Gateway test IPs and speed test results
- **Real-time Updates**: WebSocket and Redis pub/sub for live data
- **Node Connections**: Connection graph with speed information

## Redis Channels

- `metrics:topology` - Full topology snapshots and node updates
- `metrics:health` - Health status changes
- `metrics:speedtest` - Speed test results
        """,
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # CORS middleware
    allowed_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(metrics_router, prefix="/api")
    
    # Root endpoint
    @app.get("/")
    def root():
        """Service information endpoint."""
        return {
            "service": "Cartographer Metrics Service",
            "description": "Network topology metrics publishing service",
            "status": "running",
            "version": "0.1.0",
            "endpoints": {
                "metrics": "/api/metrics",
                "docs": "/docs",
                "health": "/healthz",
            }
        }
    
    # Health check endpoint
    @app.get("/healthz")
    async def healthz():
        """
        Health check endpoint for container orchestration.
        Returns service health status including Redis connectivity.
        """
        redis_info = await redis_publisher.get_connection_info()
        config = metrics_aggregator.get_config()
        
        return {
            "status": "healthy",
            "redis_connected": redis_info["connected"],
            "publishing_enabled": config["publishing_enabled"],
            "is_publishing": config["is_running"],
        }
    
    # Readiness check endpoint
    @app.get("/ready")
    async def readyz():
        """
        Readiness check endpoint.
        Returns ready only when the service can fulfill requests.
        """
        redis_info = await redis_publisher.get_connection_info()
        
        # Service is ready if Redis is connected
        is_ready = redis_info["connected"]
        
        return {
            "ready": is_ready,
            "redis_connected": redis_info["connected"],
        }
    
    return app


# Create the application instance
app = create_app()
