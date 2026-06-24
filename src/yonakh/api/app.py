"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from yonakh.api.deps import init_app_state
from yonakh.config import get_settings
from yonakh.db.engine import init_db
from yonakh.embedding.pipeline import get_embedding_provider

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    conn = init_db(settings.db_path)
    provider = get_embedding_provider()
    state = init_app_state(conn, provider)
    logger.info("Engram server started on %s:%d", settings.host, settings.port)
    yield
    state.conn.close()
    logger.info("Engram server stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Engram",
        description="Local-first AI memory server for software engineering workflows",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from yonakh.api.routes import admin, entities, events, ingest, relationships, search
    app.include_router(events.router, prefix="/api/v1")
    app.include_router(entities.router, prefix="/api/v1")
    app.include_router(relationships.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(ingest.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")

    # Serve the built React dashboard as static files
    dashboard_dir = Path(__file__).parent.parent.parent.parent / "dashboard" / "dist"
    if dashboard_dir.exists():
        app.mount(
            "/dashboard",
            StaticFiles(directory=str(dashboard_dir), html=True),
            name="dashboard",
        )

    return app
