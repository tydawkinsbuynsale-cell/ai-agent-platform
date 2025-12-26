from __future__ import annotations

from typing import Dict, List


def simple_verify(goal: str, observations: List[Dict]) -> Dict:
    if not observations:
        return {"success": False, "reason": "No steps executed"}

    obs = observations[0]
    if obs["error"] is not None:
        return {"success": False, "reason": obs["error"]}

    return {"success": True, "reason": "Acceptance criteria met"}
