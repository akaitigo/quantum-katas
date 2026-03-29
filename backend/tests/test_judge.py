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


class TestNegativeValidation:
    """H-3: Verify that WRONG answers correctly fail validation for all katas."""

    @pytest.mark.slow
    def test_print_hello_fails_kata_01(self) -> None:
        """C-1 destructive test: print('hello') must NOT pass."""
        result = validate_submission("01-single-qubit", "print('hello')")
        assert result.passed is False, "print('hello') should not pass kata validation!"

    @pytest.mark.slow
    def test_empty_circuit_fails_kata_02(self) -> None:
        """An empty circuit (no X gate) should fail kata 02."""
        code = (
            "import cirq\n"
            "q = cirq.LineQubit(0)\n"
            "circuit = cirq.Circuit([cirq.measure(q, key='result')])\n"
            "sim = cirq.Simulator()\n"
            "result = sim.run(circuit, repetitions=10)\n"
            "print(result)\n"
        )
        result = validate_submission("02-pauli-x-gate", code)
        assert result.passed is False, "Circuit without X gate should fail kata 02"

    @pytest.mark.slow
    def test_wrong_gate_fails_kata_03(self) -> None:
        """Using X gate instead of H gate should fail kata 03."""
        code = (
            "import cirq\n"
            "q = cirq.LineQubit(0)\n"
            "circuit = cirq.Circuit([cirq.X(q), cirq.measure(q, key='result')])\n"
            "sim = cirq.Simulator()\n"
            "result = sim.run(circuit, repetitions=100)\n"
            "print(result)\n"
        )
        result = validate_submission("03-hadamard-gate", code)
        assert result.passed is False, "X gate instead of H should fail kata 03"

    @pytest.mark.slow
    def test_no_circuit_variable_fails(self) -> None:
        """Code that doesn't define 'circuit' should fail."""
        code = (
            "import cirq\n"
            "q = cirq.LineQubit(0)\n"
            "my_circ = cirq.Circuit([cirq.measure(q, key='result')])\n"
            "print('done')\n"
        )
        result = validate_submission("01-single-qubit", code)
        assert result.passed is False, "Code without 'circuit' variable should fail"

    @pytest.mark.slow
    def test_arbitrary_code_fails_kata_05(self) -> None:
        """Random correct-looking code for a different task should fail."""
        code = (
            "import cirq\nq = cirq.LineQubit(0)\ncircuit = cirq.Circuit([cirq.X(q), cirq.measure(q, key='result')])\n"
        )
        result = validate_submission("05-pauli-z-gate", code)
        assert result.passed is False, "X gate alone should fail kata 05 (needs HZH)"


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

    def test_dunder_class_blocked(self) -> None:
        """C-2 destructive test: object graph traversal via __class__ must be blocked."""
        code = "().__class__.__bases__[0].__subclasses__()"
        result = validate_submission("01-single-qubit", code)
        assert result.passed is False
        assert "blocked" in (result.message or "").lower() or result.passed is False

    def test_dunder_globals_blocked(self) -> None:
        """C-2 destructive test: __globals__ access must be blocked."""
        code = "print.__init__.__globals__"
        result = validate_submission("01-single-qubit", code)
        assert result.passed is False

    def test_wrap_close_blocked(self) -> None:
        """C-2 destructive test: _wrap_close escape path must be blocked."""
        code = "''.__class__.__mro__"
        result = validate_submission("01-single-qubit", code)
        assert result.passed is False
