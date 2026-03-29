"""Tests for the code execution engine."""

import pytest

from quantum_katas.services.executor import (
    ALLOWED_MODULES,
    execute_code,
    validate_imports,
    validate_no_dunder_access,
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


class TestValidateDunderAccess:
    """Tests for dunder attribute access validation (C-2)."""

    def test_class_access_blocked(self):
        result = validate_no_dunder_access("().__class__")
        assert result is not None
        assert "blocked" in result.lower()

    def test_bases_access_blocked(self):
        result = validate_no_dunder_access("x.__bases__")
        assert result is not None
        assert "blocked" in result.lower()

    def test_subclasses_access_blocked(self):
        result = validate_no_dunder_access("x.__subclasses__()")
        assert result is not None
        assert "blocked" in result.lower()

    def test_globals_access_blocked(self):
        result = validate_no_dunder_access("f.__globals__")
        assert result is not None
        assert "blocked" in result.lower()

    def test_init_access_blocked(self):
        result = validate_no_dunder_access("x.__init__")
        assert result is not None
        assert "blocked" in result.lower()

    def test_dict_access_blocked(self):
        result = validate_no_dunder_access("x.__dict__")
        assert result is not None
        assert "blocked" in result.lower()

    def test_mro_access_blocked(self):
        result = validate_no_dunder_access("x.__mro__")
        assert result is not None
        assert "blocked" in result.lower()

    def test_wrap_close_string_blocked(self):
        result = validate_no_dunder_access("x['_wrap_close']")
        assert result is not None
        assert "blocked" in result.lower()

    def test_globals_string_blocked(self):
        result = validate_no_dunder_access("x['__globals__']")
        assert result is not None
        assert "blocked" in result.lower()

    def test_full_escape_chain_blocked(self):
        """The complete object-graph escape chain must be blocked."""
        code = "().__class__.__bases__[0].__subclasses__()"
        result = validate_no_dunder_access(code)
        assert result is not None

    def test_safe_code_passes(self):
        result = validate_no_dunder_access("x = 1 + 2\nprint(x)")
        assert result is None

    def test_cirq_code_passes(self):
        code = "import cirq\nq = cirq.LineQubit(0)\ncircuit = cirq.Circuit([cirq.H(q)])"
        result = validate_no_dunder_access(code)
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

    def test_multiline_output(self):
        result = execute_code("print('line1')\nprint('line2')")
        assert result.success is True
        assert "line1" in result.stdout
        assert "line2" in result.stdout

    def test_empty_output(self):
        result = execute_code("x = 42")
        assert result.success is True
        assert result.stdout == ""

    def test_dunder_class_blocked(self):
        """C-2: Object-graph sandbox escape must be blocked."""
        result = execute_code("().__class__.__bases__[0].__subclasses__()")
        assert result.success is False
        assert "blocked" in (result.error or "").lower()

    def test_dunder_globals_blocked(self):
        result = execute_code("print.__init__.__globals__['sys']")
        assert result.success is False
        assert "blocked" in (result.error or "").lower()

    def test_wrap_close_escape_blocked(self):
        result = execute_code("x = ''.__class__.__mro__[1].__subclasses__()")
        assert result.success is False
        assert "blocked" in (result.error or "").lower()


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

    def test_execute_dunder_blocked(self, client):
        """C-2 via API: sandbox escape attempt must be blocked."""
        response = client.post(
            "/api/execute",
            json={"code": "().__class__.__bases__[0].__subclasses__()"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "blocked" in data["error"].lower()
