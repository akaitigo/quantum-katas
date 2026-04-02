"""Execution request/response models."""

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    """Request body for code execution."""

    code: str = Field(..., min_length=1, max_length=10_000, description="Python (Cirq) code to execute")


class ExecutionResult(BaseModel):
    """Result of code execution."""

    stdout: str = Field(default="", description="Standard output from execution")
    stderr: str = Field(default="", description="Standard error from execution")
    success: bool = Field(default=True, description="Whether execution completed without errors")
    error: str | None = Field(default=None, description="Error message if execution failed")
