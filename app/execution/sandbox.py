# app/execution/sandbox.py

import ast
import logging
from typing import Any

logger = logging.getLogger(__name__)


class PythonSandbox:

    FORBIDDEN_MODULES = {
        "os",
        "sys",
        "subprocess",
        "socket",
        "shutil",
        "pathlib",
        "multiprocessing",
        "threading",
    }

    FORBIDDEN_FUNCTIONS = {
        "eval",
        "exec",
        "compile",
        "open",
        "input",
    }

    SAFE_BUILTINS = {
        "range": range,
        "len": len,
        "print": print,
        "str": str,
        "int": int,
        "float": float,
        "list": list,
        "dict": dict,
        "set": set,
        "min": min,
        "max": max,
        "sum": sum,
        "abs": abs,
        "enumerate": enumerate,
        "__import__": __import__,
        "any": Any,
        "tuple": tuple,
        "set": set,
        "frozenset": frozenset,
        "bool": bool,
        "int": int,
        "complex": complex,
        "bytes": bytes,
        "bytearray": bytearray,
        "memoryview": memoryview,
        "range": range,
        "len": len,
        "print": print,
    }

    # =========================================================
    # PUBLIC API
    # =========================================================

    def execute(self, code: str) -> dict[str, Any]:
        # Executes user code inside a controlled environment.
        # Returns the execution locals.

        logger.debug("Validating AST security")

        self._validate_ast(code)

        local_env: dict[str, Any] = {}

        safe_builtins = dict(self.SAFE_BUILTINS)
        safe_builtins["__import__"] = self._safe_import

        safe_globals = {"__builtins__": safe_builtins}

        exec(code, safe_globals, local_env)

        return local_env

    # =========================================================
    # AST SECURITY
    # =========================================================

    def _validate_ast(self, code: str):

        tree = ast.parse(code)

        for node in ast.walk(tree):

            # Block dangerous imports
            if isinstance(node, ast.Import):

                for alias in node.names:

                    module = alias.name.split(".")[0]

                    if module in self.FORBIDDEN_MODULES:
                        raise RuntimeError(
                            f"Import of module '{module}' is not allowed"
                        )

            if isinstance(node, ast.ImportFrom):

                if node.module:

                    module = node.module.split(".")[0]

                    if module in self.FORBIDDEN_MODULES:
                        raise RuntimeError(
                            f"Import from module '{module}' is not allowed"
                        )

            # Block dangerous functions
            if isinstance(node, ast.Call):

                if isinstance(node.func, ast.Name):

                    if node.func.id in self.FORBIDDEN_FUNCTIONS:
                        raise RuntimeError(f"Use of '{node.func.id}' is not allowed")


    # =========================================================
    # SAFE IMPORT
    # =========================================================
    def _safe_import(self, name, globals=None, locals=None, fromlist=(), level=0):

        root_module = name.split(".")[0]

        if root_module in self.FORBIDDEN_MODULES:
            raise ImportError(f"Import of module '{root_module}' is not allowed")

        return __import__(name, globals, locals, fromlist, level)