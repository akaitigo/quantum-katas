"""Judge service — validates user-submitted code against kata validation criteria.

Executes the user's code in a sandbox and then runs the kata's validation
code to determine correctness. The validation code receives the user's code
via a shared preamble so it can verify the actual user submission.
"""

from __future__ import annotations

import logging

from quantum_katas.models.kata import ValidateResponse
from quantum_katas.services.executor import execute_code
from quantum_katas.services.kata_registry import get_kata_raw

logger = logging.getLogger(__name__)


def validate_submission(kata_id: str, user_code: str) -> ValidateResponse:
    """Validate user-submitted code for a given kata.

    First executes the user's code to verify it runs without errors,
    then executes the kata's validation_code with the user's code prepended
    so that the validation logic operates on the user's actual output.

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

    # Execute user code first to check for errors
    user_result = execute_code(user_code)
    if not user_result.success:
        return ValidateResponse(
            passed=False,
            message=user_result.error or "Code execution failed",
            stdout=user_result.stdout,
            stderr=user_result.stderr,
        )

    # Combine user code + validation code so validation operates on user's work
    combined_code = user_code + "\n" + kata.validation_code
    validation_result = execute_code(combined_code)

    if not validation_result.success:
        return ValidateResponse(
            passed=False,
            message=validation_result.error or "Validation failed",
            stdout=validation_result.stdout,
            stderr=validation_result.stderr,
        )

    if "PASSED" in validation_result.stdout:
        return ValidateResponse(
            passed=True,
            message="Correct! Well done!",
            stdout=validation_result.stdout,
            stderr=validation_result.stderr,
        )

    return ValidateResponse(
        passed=False,
        message="Validation did not produce expected output",
        stdout=validation_result.stdout,
        stderr=validation_result.stderr,
    )
