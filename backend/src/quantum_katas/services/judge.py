"""Judge service — validates user-submitted code against kata validation criteria.

Executes the user's code and the kata's validation code in a single shared
namespace so that validation_code can inspect variables (circuit, q, result, etc.)
defined by the user's code to verify correctness.
"""

from __future__ import annotations

import logging

from quantum_katas.models.kata import ValidateResponse
from quantum_katas.services.executor import execute_judge
from quantum_katas.services.kata_registry import get_kata_raw

logger = logging.getLogger(__name__)


def validate_submission(kata_id: str, user_code: str) -> ValidateResponse:
    """Validate user-submitted code for a given kata.

    Executes the user's code and validation_code in a shared namespace.
    The validation_code can access variables defined by the user's code
    (e.g. circuit, q) and uses assertions to verify correctness.

    Args:
        kata_id: The ID of the kata to validate against.
        user_code: The user's submitted Python/Cirq code.

    Returns:
        A ValidateResponse indicating pass/fail with details.
    """
    kata = get_kata_raw(kata_id)
    if kata is None:
        return ValidateResponse(
            passed=False,
            message=f"Kata not found: {kata_id}",
        )

    # Execute user code + validation code in the SAME namespace
    # so validation_code can inspect user-defined variables
    judge_result = execute_judge(user_code, kata.validation_code)

    if not judge_result.success:
        return ValidateResponse(
            passed=False,
            message=judge_result.error or "Validation failed",
            stdout=judge_result.stdout,
            stderr=judge_result.stderr,
        )

    if "PASSED" in judge_result.stdout:
        return ValidateResponse(
            passed=True,
            message="Correct! Well done!",
            stdout=judge_result.stdout,
            stderr=judge_result.stderr,
        )

    return ValidateResponse(
        passed=False,
        message="Validation did not produce expected output",
        stdout=judge_result.stdout,
        stderr=judge_result.stderr,
    )
