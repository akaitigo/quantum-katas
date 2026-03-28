"""Tests for the code execution engine."""

import pytest

from quantum_katas.services.executor import (
    ALLOWED_MODULES,
    _validate_blocked_attrs,
    execute_code,
    validate_imports,
)


class TestValidateImports:
    """Tests for import validation."""

    def test_allowed_import_cirq(self):
        assert validate_imports("import cirq") is None

    def test_allowed_import_numpy(self):
        assert validate_imports("import numpy") is None

    def test_allowed_import_math(self):
        assert validate_imports("import math") is None

    def test_allowed_from_import(self):
        assert validate_imports("from cirq import LineQubit") is None

    def test_allowed_submodule_import(self):
        assert validate_imports("import numpy.linalg") is None

    def test_disallowed_import_os(self):
        result = validate_imports("import os")
        assert result is not None
        assert "os" in result

    def test_disallowed_import_subprocess(self):
        result = validate_imports("import subprocess")
        assert result is not None
        assert "subprocess" in result

    def test_disallowed_from_import(self):
        result = validate_imports("from pathlib import Path")
        assert result is not None
        assert "pathlib" in result

    def test_disallowed_import_socket(self):
        result = validate_imports("import socket")
        assert result is not None

    def test_disallowed_import_sys(self):
        result = validate_imports("import sys")
        assert result is not None

    def test_syntax_error(self):
        result = validate_imports("def (invalid")
        assert result is not None
        assert "Syntax error" in result

    def test_no_imports(self):
        assert validate_imports("x = 1 + 2\nprint(x)") is None

    def test_allowed_modules_frozen(self):
        assert isinstance(ALLOWED_MODULES, frozenset)


class TestValidateBlockedAttrs:
    """Tests for blocked dunder attribute validation."""

    def test_class_attr_blocked(self):
        result = _validate_blocked_attrs("x = ''.__class__")
        assert result is not None
        assert "__class__" in result

    def test_bases_attr_blocked(self):
        result = _validate_blocked_attrs("x = str.__bases__")
        assert result is not None
        assert "__bases__" in result

    def test_subclasses_attr_blocked(self):
        result = _validate_blocked_attrs("x = object.__subclasses__()")
        assert result is not None
        assert "__subclasses__" in result

    def test_normal_attr_allowed(self):
        result = _validate_blocked_attrs("x = [1, 2, 3]\nprint(len(x))")
        assert result is None

    def test_syntax_error_returns_none(self):
        result = _validate_blocked_attrs("def (invalid")
        assert result is None


class TestExecuteCode:
    """Tests for code execution."""

    def test_simple_print(self):
        result = execute_code("print('hello quantum')")
        assert result.success is True
        assert "hello quantum" in result.stdout

    def test_math_operations(self):
        result = execute_code("import math\nprint(math.pi)")
        assert result.success is True
        assert "3.14" in result.stdout

    @pytest.mark.slow
    def test_cirq_basic_circuit(self):
        code = """\
import cirq

q = cirq.LineQubit(0)
circuit = cirq.Circuit([cirq.H(q), cirq.measure(q, key='result')])
print(circuit)
"""
        result = execute_code(code)
        assert result.success is True
        assert "H" in result.stdout

    @pytest.mark.slow
    def test_cirq_simulation(self):
        code = """\
import cirq

q = cirq.LineQubit(0)
circuit = cirq.Circuit([cirq.X(q), cirq.measure(q, key='m')])
sim = cirq.Simulator()
result = sim.run(circuit, repetitions=10)
print(result)
"""
        result = execute_code(code)
        assert result.success is True
        assert result.stdout.strip() != ""

    def test_disallowed_import_rejected(self):
        result = execute_code("import os\nos.listdir('.')")
        assert result.success is False
        assert result.error is not None
        assert "Import not allowed" in result.error

    def test_subprocess_import_rejected(self):
        result = execute_code("import subprocess\nsubprocess.run(['ls'])")
        assert result.success is False
        assert result.error is not None

    @pytest.mark.slow
    def test_timeout_on_infinite_loop(self):
        result = execute_code("while True: pass")
        assert result.success is False
        assert result.error is not None
        assert "timed out" in result.error

    def test_syntax_error_in_code(self):
        result = execute_code("def (invalid")
        assert result.success is False
        assert result.error is not None

    def test_runtime_error(self):
        result = execute_code("print(1 / 0)")
        assert result.success is False
        assert result.error is not None

    def test_open_builtin_blocked(self):
        code = "f = open('/etc/passwd', 'r')\nprint(f.read())"
        result = execute_code(code)
        assert result.success is False

    def test_metaclass_class_blocked(self):
        result = execute_code("x = ''.__class__")
        assert result.success is False
        assert result.error is not None
        assert "__class__" in result.error

    def test_metaclass_bases_blocked(self):
        result = execute_code("x = str.__bases__")
        assert result.success is False

    def test_metaclass_subclasses_blocked(self):
        result = execute_code("x = object.__subclasses__()")
        assert result.success is False

    def test_multiline_output(self):
        result = execute_code("print('line1')\nprint('line2')")
        assert result.success is True
        assert "line1" in result.stdout
        assert "line2" in result.stdout

    def test_empty_output(self):
        result = execute_code("x = 42")
        assert result.success is True
        assert result.stdout == ""


class TestExecuteEndpoint:
    """Tests for the /api/execute endpoint (integration)."""

    def test_execute_valid_code(self, client):
        response = client.post("/api/execute", json={"code": "print('hello')"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "hello" in data["stdout"]

    def test_execute_invalid_import(self, client):
        response = client.post("/api/execute", json={"code": "import os"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Import not allowed" in data["error"]

    def test_execute_empty_code(self, client):
        response = client.post("/api/execute", json={"code": ""})
        assert response.status_code == 422

    def test_execute_missing_code(self, client):
        response = client.post("/api/execute", json={})
        assert response.status_code == 422

    def test_execute_rate_limited(self, client):
        """Verify rate limiting returns 429 when limit is exceeded."""
        from quantum_katas.services.rate_limiter import rate_limiter  # noqa: PLC0415

        # Exhaust rate limit
        for _ in range(31):
            rate_limiter.is_allowed("testclient")

        response = client.post("/api/execute", json={"code": "print('test')"})
        assert response.status_code == 429

        # Reset for other tests by waiting (or just clearing internal state)
        rate_limiter._requests.clear()  # noqa: SLF001
