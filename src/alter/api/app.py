"""FastAPI application factory for LifeOS."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle — start/stop consciousness engine."""
    # Startup: optionally start consciousness
    if os.environ.get("ALTER_CONSCIOUSNESS") == "1":
        from alter.adapters.standalone import StandaloneAdapter

        user_id = os.environ.get("ALTER_USER_ID", "default")
        provider = os.environ.get("ALTER_LLM_PROVIDER", "anthropic")
        model = os.environ.get("ALTER_LLM_MODEL") or None

        adapter = StandaloneAdapter(
            user_id=user_id,
            provider=provider,
            model=model,
        )
        adapter.start()
        app.state.consciousness = adapter
        logger.info("Consciousness engine started for user %s", user_id)
    else:
        app.state.consciousness = None

    yield

    # Shutdown: stop consciousness if running
    if getattr(app.state, "consciousness", None):
        app.state.consciousness.stop()
        logger.info("Consciousness engine stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="LifeOS",
        description="Life Operating System — Automate thinking",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS for future mobile/SPA clients
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    from alter.api.routers import health, user, goals, constitution, cycle, consciousness, inbox, habits
    application.include_router(health.router, prefix="/api/v1", tags=["health"])
    application.include_router(user.router, prefix="/api/v1", tags=["users"])
    application.include_router(goals.router, prefix="/api/v1", tags=["goals"])
    application.include_router(constitution.router, prefix="/api/v1", tags=["constitution"])
    application.include_router(cycle.router, prefix="/api/v1", tags=["cycles"])
    application.include_router(consciousness.router, prefix="/api/v1", tags=["consciousness"])
    application.include_router(inbox.router, prefix="/api/v1", tags=["inbox"])
    application.include_router(habits.router, prefix="/api/v1", tags=["habits"])

    # Static files
    static_dir = Path(__file__).parent.parent / "web" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Web UI routes (must be last - catches /*)
    from alter.web.routes import router as web_router
    application.include_router(web_router, tags=["web"])

    return application


app = create_app()
