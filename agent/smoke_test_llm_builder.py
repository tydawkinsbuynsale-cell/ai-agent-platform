from __future__ import annotations

import json

from agent._fixtures import write_fixture
from agent.registry import build_registry
from agent.core.agent_loop import AgentMode
from agent.core.production_agent import ProductionAgent


def main():
    # Reset file to deterministic state every run
    write_fixture("docs/llm_builder_test.txt", "line one\n")

    agent = ProductionAgent(build_registry(), AgentMode.BUILDER)

    prompt = """Apply a patch to docs/llm_builder_test.txt to add a second line:
'line two (added by agent)'.
Use fs.apply_patch."""
    out = agent.run(prompt)
    print(json.dumps(out, indent=2)[:7000])


if __name__ == "__main__":
    main()
