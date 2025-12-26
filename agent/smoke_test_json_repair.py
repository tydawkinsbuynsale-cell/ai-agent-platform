from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from agent.registry import build_registry
from agent.core.agent_loop import AgentMode
from agent.core.production_agent import ProductionAgent


@dataclass(frozen=True)
class FakeResp:
    text: str
    raw: Optional[Dict[str, Any]] = None


class FlakyLLM:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, prompt: str) -> FakeResp:
        self.calls += 1
        if self.calls == 1:
            return FakeResp(text="not json at all")
        # Valid minimal plan JSON on retry
        return FakeResp(
            text=json.dumps(
                {
                    "goal": "Read file",
                    "steps": [
                        {
                            "tool": "fs.read_text",
                            "args": {"path": "docs/patch_test.txt", "max_chars": 2000},
                            "acceptance": "Content returned",
                        }
                    ],
                }
            )
        )


def main():
    agent = ProductionAgent(build_registry(), AgentMode.REVIEWER)
    # Inject flaky llm
    agent.llm = FlakyLLM()

    out = agent.run("Read docs/patch_test.txt")
    print(json.dumps(out, indent=2)[:5000])


if __name__ == "__main__":
    main()
