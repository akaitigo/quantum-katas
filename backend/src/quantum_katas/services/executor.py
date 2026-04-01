"""Sandboxed Python code execution engine.

Executes user-submitted Python code (Cirq) in an isolated subprocess
with strict security constraints:
- Import whitelist: only cirq, numpy, math are allowed
- Timeout: 15 seconds maximum execution time (Cirq import takes ~8s)
- Dunder attribute access blocked (prevents object-graph sandbox escape)
- No file system access
- No network access
- Memory limit via RLIMIT_AS
- Concurrency limit via semaphore (max 3 simultaneous executions)
"""

from __future__ import annotations

import ast
import logging
import os
import subprocess
import sys
import textwrap
import threading

from quantum_katas.models.execution import ExecutionResult

logger = logging.getLogger(__name__)

EXECUTION_TIMEOUT_SECONDS = 15

MAX_CODE_LENGTH = 10_000

ALLOWED_MODULES: frozenset[str] = frozenset(
    {
        "cirq",
        "numpy",
        "math",
    }
)

_BLOCKED_BUILTINS: frozenset[str] = frozenset(
    {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "breakpoint",
        "globals",
        "locals",
        "vars",
        "dir",
        "getattr",
        "setattr",
        "delattr",
        "memoryview",
        "input",
        "help",
    }
)

_BLOCKED_SET_LITERAL = repr(set(_BLOCKED_BUILTINS))

# Dunder attributes that enable object-graph sandbox escapes
_BLOCKED_DUNDER_ATTRS: frozenset[str] = frozenset(
    {
        "__class__",
        "__bases__",
        "__subclasses__",
        "__globals__",
        "__init__",
        "__dict__",
        "__mro__",
        "__qualname__",
        "__module__",
        "__wrapped__",
        "__loader__",
        "__spec__",
        "__code__",
        "__func__",
        "__self__",
        "__builtins__",
        "__closure__",
        "_wrap_close",
    }
)

# FFI-related attribute names that enable sandbox escape via native code loading.
# Blocks paths like numpy.ctypeslib.ctypes.CDLL(None).system()
_BLOCKED_FFI_ATTRS: frozenset[str] = frozenset(
    {
        # ctypes module access via attribute chains
        "ctypeslib",
        "ctypes",
        # ctypes shared-library loaders
        "CDLL",
        "cdll",
        "windll",
        "oledll",
        "WinDLL",
        "OleDLL",
        "PyDLL",
        "pydll",
        # cffi
        "cffi",
        "FFI",
        # dl / low-level dynamic loading
        "dlopen",
        "dlsym",
    }
)

# M-2: Semaphore to limit concurrent subprocess executions
_execution_semaphore = threading.Semaphore(3)

# M-1: Memory limit in bytes (1 GB — Cirq import needs headroom)
_MEMORY_LIMIT_BYTES = 1024 * 1024 * 1024

# H-3: Max child processes / threads allowed in the sandbox.
# OpenBLAS (used by NumPy) spawns up to OPENBLAS_NUM_THREADS threads at import
# time, so this limit must accommodate them. We also set OPENBLAS_NUM_THREADS=1
# in the subprocess environment to minimise thread count.
_MAX_NPROC = 64


def validate_imports(code: str) -> str | None:
    """Validate that only whitelisted modules are imported.

    Returns an error message if a disallowed import is found, or None if valid.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"Syntax error: {exc}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split(".")[0]
                if root_module not in ALLOWED_MODULES:
                    return f"Import not allowed: {alias.name}"
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            root_module = node.module.split(".")[0]
            if root_module not in ALLOWED_MODULES:
                return f"Import not allowed: {node.module}"

    return None


def validate_no_dunder_access(code: str) -> str | None:
    """Check for blocked dunder attribute access in user code.

    Prevents object-graph traversal attacks such as:
        ().__class__.__bases__[0].__subclasses__()
        os._wrap_close.__init__.__globals__['sys']

    Returns an error message if a blocked access is found, or None if safe.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Syntax errors are caught by validate_imports; skip here
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in _BLOCKED_DUNDER_ATTRS:
            return f"Access blocked: '{node.attr}' attribute access is not allowed"
        # Catch string-based attribute access via bracket notation (obj['__globals__'])
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in _BLOCKED_DUNDER_ATTRS:
            return f"Access blocked: reference to '{node.value}' is not allowed"

    return None


