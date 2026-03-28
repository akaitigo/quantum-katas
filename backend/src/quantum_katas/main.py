"""FastAPI application entry point."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from quantum_katas.routers import execute, katas

app = FastAPI(
    title="quantum-katas API",
    description="Interactive quantum computing learning platform",
    version="0.1.0",
)

_cors_origins_env = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
_cors_origins = [origin.strip() for origin in _cors_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(execute.router, prefix="/api")
app.include_router(katas.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
