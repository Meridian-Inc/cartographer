import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routers.mapper import router as mapper_router
from .routers.health_proxy import router as health_proxy_router
from .routers.auth_proxy import router as auth_proxy_router
from .routers.metrics_proxy import router as metrics_proxy_router
from .routers.assistant_proxy import router as assistant_proxy_router
from .routers.notification_proxy import router as notification_proxy_router


# Resolve dist path at module level so it's available for route definitions
_default_dist = Path(__file__).resolve().parents[3] / "frontend" / "dist"
DIST_PATH = Path(os.environ.get("FRONTEND_DIST", str(_default_dist)))


def create_app() -> FastAPI:
	app = FastAPI(title="Cartographer Backend", version="0.1.0")

	# Allow local dev UIs
	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	# API routes - these MUST be registered before static file handling
	app.include_router(mapper_router, prefix="/api")
	app.include_router(health_proxy_router, prefix="/api")
	app.include_router(auth_proxy_router, prefix="/api")
	app.include_router(metrics_proxy_router, prefix="/api")
	app.include_router(assistant_proxy_router, prefix="/api")
	app.include_router(notification_proxy_router, prefix="/api")

	# Serve built frontend if present (for production)
	if DIST_PATH.exists():
		index_file = DIST_PATH / "index.html"
		assets_dir = DIST_PATH / "assets"

		# Mount Vite assets directory
		if assets_dir.exists():
			app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

		if index_file.exists():
			# Explicit favicon route - this ensures it's served correctly
			@app.get("/favicon.png", include_in_schema=False)
			async def serve_favicon():
				favicon_path = DIST_PATH / "favicon.png"
				if favicon_path.exists():
					return FileResponse(
						str(favicon_path),
						media_type="image/png",
						headers={"Cache-Control": "public, max-age=86400"}
					)
				return FileResponse(str(index_file))

			# Serve index.html for root
			@app.get("/", include_in_schema=False)
			async def serve_index():
				return FileResponse(str(index_file))

			# SPA catch-all - must be LAST
			@app.get("/{full_path:path}", include_in_schema=False)
			async def serve_spa(full_path: str):
				# Don't catch /api routes (shouldn't happen due to order, but be safe)
				if full_path.startswith("api/"):
					return {"detail": "Not Found"}
				
				# Check if it's a static file in dist root
				file_path = DIST_PATH / full_path
				if file_path.exists() and file_path.is_file():
					# Security: ensure path is within dist directory
					try:
						file_path.resolve().relative_to(DIST_PATH.resolve())
						return FileResponse(str(file_path))
					except ValueError:
						pass  # Path traversal attempt, serve index.html
				
				# Default: serve index.html for SPA routing
				return FileResponse(str(index_file))

	return app


app = create_app()


