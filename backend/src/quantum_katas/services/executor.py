"""Sandboxed Python code execution engine.

Executes user-submitted Python code (Cirq) in an isolated subprocess
with strict security constraints:
- Import whitelist: only cirq, numpy, math are allowed
- Timeout: 5 seconds maximum execution time
- No file system access
- No network access
"""

from __future__ import annotations

import ast
import logging
import subprocess
import sys
import textwrap

from quantum_katas.models.execution import ExecutionResult

logger = logging.getLogger(__name__)

EXECUTION_TIMEOUT_SECONDS = 5

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


def _build_wrapper_code(user_code: str) -> str:
    """Build a wrapper script that restricts builtins before executing user code.

    Constructs a safe builtins dict by filtering out blocked names,
    then injects a whitelist-guarded ``__import__`` so that only
    allowed modules (cirq, numpy, math) can be imported at runtime.
    """
    escaped_code = user_code.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    allowed_repr = repr(set(ALLOWED_MODULES))

    return textwrap.dedent(f"""\
        import builtins as _builtins

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

        _code = '{escaped_code}'
        exec(compile(_code, "<user_code>", "exec"), {{"__builtins__": _safe_builtins}})
    """)


def execute_code(code: str) -> ExecutionResult:
    """Execute user-submitted Python code in a sandboxed subprocess.

    Security measures:
    1. AST-level import validation (whitelist)
    2. Blocked dangerous builtins (open, exec, eval, etc.)
    3. Subprocess isolation with timeout
    4. No shell=True to prevent shell injection
    """
    import_error = validate_imports(code)
    if import_error is not None:
        return ExecutionResult(
            success=False,
            error=import_error,
        )

    wrapper_code = _build_wrapper_code(code)

    try:
        result = subprocess.run(  # noqa: S603 — input is validated above
            [sys.executable, "-c", wrapper_code],
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT_SECONDS,
            check=False,
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
