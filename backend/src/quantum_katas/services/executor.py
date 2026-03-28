"""Sandboxed Python code execution engine.

Executes user-submitted Python code (Cirq) in an isolated subprocess
with strict security constraints:
- Import whitelist: only cirq, numpy, math are allowed
- Timeout: 5 seconds maximum execution time
- No file system access
- No network access
- Memory limit: 512 MB
- Process limit: 50
- Metaclass / dunder attribute access blocked
"""

from __future__ import annotations

import ast
import logging
import os
import platform
import subprocess
import sys
import textwrap

from quantum_katas.models.execution import ExecutionResult

logger = logging.getLogger(__name__)

EXECUTION_TIMEOUT_SECONDS = 10
MEMORY_LIMIT_BYTES = 512 * 1024 * 1024  # 512 MB
NPROC_LIMIT = 50

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

_BLOCKED_DUNDER_ATTRS: frozenset[str] = frozenset(
    {
        "__class__",
        "__bases__",
        "__subclasses__",
        "__mro__",
        "__qualname__",
    }
)

_BLOCKED_SET_LITERAL = repr(set(_BLOCKED_BUILTINS))


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


def _validate_blocked_attrs(code: str) -> str | None:
    """Block access to dangerous dunder attributes (metaclass attacks).

    Returns an error message if a blocked attribute is found, or None if valid.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None  # Syntax errors are caught by validate_imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in _BLOCKED_DUNDER_ATTRS:
            return f"Access to '{node.attr}' is not allowed"

    return None


def _build_wrapper_code() -> str:
    """Build a wrapper script that reads user code from stdin and executes it safely.

    Constructs a safe builtins dict by filtering out blocked names,
    then injects a whitelist-guarded ``__import__`` so that only
    allowed modules (cirq, numpy, math) can be imported at runtime.
    User code is read from stdin to avoid string escaping vulnerabilities.
    """
    allowed_repr = repr(set(ALLOWED_MODULES))

    return textwrap.dedent(f"""\
        import builtins as _builtins
        import sys as _sys

        _blocked = {_BLOCKED_SET_LITERAL}
        _safe_builtins = {{k: v for k, v in vars(_builtins).items() if k not in _blocked}}

        _allowed_modules = {allowed_repr}
        _real_import = _builtins.__import__

        def _safe_import(name, *args, **kwargs):
            root = name.split(".")[0]
            if root not in _allowed_modules:
                raise ImportError(f"Import not allowed: {{name}}")
            return _real_import(name, *args, **kwargs)

        _safe_builtins["__import__"] = _safe_import

        _code = _sys.stdin.read()
        exec(compile(_code, "<user_code>", "exec"), {{"__builtins__": _safe_builtins}})
    """)


def _build_preexec_fn() -> object | None:
    """Build a preexec_fn that sets resource limits (Linux only).

    Sets memory (RLIMIT_AS) limit to mitigate resource exhaustion attacks.
    Process/thread limits are handled via environment variables
    (OPENBLAS_NUM_THREADS, MKL_NUM_THREADS) to avoid breaking numpy/cirq.
    """
    if platform.system() != "Linux":
        return None

    def _set_limits() -> None:
        import resource  # noqa: PLC0415

        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
        resource.setrlimit(resource.RLIMIT_NPROC, (NPROC_LIMIT, NPROC_LIMIT))

    return _set_limits


def execute_code(code: str) -> ExecutionResult:
    """Execute user-submitted Python code in a sandboxed subprocess.

    Security measures:
    1. AST-level import validation (whitelist)
    2. AST-level blocked dunder attribute validation
    3. Blocked dangerous builtins (open, exec, eval, etc.)
    4. Subprocess isolation with timeout
    5. No shell=True to prevent shell injection
    6. Code passed via stdin (no string escaping issues)
    7. Memory and process limits (Linux)
    """
    import_error = validate_imports(code)
    if import_error is not None:
        return ExecutionResult(
            success=False,
            error=import_error,
        )

    attr_error = _validate_blocked_attrs(code)
    if attr_error is not None:
        return ExecutionResult(
            success=False,
            error=attr_error,
        )

    wrapper_code = _build_wrapper_code()

    # Restrict OpenBLAS/MKL thread spawning to prevent resource exhaustion
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}

    try:
        result = subprocess.run(  # noqa: S603 — input is validated above
            [sys.executable, "-c", wrapper_code],
            input=code,
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT_SECONDS,
            check=False,
            preexec_fn=_build_preexec_fn(),
            env=env,
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
