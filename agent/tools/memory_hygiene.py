from __future__ import annotations

from pydantic import BaseModel
from agent.core.memory_hygiene import summarize_and_prune_decisions
from agent.tools.base import ToolSpec


class HygieneIn(BaseModel):
    pass


class HygieneOut(BaseModel):
    changed: bool
    reason: str | None = None
    pruned_count: int | None = None
    kept_count: int | None = None
    decisions_chars: int | None = None


def _handler(_: HygieneIn) -> HygieneOut:
    res = summarize_and_prune_decisions()
    return HygieneOut(**res)


MEMORY_HYGIENE_TOOL = ToolSpec(
    name="memory.hygiene",
    description="Summarize and prune decisions.md to keep memory bounded.",
    input_model=HygieneIn,
    output_model=HygieneOut,
    handler=_handler,
)
