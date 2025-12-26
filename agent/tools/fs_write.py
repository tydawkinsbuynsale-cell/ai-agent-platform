from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel, Field

from agent.tools.base import ToolExecutionError, ToolSpec


class AppendTextIn(BaseModel):
    path: str = Field(..., description="Target file path")
    text: str = Field(..., description="Text to append (newline added automatically)")
    max_chars: int = Field(5000, ge=1, le=20000)


class AppendTextOut(BaseModel):
    path: str
    appended_chars: int


def _append_text_handler(inp: AppendTextIn) -> AppendTextOut:
    p = Path(inp.path)

    if p.exists() and p.is_dir():
        raise ToolExecutionError("Target path is a directory")

    text = inp.text[: inp.max_chars]
    p.parent.mkdir(parents=True, exist_ok=True)

    with p.open("a", encoding="utf-8") as f:
        f.write(text + "\n")

    return AppendTextOut(path=str(p), appended_chars=len(text))


APPEND_TEXT_TOOL = ToolSpec(
    name="fs.append_text",
    description="Append text to a file (safe, append-only).",
    input_model=AppendTextIn,
    output_model=AppendTextOut,
    handler=_append_text_handler,
)
