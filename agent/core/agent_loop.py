from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from agent.tools.base import ToolError
from agent.tools.base import ToolRegistry
from agent.core.memory_store import MemoryStore, keyword_retrieve


class AgentMode(str, Enum):
    BUILDER = "builder"
    REVIEWER = "reviewer"


@dataclass
class AgentStep:
    phase: str
    content: Dict[str, Any]
    timestamp: float


class AgentTrace:
    def __init__(self) -> None:
        self.steps: List[AgentStep] = []

    def add(self, phase: str, content: Dict[str, Any]) -> None:
        self.steps.append(
            AgentStep(
                phase=phase,
                content=content,
                timestamp=time.time(),
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": [
                {
                    "phase": s.phase,
                    "timestamp": s.timestamp,
                    "content": s.content,
                }
                for s in self.steps
            ]
        }


class Agent:
    def __init__(self, tools: ToolRegistry, mode: AgentMode) -> None:
        self.tools = tools
        self.mode = mode

    # ---- Phase hooks (LLM-backed later) ----

    def plan(self, user_input: str) -> Dict[str, Any]:
        """
        Output format (STRICT):
        {
          "goal": "...",
          "steps": [
            {
              "tool": "fs.read_text",
              "args": {...},
              "acceptance": "what success means"
            }
          ]
        }
        """
        raise NotImplementedError("Planner not wired yet")

    def verify(self, goal: str, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Output:
        {
          "success": bool,
          "reason": "..."
        }
        """
        raise NotImplementedError("Verifier not wired yet")

    # ---- Execution ----

    def run(self, user_input: str) -> Dict[str, Any]:
        trace = AgentTrace()

        mem = MemoryStore()
        facts = mem.read_project_facts()
        trace.add("MEMORY_FACTS", {"project_facts": facts})

        # retrieval context (deterministic)
        retrieval_hits = keyword_retrieve(
            query=user_input,
            search_paths=["memory", "docs"],
            max_hits=6,
        )
        trace.add(
            "RETRIEVAL",
            {
                "query": user_input,
                "hits": [
                    {"source": h.source, "path": h.path, "snippet": h.snippet}
                    for h in retrieval_hits
                ],
            },
        )

        # PLAN
        plan = self.plan(user_input)
        trace.add("PLAN", plan)

        observations: List[Dict[str, Any]] = []

        # ACT + OBSERVE
        for step in plan.get("steps", []):
            tool_name = step["tool"]
            args = step["args"]

            # Policy enforcement happens here (Agent layer),
            # not in ToolRegistry by design.
            write_tools = ("fs.append_text", "fs.apply_patch", "memory.append_decision")
            if self.mode == AgentMode.REVIEWER and tool_name in write_tools:
                obs = {
                    "tool": tool_name,
                    "args": args,
                    "result": None,
                    "error": "Write operations not allowed in REVIEWER mode",
                }
                observations.append(obs)
                trace.add("OBSERVE", obs)
                continue

            try:
                result = self.tools.call(tool_name, args)
                obs = {
                    "tool": tool_name,
                    "args": args,
                    "result": result,
                    "error": None,
                }
            except ToolError as e:
                obs = {
                    "tool": tool_name,
                    "args": args,
                    "result": None,
                    "error": str(e),
                }

            observations.append(obs)
            trace.add("OBSERVE", obs)

        # VERIFY
        verification = self.verify(plan.get("goal", ""), observations)
        trace.add("VERIFY", verification)

        return {
            "goal": plan.get("goal"),
            "verification": verification,
            "observations": observations,
            "trace": trace.to_dict(),
        }
