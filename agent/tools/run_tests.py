from __future__ import annotations

import subprocess
from pydantic import BaseModel, Field

from .base import ToolExecutionError, ToolSpec


class RunTestsIn(BaseModel):
    command: str = Field(..., description="Test command to run (e.g. 'pytest -q')")
    timeout_sec: int = Field(300, ge=1, le=3600, description="Timeout in seconds")


class RunTestsOut(BaseModel):
    passed: bool
    stdout: str
    stderr: str
    exit_code: int


def _run_tests_handler(inp: RunTestsIn) -> RunTestsOut:
    try:
        result = subprocess.run(
            inp.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=inp.timeout_sec
        )
        return RunTestsOut(
            passed=(result.returncode == 0),
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    except subprocess.TimeoutExpired as e:
        raise ToolExecutionError(f"Tests timed out after {inp.timeout_sec}s") from e
    except Exception as e:
        raise ToolExecutionError(f"Failed to run tests: {e}") from e


RUN_TESTS_TOOL = ToolSpec(
    name="dev.run_tests",
    description="Run test suite with configurable timeout",
    input_model=RunTestsIn,
    output_model=RunTestsOut,
    handler=_run_tests_handler
)
