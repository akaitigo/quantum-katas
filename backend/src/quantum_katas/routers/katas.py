"""Kata API router — endpoints for listing, retrieving, and validating katas."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from quantum_katas.services.judge import validate_submission
from quantum_katas.services.kata_registry import get_all_katas, get_kata_by_id

router = APIRouter()


class ValidateRequestBody(BaseModel):
    """Request body for kata validation."""

    code: str = Field(..., min_length=1, max_length=10_000, description="User-submitted Python (Cirq) code")


@router.get("/katas")
async def list_katas() -> list[dict[str, str | int | list[str]]]:
    """Return a list of all katas with summary information."""
    summaries = get_all_katas()
    return [asdict(s) for s in summaries]


@router.get("/katas/{kata_id}")
async def get_kata(kata_id: str) -> dict[str, str | int | list[str]]:
    """Return detailed information for a single kata (excludes solution_code)."""
    detail = get_kata_by_id(kata_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Kata not found: {kata_id}")
    return asdict(detail)


@router.post("/katas/{kata_id}/validate")
async def validate_kata(kata_id: str, body: ValidateRequestBody) -> dict[str, str | bool]:
    """Validate user-submitted code against a kata's expected output."""
    response = validate_submission(kata_id, body.code)
    return asdict(response)
