"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from quantum_katas.routers import execute, katas

app = FastAPI(
    title="quantum-katas API",
    description="Interactive quantum computing learning platform",
    version="0.1.0",
)

_DEFAULT_CORS_ORIGINS = "http://localhost:5173"
_cors_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(execute.router, prefix="/api")
app.include_router(katas.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