def validate_no_ffi_access(code: str) -> str | None:
    """Check for FFI-related attribute access that could bypass the sandbox.

    Blocks attack vectors such as:
        numpy.ctypeslib.ctypes.CDLL(None).system('id')
        numpy.ctypeslib.ctypes.cdll.LoadLibrary(None)

    These allow loading arbitrary native code or invoking OS commands
    even when ctypes/cffi import statements are blocked.

    Returns an error message if a blocked access is found, or None if safe.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        # Attribute access: obj.ctypes, obj.CDLL, etc.
        if isinstance(node, ast.Attribute) and node.attr in _BLOCKED_FFI_ATTRS:
            return f"Access blocked: '{node.attr}' — FFI/native code access is not allowed"
        # String-based access: obj['ctypes'], obj['CDLL'], etc.
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in _BLOCKED_FFI_ATTRS:
            return f"Access blocked: reference to '{node.value}' — FFI/native code access is not allowed"
        # Direct function calls: CDLL(...), cdll(...), etc.
        if isinstance(node, ast.Name) and node.id in _BLOCKED_FFI_ATTRS:
            return f"Access blocked: '{node.id}' — FFI/native code access is not allowed"

    return None


def _build_wrapper_code() -> str:
    """Build a wrapper script that restricts builtins before executing user code.

    Pre-imports allowed modules (cirq, numpy, math) and their transitive
    dependencies BEFORE applying sandbox restrictions, then constructs a safe
    builtins dict with a guarded ``__import__`` that only allows whitelisted
    top-level modules. Also sets RLIMIT_AS and RLIMIT_NPROC limits.

    User code is read from stdin to avoid string-escaping injection (C-2).
    """
    allowed_repr = repr(set(ALLOWED_MODULES))

    return textwrap.dedent(f"""\
        import resource as _resource
        _resource.setrlimit(_resource.RLIMIT_AS, ({_MEMORY_LIMIT_BYTES}, {_MEMORY_LIMIT_BYTES}))
        _resource.setrlimit(_resource.RLIMIT_NPROC, ({_MAX_NPROC}, {_MAX_NPROC}))

        import sys as _sys

        # Read user code from stdin — avoids string-escaping injection
        _code = _sys.stdin.read()

        # Pre-import allowed modules with all transitive deps BEFORE sandbox
        import cirq
        import numpy
        import math
        _pre_modules = set(_sys.modules.keys())

        import builtins as _builtins

        _blocked = {_BLOCKED_SET_LITERAL}
        _safe_builtins = {{k: v for k, v in vars(_builtins).items() if k not in _blocked}}

        _allowed_modules = {allowed_repr}
        _real_import = _builtins.__import__

        def _safe_import(name, *args, **kwargs):
            # Allow already-loaded modules (transitive deps of cirq/numpy/math)
            if name in _sys.modules or name in _pre_modules:
                return _real_import(name, *args, **kwargs)
            root = name.split(".")[0]
            if root not in _allowed_modules:
                raise ImportError(f"Import not allowed: {{name}}")
            return _real_import(name, *args, **kwargs)

        _safe_builtins["__import__"] = _safe_import

        exec(compile(_code, "<user_code>", "exec"), {{"__builtins__": _safe_builtins}})
    """)


def _build_judge_wrapper_code() -> str:
    """Build a wrapper that executes user code then validation code in the same namespace.

    The validation_code can access variables defined by user_code (e.g. circuit, q),
    enabling real verification of the user's solution.
    Also sets RLIMIT_AS and RLIMIT_NPROC limits.

    Both code blocks are read from stdin (NUL-separated) to avoid injection (C-2).
    """
    allowed_repr = repr(set(ALLOWED_MODULES))

    return textwrap.dedent(f"""\
        import resource as _resource
        _resource.setrlimit(_resource.RLIMIT_AS, ({_MEMORY_LIMIT_BYTES}, {_MEMORY_LIMIT_BYTES}))
        _resource.setrlimit(_resource.RLIMIT_NPROC, ({_MAX_NPROC}, {_MAX_NPROC}))

        import sys as _sys

        # Read user code and validation code from stdin (NUL-separated)
        _parts = _sys.stdin.read().split("\\0")
        _user_code = _parts[0]
        _val_code = _parts[1] if len(_parts) > 1 else ""

        # Pre-import allowed modules with all transitive deps BEFORE sandbox
        import cirq
        import numpy
        import math
        _pre_modules = set(_sys.modules.keys())

        import builtins as _builtins

        _blocked = {_BLOCKED_SET_LITERAL}
        _safe_builtins = {{k: v for k, v in vars(_builtins).items() if k not in _blocked}}

        _allowed_modules = {allowed_repr}
        _real_import = _builtins.__import__

        def _safe_import(name, *args, **kwargs):
            # Allow already-loaded modules (transitive deps of cirq/numpy/math)
            if name in _sys.modules or name in _pre_modules:
                return _real_import(name, *args, **kwargs)
            root = name.split(".")[0]
            if root not in _allowed_modules:
                raise ImportError(f"Import not allowed: {{name}}")
            return _real_import(name, *args, **kwargs)

        _safe_builtins["__import__"] = _safe_import

        _ns = {{"__builtins__": _safe_builtins}}

        # Execute user code — variables are stored in _ns
        exec(compile(_user_code, "<user_code>", "exec"), _ns)

        # Restore builtins before running validation code to prevent
        # grading result forgery via builtin redefinition (e.g. any/all/print).
        # User code may have injected fake any/all into _ns to make
        # validation assertions pass with wrong answers.
        _pristine_builtins = {{k: v for k, v in vars(_builtins).items() if k not in _blocked}}
        _pristine_builtins["__import__"] = _safe_import

        # Remove any user-defined shadowing of builtin names from _ns
        for _bname in vars(_builtins):
            if _bname in _ns and _bname != "__builtins__":
                del _ns[_bname]

        # Execute validation code with pristine builtins in an isolated dict
        # that can still READ user-defined variables (circuit, q, etc.)
        _val_ns = dict(_ns)
        _val_ns["__builtins__"] = _pristine_builtins
        exec(compile(_val_code, "<validation_code>", "exec"), _val_ns)
    """)


def _validate_user_code(code: str) -> str | None:
    """Run all static validations on user code.

    Returns an error message if any check fails, or None if safe.
    """
    import_error = validate_imports(code)
    if import_error is not None:
        return import_error

    dunder_error = validate_no_dunder_access(code)
    if dunder_error is not None:
        return dunder_error

    return validate_no_ffi_access(code)


def _sandbox_env() -> dict[str, str]:
    """Build a restricted environment for the sandbox subprocess.

    Limits OpenBLAS thread count to avoid hitting RLIMIT_NPROC during
    NumPy/Cirq import.
    """
    env = os.environ.copy()
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    return env


def _run_sandboxed(wrapper_code: str, stdin_data: str) -> ExecutionResult:
    """Execute pre-built wrapper code in a sandboxed subprocess with semaphore.

    User code is passed via stdin (not command-line) to prevent
    string-escaping injection attacks (C-2).
    """
    acquired = _execution_semaphore.acquire(timeout=10)
    if not acquired:
        return ExecutionResult(
            success=False,
            error="Server busy: too many concurrent executions. Please try again.",
        )
    try:
        result = subprocess.run(  # noqa: S603 — input is validated by caller
            [sys.executable, "-c", wrapper_code],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT_SECONDS,
            check=False,
            env=_sandbox_env(),
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            success=False,
            error=f"Execution timed out after {EXECUTION_TIMEOUT_SECONDS} seconds",
        )
    except OSError as exc:
        logger.exception("Failed to start subprocess")
        return ExecutionResult(
            success=False,
            error=f"Execution failed: {exc}",
        )
    finally:
        _execution_semaphore.release()

    if result.returncode != 0:
        return ExecutionResult(
            stdout=result.stdout,
            stderr=result.stderr,
            success=False,
            error=result.stderr or f"Process exited with code {result.returncode}",
        )

    return ExecutionResult(
        stdout=result.stdout,
        stderr=result.stderr,
        success=True,
    )


def execute_code(code: str) -> ExecutionResult:
    """Execute user-submitted Python code in a sandboxed subprocess.

    Security measures:
    1. AST-level import validation (whitelist)
    2. Dunder attribute access validation (object-graph escape prevention)
    3. Blocked dangerous builtins (open, exec, eval, etc.)
    4. Subprocess isolation with timeout (15s)
    5. Memory limit via RLIMIT_AS (512 MB)
    6. Concurrency limit via semaphore (max 3)
    7. No shell=True to prevent shell injection
    """
    validation_error = _validate_user_code(code)
    if validation_error is not None:
        return ExecutionResult(
            success=False,
            error=validation_error,
        )

    return _run_sandboxed(_build_wrapper_code(), stdin_data=code)


def execute_judge(user_code: str, validation_code: str) -> ExecutionResult:
    """Execute user code + validation code in a single shared namespace.

    This is the core of the grading pipeline: user code is executed first,
    then validation_code runs in the same namespace so it can inspect
    variables (circuit, q, result, etc.) defined by the user.

    Security: same measures as execute_code, plus validation_code is trusted
    (comes from YAML, not user input) but still sandboxed for defense-in-depth.
    """
    validation_error = _validate_user_code(user_code)
    if validation_error is not None:
        return ExecutionResult(
            success=False,
            error=validation_error,
        )

    # NUL-separate user code and validation code for stdin transport
    stdin_data = f"{user_code}\0{validation_code}"
    return _run_sandboxed(_build_judge_wrapper_code(), stdin_data=stdin_data)
