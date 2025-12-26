from __future__ import annotations

import json

from agent.registry import build_registry
from agent.core.agent_loop import AgentMode
from agent.core.production_agent import ProductionAgent


def main():
    agent = ProductionAgent(build_registry(), AgentMode.REVIEWER)
    result = agent.run("Read docs/patch_test.txt")
    print(json.dumps(result, indent=2)[:4000])


if __name__ == "__main__":
    main()
