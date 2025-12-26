from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

from agent.tools.base import ToolError
from agent.tools.base import ToolRegistry


def run_parallel_tools(
    tools: ToolRegistry,
    steps: List[Dict[str, Any]],
    max_workers: int = 2,
) -> List[Dict[str, Any]]:
    """
    Execute tool steps in parallel. Returns OBSERVE-style dicts.
    Intended ONLY for independent dev checks (lint/tests).
    """
    def _call(step: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = step["tool"]
        args = step["args"]
        t0 = time.time()
        try:
            result = tools.call(tool_name, args)
            return {
                "tool": tool_name,
                "args": args,
                "result": result,
                "error": None,
                "latency_sec": round(time.time() - t0, 3),
            }
        except ToolError as e:
            return {
                "tool": tool_name,
                "args": args,
                "result": None,
                "error": str(e),
                "latency_sec": round(time.time() - t0, 3),
            }

    observations: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_call, s) for s in steps]
        for f in as_completed(futs):
            observations.append(f.result())

    # Deterministic ordering: sort results by tool name
    observations.sort(key=lambda o: o["tool"])
    return observations
