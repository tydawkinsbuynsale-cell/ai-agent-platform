from __future__ import annotations
from typing import Dict, Any


def enforce_post_change_checks(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    If the plan contains write operations, append required checks:
    - dev.run_linter
    - dev.run_tests
    Only add if not already present.
    """
    steps = plan.get("steps", [])
    if not isinstance(steps, list):
        return plan

    write_tools = {"fs.apply_patch", "fs.append_text"}
    has_write = any(s.get("tool") in write_tools for s in steps)

    if not has_write:
        return plan

    has_lint = any(s.get("tool") == "dev.run_linter" for s in steps)
    has_tests = any(s.get("tool") == "dev.run_tests" for s in steps)

    if not has_lint:
        steps.append(
            {
                "tool": "dev.run_linter",
                "args": {"command": "ruff .", "timeout_sec": 120},
                "acceptance": "Linter returns clean=true",
            }
        )

    if not has_tests:
        steps.append(
            {
                "tool": "dev.run_tests",
                "args": {"command": "pytest -q", "timeout_sec": 300},
                "acceptance": "Tests return passed=true",
            }
        )

    plan["steps"] = steps
    return plan
