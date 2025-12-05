import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from .routers.mapper import router as mapper_router
from .routers.health_proxy import router as health_proxy_router
from .routers.auth_proxy import router as auth_proxy_router
from .routers.metrics_proxy import router as metrics_proxy_router
from .routers.assistant_proxy import router as assistant_proxy_router
from .routers.notification_proxy import router as notification_proxy_router


class SPAStaticFiles(StaticFiles):
	"""StaticFiles subclass that serves index.html for missing files (SPA support)."""
	
	async def get_response(self, path: str, scope) -> Response:
		try:
			return await super().get_response(path, scope)
		except StarletteHTTPException as ex:
			if ex.status_code == 404:
				# For 404s, serve index.html (SPA routing)
				return await super().get_response("index.html", scope)
			raise


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

	app.include_router(mapper_router, prefix="/api")
	app.include_router(health_proxy_router, prefix="/api")
	app.include_router(auth_proxy_router, prefix="/api")
	app.include_router(metrics_proxy_router, prefix="/api")
	app.include_router(assistant_proxy_router, prefix="/api")
	app.include_router(notification_proxy_router, prefix="/api")

	# Serve built frontend if present (for production) with SPA fallback
	# FRONTEND_DIST can override default location
	default_dist = Path(__file__).resolve().parents[3] / "frontend" / "dist"
	dist_path = Path(os.environ.get("FRONTEND_DIST", str(default_dist)))
	if dist_path.exists():
		index_file = dist_path / "index.html"
		if index_file.exists():
			# Mount entire dist directory with SPA support
			# This serves static files AND falls back to index.html for missing paths
			app.mount("/", SPAStaticFiles(directory=str(dist_path), html=True), name="spa")

	return app


app = create_app()


