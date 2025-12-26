from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel, Field

from .base import ToolExecutionError, ToolSpec


class ReadTextIn(BaseModel):
    path: str = Field(..., description="Relative or absolute path to a UTF-8 text file")
    max_chars: int = Field(12000, ge=1, le=200000, description="Safety limit")


class ReadTextOut(BaseModel):
    path: str
    content: str
    truncated: bool


def _read_text_handler(inp: ReadTextIn) -> ReadTextOut:
    p = Path(inp.path).expanduser()

    if not p.exists():
        raise ToolExecutionError(f"File not found: {p}")
    if p.is_dir():
        raise ToolExecutionError(f"Path is a directory, not a file: {p}")

    data = p.read_text(encoding="utf-8", errors="replace")
    truncated = False
    if len(data) > inp.max_chars:
        data = data[: inp.max_chars]
        truncated = True

    return ReadTextOut(path=str(p), content=data, truncated=truncated)


READ_TEXT_TOOL = ToolSpec(
    name="fs.read_text",
    description="Read a UTF-8 text file from disk (with a max character limit).",
    input_model=ReadTextIn,
    output_model=ReadTextOut,
    handler=_read_text_handler,
)
