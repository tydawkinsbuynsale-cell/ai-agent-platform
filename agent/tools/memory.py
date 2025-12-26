from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Dict, Any

from agent.core.memory_store import MemoryStore
from agent.tools.base import ToolSpec


# ---------- Read project facts ----------

class ReadFactsIn(BaseModel):
    pass


class ReadFactsOut(BaseModel):
    data: Dict[str, Any]


def _read_facts_handler(_: ReadFactsIn) -> ReadFactsOut:
    mem = MemoryStore()
    data = mem.read_project_facts()
    return ReadFactsOut(data=data)


READ_PROJECT_FACTS_TOOL = ToolSpec(
    name="memory.read_project_facts",
    description="Read persistent project facts from disk.",
    input_model=ReadFactsIn,
    output_model=ReadFactsOut,
    handler=_read_facts_handler,
)

# ---------- Append decision ----------

class AppendDecisionIn(BaseModel):
    title: str = Field(..., description="Decision title with date")
    body: str = Field(..., description="Decision rationale and details")


class AppendDecisionOut(BaseModel):
    success: bool


def _append_decision_handler(inp: AppendDecisionIn) -> AppendDecisionOut:
    mem = MemoryStore()
    mem.append_decision(inp.title, inp.body)
    return AppendDecisionOut(success=True)


APPEND_DECISION_TOOL = ToolSpec(
    name="memory.append_decision",
    description="Append a design or implementation decision to decisions.md",
    input_model=AppendDecisionIn,
    output_model=AppendDecisionOut,
    handler=_append_decision_handler,
)

