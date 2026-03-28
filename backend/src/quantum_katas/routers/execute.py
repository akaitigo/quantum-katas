"""Code execution router."""

import asyncio

from fastapi import APIRouter

from quantum_katas.models.execution import ExecutionRequest, ExecutionResult
from quantum_katas.services.executor import execute_code

router = APIRouter()


@router.post("/execute", response_model=ExecutionResult)
async def execute(request: ExecutionRequest) -> ExecutionResult:
    """Execute user-submitted Python (Cirq) code in a sandbox.

    Uses asyncio.to_thread to avoid blocking the event loop during
    synchronous subprocess execution.
    """
    return await asyncio.to_thread(execute_code, request.code)
