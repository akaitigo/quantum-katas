"""Code execution router."""

from fastapi import APIRouter

from quantum_katas.models.execution import ExecutionRequest, ExecutionResult
from quantum_katas.services.executor import execute_code

router = APIRouter()


@router.post("/execute", response_model=ExecutionResult)
async def execute(request: ExecutionRequest) -> ExecutionResult:
    """Execute user-submitted Python (Cirq) code in a sandbox."""
    return execute_code(request.code)
