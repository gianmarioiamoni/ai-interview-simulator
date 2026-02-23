# services/coding_engine/execution_sandbox.py

# ExecutionSandbox
#
# Responsibility:
# Executes arbitrary Python code in an isolated subprocess.
# Provides timeout control and captures raw execution output.
# Does not contain domain logic.

import subprocess
import tempfile
import time
from pathlib import Path


class SandboxExecutionOutput:
    def __init__(
        self,
        returncode: int,
        stdout: str,
        stderr: str,
        execution_time_ms: int,
        timeout: bool = False,
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time_ms = execution_time_ms
        self.timeout = timeout


class ExecutionSandbox:
    def __init__(self, timeout_seconds: int = 5) -> None:
        self._timeout_seconds = timeout_seconds

    def execute(self, code: str) -> SandboxExecutionOutput:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "user_code.py"
            file_path.write_text(code)

            start = time.perf_counter()

            try:
                result = subprocess.run(
                    ["python", str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=self._timeout_seconds,
                )

                end = time.perf_counter()

                return SandboxExecutionOutput(
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    execution_time_ms=int((end - start) * 1000),
                )

            except subprocess.TimeoutExpired as e:
                end = time.perf_counter()

                return SandboxExecutionOutput(
                    returncode=-1,
                    stdout=e.stdout or "",
                    stderr="Execution timed out",
                    execution_time_ms=int((end - start) * 1000),
                    timeout=True,
                )

            except Exception as e:
                end = time.perf_counter()

                return SandboxExecutionOutput(
                    returncode=-2,
                    stdout="",
                    stderr=str(e),
                    execution_time_ms=int((end - start) * 1000),
                )
