from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from agent.tools.base import ToolError
from agent.tools.base import ToolRegistry
from agent.core.memory_store import MemoryStore, keyword_retrieve
from agent.core.strict_verifier import strict_verify
from agent.core.policy import enforce_post_change_checks
from agent.core.limits import RunLimits
from agent.core.memory_hygiene import summarize_and_prune_decisions
from agent.core.parallel import run_parallel_tools


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
    def __init__(self, tools: ToolRegistry, mode: AgentMode, limits: RunLimits | None = None) -> None:
        self.tools = tools
        self.mode = mode
        self.limits = limits or RunLimits()
        self._code_modified = False

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
        return strict_verify(goal, observations, self._code_modified)

    # ---- Execution ----

    def run(self, user_input: str) -> Dict[str, Any]:
        start_ts = time.time()
        trace = AgentTrace()
        self._code_modified = False

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
        plan = enforce_post_change_checks(plan)
        trace.add("PLAN", plan)

        # Cap steps
        steps = plan.get("steps", [])
        if len(steps) > self.limits.max_steps:
            raise RuntimeError(f"Plan exceeds max_steps={self.limits.max_steps}")

        observations: List[Dict[str, Any]] = []

        # Separate dev checks (lint/tests) from normal steps for parallel execution
        dev_check_tools = ("dev.run_linter", "dev.run_tests")
        normal_steps = []
        dev_parallel = []
        
        for step in plan.get("steps", []):
            if step["tool"] in dev_check_tools:
                dev_parallel.append(step)
            else:
                normal_steps.append(step)

        # ACT + OBSERVE (normal steps sequentially)
        for step in normal_steps:
            # Check timeout before each step
            if time.time() - start_ts > self.limits.max_total_seconds:
                raise RuntimeError("Run aborted: max_total_seconds exceeded")

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
                t0 = time.time()
                result = self.tools.call(tool_name, args)
                lat = time.time() - t0
                obs = {
                    "tool": tool_name,
                    "args": args,
                    "result": result,
                    "error": None,
                    "latency_sec": round(lat, 3),
                }
                
                # Track code modifications
                if tool_name in ("fs.apply_patch", "fs.append_text"):
                    self._code_modified = True
                    
            except ToolError as e:
                obs = {
                    "tool": tool_name,
                    "args": args,
                    "result": None,
                    "error": str(e),
                }

            observations.append(obs)
            trace.add("OBSERVE", obs)
        
        # Execute dev checks in parallel (if any)
        if dev_parallel:
            par_obs = run_parallel_tools(self.tools, dev_parallel, max_workers=2)
            for obs in par_obs:
                observations.append(obs)
                trace.add("OBSERVE", obs)

        # VERIFY
        verification = self.verify(plan.get("goal", ""), observations)
        trace.add("VERIFY", verification)

        # Memory write-back: only after proven success and real changes
        if verification.get("success") and self._code_modified:
            try:
                self.tools.call(
                    "memory.append_decision",
                    {
                        "title": "Automated code change verified",
                        "body": (
                            f"Goal: {plan.get('goal')}\n\n"
                            "Result: Code change applied and verified.\n"
                            "Quality gates: tests and linter passed.\n"
                        ),
                    },
                )
                trace.add(
                    "MEMORY_WRITE",
                    {"status": "appended decision"},
                )
                
                # Run memory hygiene after successful write
                h = summarize_and_prune_decisions()
                trace.add("MEMORY_HYGIENE", h)
            except Exception as e:
                trace.add(
                    "MEMORY_WRITE",
                    {"status": "failed", "error": str(e)},
                )

        return {
            "goal": plan.get("goal"),
            "verification": verification,
            "observations": observations,
            "code_modified": self._code_modified,
            "trace": trace.to_dict(),
            "metrics": {
                "total_seconds": round(time.time() - start_ts, 3),
                "steps_executed": len(observations),
            },
        }
