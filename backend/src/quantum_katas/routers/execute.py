"""Code execution router."""

from fastapi import APIRouter, HTTPException, Request

from quantum_katas.models.execution import ExecutionRequest, ExecutionResult
from quantum_katas.services.executor import execute_code
from quantum_katas.services.rate_limiter import rate_limiter

router = APIRouter()


@router.post("/execute", response_model=ExecutionResult)
async def execute(request: Request, body: ExecutionRequest) -> ExecutionResult:
    """Execute user-submitted Python (Cirq) code in a sandbox."""
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    return execute_code(body.code)
