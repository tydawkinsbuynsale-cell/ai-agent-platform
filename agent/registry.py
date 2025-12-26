from __future__ import annotations

from agent.tools.base import ToolRegistry
from agent.tools.fs import READ_TEXT_TOOL
from agent.tools.fs_write import APPEND_TEXT_TOOL
from agent.tools.fs_patch import APPLY_PATCH_TOOL
from agent.tools.memory import READ_PROJECT_FACTS_TOOL, APPEND_DECISION_TOOL


def build_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(READ_TEXT_TOOL)
    reg.register(APPEND_TEXT_TOOL)
    reg.register(APPLY_PATCH_TOOL)
    reg.register(READ_PROJECT_FACTS_TOOL)
    reg.register(APPEND_DECISION_TOOL)
    return reg
