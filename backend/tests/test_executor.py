"""Tests for the code execution engine."""

import pytest

from quantum_katas.services.executor import (
    ALLOWED_MODULES,
    execute_code,
    execute_judge,
    validate_imports,
    validate_no_dunder_access,
    validate_no_ffi_access,
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


class TestValidateFFIAccess:
    """Tests for FFI/native-code access validation (sandbox bypass prevention)."""

    def test_ctypeslib_attribute_blocked(self):
        """numpy.ctypeslib access must be blocked."""
        result = validate_no_ffi_access("import numpy\nnumpy.ctypeslib")
        assert result is not None
        assert "ctypeslib" in result

    def test_ctypes_attribute_blocked(self):
        """ctypes attribute access via any chain must be blocked."""
        result = validate_no_ffi_access("x.ctypes.CDLL(None)")
        assert result is not None
        assert "ffi" in result.lower()

    def test_cdll_attribute_blocked(self):
        """CDLL attribute access must be blocked."""
        result = validate_no_ffi_access("x.CDLL(None)")
        assert result is not None
        assert "CDLL" in result

    def test_cdll_lowercase_blocked(self):
        """cdll attribute access must be blocked."""
        result = validate_no_ffi_access("x.cdll.LoadLibrary('libc.so.6')")
        assert result is not None
        assert "cdll" in result

    def test_windll_blocked(self):
        result = validate_no_ffi_access("x.windll")
        assert result is not None
        assert "windll" in result

    def test_oledll_blocked(self):
        result = validate_no_ffi_access("x.oledll")
        assert result is not None
        assert "oledll" in result

    def test_pydll_blocked(self):
        result = validate_no_ffi_access("x.PyDLL('libc.so.6')")
        assert result is not None
        assert "PyDLL" in result

    def test_cffi_attribute_blocked(self):
        result = validate_no_ffi_access("x.cffi.FFI()")
        assert result is not None
        assert "ffi" in result.lower()

    def test_ffi_class_blocked(self):
        result = validate_no_ffi_access("f = x.FFI()")
        assert result is not None
        assert "FFI" in result

    def test_dlopen_blocked(self):
        result = validate_no_ffi_access("x.dlopen('libc.so.6')")
        assert result is not None
        assert "dlopen" in result

    def test_full_ctypeslib_chain_blocked(self):
        """The full numpy.ctypeslib.ctypes.CDLL(None).system() chain must be blocked."""
        code = "import numpy\nnumpy.ctypeslib.ctypes.CDLL(None).system('id')"
        result = validate_no_ffi_access(code)
        assert result is not None

    def test_string_based_ctypes_access_blocked(self):
        """String-based attribute lookup for ctypes must be blocked."""
        result = validate_no_ffi_access("x['ctypes']")
        assert result is not None

    def test_string_based_cdll_access_blocked(self):
        """String-based attribute lookup for CDLL must be blocked."""
        result = validate_no_ffi_access("x['CDLL']")
        assert result is not None

    def test_safe_code_passes(self):
        """Normal code with no FFI access should pass."""
        result = validate_no_ffi_access("x = 1 + 2\nprint(x)")
        assert result is None

    def test_cirq_code_passes(self):
        """Cirq quantum circuit code should pass."""
        code = "import cirq\nq = cirq.LineQubit(0)\ncircuit = cirq.Circuit([cirq.H(q)])"
        result = validate_no_ffi_access(code)
        assert result is None

    def test_numpy_safe_operations_pass(self):
        """Normal numpy operations (array, linalg) should pass."""
        code = "import numpy as np\narr = np.array([1, 2, 3])\nprint(np.linalg.norm(arr))"
        result = validate_no_ffi_access(code)
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

    def test_ctypeslib_bypass_blocked(self):
        """P0 security: numpy.ctypeslib.ctypes.CDLL(None).system() must be blocked."""
        code = "import numpy\nnumpy.ctypeslib.ctypes.CDLL(None).system('id')"
        result = execute_code(code)
        assert result.success is False
        assert "blocked" in (result.error or "").lower()
        assert "ffi" in (result.error or "").lower() or "ctypeslib" in (result.error or "").lower()

    def test_ctypes_import_blocked(self):
        """Direct ctypes import must be blocked."""
        result = execute_code("import ctypes")
        assert result.success is False

    def test_cffi_import_blocked(self):
        """Direct cffi import must be blocked."""
        result = execute_code("import cffi")
        assert result.success is False

    def test_cdll_via_attribute_chain_blocked(self):
        """CDLL access via any attribute chain must be blocked."""
        code = "import numpy as np\nnp.ctypeslib.ctypes.CDLL(None)"
        result = execute_code(code)
        assert result.success is False
        assert "blocked" in (result.error or "").lower()


class TestJudgeBuiltinIsolation:
    """Tests for builtin isolation between user code and validation code.

    Ensures that user-defined shadowing of builtins (any, all, print, etc.)
    does not affect validation code execution.
    """

    def test_any_restored_for_validation(self):
        """User redefining any() must not affect validation code."""
        user_code = "any = lambda x: True\nx = 42"
        val_code = "assert any([False]) is False, 'any() was not restored'"
        result = execute_judge(user_code, val_code)
        assert result.success is True, f"Validation should use real any(): {result.error}"

    def test_all_restored_for_validation(self):
        """User redefining all() must not affect validation code."""
        user_code = "all = lambda x: True\nx = 42"
        val_code = "assert all([False]) is False, 'all() was not restored'"
        result = execute_judge(user_code, val_code)
        assert result.success is True, f"Validation should use real all(): {result.error}"

    def test_print_restored_for_validation(self):
        """User redefining print() must not affect validation code output."""
        user_code = "def print(*a, **k): pass\nx = 42"
        val_code = "print('PASSED')"
        result = execute_judge(user_code, val_code)
        assert result.success is True
        assert "PASSED" in result.stdout, "Validation print() should produce output"

    def test_user_variables_accessible_in_validation(self):
        """User-defined variables (non-builtin) must still be accessible."""
        user_code = "my_value = 42\nmy_list = [1, 2, 3]"
        val_code = "assert my_value == 42\nassert len(my_list) == 3\nprint('PASSED')"
        result = execute_judge(user_code, val_code)
        assert result.success is True
        assert "PASSED" in result.stdout

    def test_multiple_builtins_restored(self):
        """Multiple builtin overrides should all be restored."""
        user_code = "any = lambda x: True\nall = lambda x: True\nlen = lambda x: 999\nsum = lambda x: 0\nx = 42\n"
        val_code = (
            "assert any([False]) is False\n"
            "assert all([False]) is False\n"
            "assert len([1,2,3]) == 3\n"
            "assert sum([1,2,3]) == 6\n"
            "print('PASSED')\n"
        )
        result = execute_judge(user_code, val_code)
        assert result.success is True, f"All builtins should be restored: {result.error}"


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
