"""FastAPI application factory and middleware configuration."""

import os
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.rag.retriever import RAGRetriever
from .routes import campaigns, segments, analytics, settings, rag


# Global RAG retriever instance
rag_retriever: RAGRetriever = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown."""
    # Startup
    print("Starting FastAPI application...")

    # Load saved settings into environment on startup
    settings_file = Path("settings_store.json")
    if settings_file.exists():
        try:
            saved = json.loads(settings_file.read_text())
            env_map = {
                "openai_api_key": "OPENAI_API_KEY",
                "gmail_email": "GMAIL_EMAIL",
                "gmail_app_password": "GMAIL_APP_PASSWORD",
                "stripe_secret_key": "STRIPE_SECRET_KEY",
                "stripe_webhook_secret": "STRIPE_WEBHOOK_SECRET",
            }
            for key, env_var in env_map.items():
                if saved.get(key):
                    os.environ[env_var] = saved[key]
            print("Loaded saved settings into environment")
        except Exception as e:
            print(f"Warning: Could not load saved settings: {e}")

    global rag_retriever
    rag_retriever = RAGRetriever()
    try:
        rag_retriever.initialize()
        print("RAG retriever initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize RAG retriever: {e}")

    yield

    # Shutdown
    print("Shutting down FastAPI application...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="OHM Email Intelligence Agent API",
        description="REST API for email generation, analytics, and CRM integration",
        version="1.0.0",
        lifespan=lifespan
    )

    # CORS middleware - allow all origins for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "OHM Email Intelligence Agent API"}

    # Include route modules
    app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
    app.include_router(segments.router, prefix="/api/segments", tags=["Segments"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
    app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
    app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])

    return app


# Create the app instance
app = create_app()
