from __future__ import annotations

import subprocess
from pydantic import BaseModel, Field

from .base import ToolExecutionError, ToolSpec


class RunLinterIn(BaseModel):
    command: str = Field(..., description="Linter command to run (e.g. 'ruff .')")
    timeout_sec: int = Field(120, ge=1, le=600, description="Timeout in seconds")


class RunLinterOut(BaseModel):
    clean: bool
    stdout: str
    stderr: str
    exit_code: int


def _run_linter_handler(inp: RunLinterIn) -> RunLinterOut:
    try:
        result = subprocess.run(
            inp.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=inp.timeout_sec
        )
        return RunLinterOut(
            clean=(result.returncode == 0),
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    except subprocess.TimeoutExpired as e:
        raise ToolExecutionError(f"Linter timed out after {inp.timeout_sec}s") from e
    except Exception as e:
        raise ToolExecutionError(f"Failed to run linter: {e}") from e


RUN_LINTER_TOOL = ToolSpec(
    name="dev.run_linter",
    description="Run linter with configurable timeout",
    input_model=RunLinterIn,
    output_model=RunLinterOut,
    handler=_run_linter_handler
)
