from __future__ import annotations

from agent.tools.base import ToolRegistry
from agent.tools.fs import READ_TEXT_TOOL
from agent.tools.fs_write import APPEND_TEXT_TOOL
from agent.tools.fs_patch import APPLY_PATCH_TOOL
from agent.tools.memory import READ_PROJECT_FACTS_TOOL, APPEND_DECISION_TOOL
from agent.tools.run_tests import RUN_TESTS_TOOL
from agent.tools.run_linter import RUN_LINTER_TOOL
from agent.tools.memory_hygiene import MEMORY_HYGIENE_TOOL


def build_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(READ_TEXT_TOOL)
    reg.register(APPEND_TEXT_TOOL)
    reg.register(APPLY_PATCH_TOOL)
    reg.register(READ_PROJECT_FACTS_TOOL)
    reg.register(APPEND_DECISION_TOOL)
    reg.register(RUN_TESTS_TOOL)
    reg.register(RUN_LINTER_TOOL)
    reg.register(MEMORY_HYGIENE_TOOL)
    return reg
