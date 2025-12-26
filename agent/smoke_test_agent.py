from __future__ import annotations

import json

from agent.registry import build_registry
from agent.core.agent_loop import Agent
from agent.core.deterministic_planner import simple_read_plan
from agent.core.deterministic_verifier import simple_verify


class TestAgent(Agent):
    def plan(self, user_input: str):
        return simple_read_plan(user_input)

    def verify(self, goal, observations):
        return simple_verify(goal, observations)


def main():
    agent = TestAgent(build_registry())
    result = agent.run("read README.md")
    print(json.dumps(result, indent=2)[:3000])


if __name__ == "__main__":
    main()
