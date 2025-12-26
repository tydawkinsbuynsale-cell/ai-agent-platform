from __future__ import annotations

import json
from agent.registry import build_registry
from agent.core.agent_loop import Agent, AgentMode


# NOTE:
# This test intentionally calls the registry directly to demonstrate that
# mode enforcement lives in the Agent loop, not in the ToolRegistry.


def main():
    reg = build_registry()

    builder = Agent(reg, AgentMode.BUILDER)
    reviewer = Agent(reg, AgentMode.REVIEWER)

    # Builder can write
    builder_result = reg.call(
        "fs.append_text",
        {"path": "docs/agent_notes.md", "text": "Builder mode write test"},
    )
    print("BUILDER WRITE:", builder_result)

    # Reviewer cannot write (simulated via agent loop gate)
    try:
        reviewer_result = reg.call(
            "fs.append_text",
            {"path": "docs/agent_notes.md", "text": "Reviewer should fail"},
        )
        print("REVIEWER WRITE (unexpected):", reviewer_result)
    except Exception as e:
        print("REVIEWER BLOCKED:", str(e))


if __name__ == "__main__":
    main()
