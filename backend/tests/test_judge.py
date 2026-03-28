"""Tests for the judge service — validates correct solutions and sandbox security."""

from __future__ import annotations

import pytest

from quantum_katas.services.judge import validate_submission
from quantum_katas.services.kata_registry import get_kata_raw, reset_cache


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Reset kata cache before each test."""
    reset_cache()
    yield  # type: ignore[misc]
    reset_cache()


class TestValidateSubmission:
    """Tests for the validate_submission function."""

    def test_nonexistent_kata_returns_failure(self) -> None:
        result = validate_submission("nonexistent-kata", "print('hello')")
        assert result.passed is False
        assert "not found" in result.message.lower()

    def test_syntax_error_returns_failure(self) -> None:
        result = validate_submission("01-single-qubit", "def (broken")
        assert result.passed is False

    def test_disallowed_import_returns_failure(self) -> None:
        result = validate_submission("01-single-qubit", "import os\nprint(os.getcwd())")
        assert result.passed is False


class TestSolutionValidation:
    """Validate that the correct solution code for each kata passes validation."""

    @pytest.mark.slow
    def test_kata_01_solution_passes(self) -> None:
        kata = get_kata_raw("01-single-qubit")
        assert kata is not None
        result = validate_submission("01-single-qubit", kata.solution_code)
        assert result.passed is True, f"Kata 01 solution failed: {result.message}"

    @pytest.mark.slow
    def test_kata_02_solution_passes(self) -> None:
        kata = get_kata_raw("02-pauli-x-gate")
        assert kata is not None
        result = validate_submission("02-pauli-x-gate", kata.solution_code)
        assert result.passed is True, f"Kata 02 solution failed: {result.message}"

    @pytest.mark.slow
    def test_kata_03_solution_passes(self) -> None:
        kata = get_kata_raw("03-hadamard-gate")
        assert kata is not None
        result = validate_submission("03-hadamard-gate", kata.solution_code)
        assert result.passed is True, f"Kata 03 solution failed: {result.message}"


class TestSandboxSecurity:
    """Security tests for the code execution sandbox."""

    def test_file_read_blocked(self) -> None:
        code = "f = open('/etc/passwd', 'r')\nprint(f.read())"
        result = validate_submission("01-single-qubit", code)
        assert result.passed is False

    def test_os_import_blocked(self) -> None:
        result = validate_submission("01-single-qubit", "import os\nos.system('id')")
        assert result.passed is False

    def test_subprocess_import_blocked(self) -> None:
        result = validate_submission("01-single-qubit", "import subprocess\nsubprocess.run(['ls'])")
        assert result.passed is False

    def test_socket_import_blocked(self) -> None:
        result = validate_submission("01-single-qubit", "import socket")
        assert result.passed is False

    def test_eval_blocked(self) -> None:
        result = validate_submission("01-single-qubit", "eval('__import__(\"os\")')")
        assert result.passed is False
