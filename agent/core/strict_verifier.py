from __future__ import annotations
from typing import Dict, List


def strict_verify(goal: str, observations: List[Dict], code_modified: bool) -> Dict:
    errors = [o["error"] for o in observations if o["error"]]

    if errors:
        return {"success": False, "reason": errors[0]}

    if code_modified:
        ran_tests = any(o["tool"] == "dev.run_tests" for o in observations)
        ran_lint = any(o["tool"] == "dev.run_linter" for o in observations)

        if not ran_tests:
            return {"success": False, "reason": "Code changed but tests were not run"}

        if not ran_lint:
            return {"success": False, "reason": "Code changed but linter was not run"}

        tests_ok = any(
            o["tool"] == "dev.run_tests" and o["result"]["passed"]
            for o in observations
        )
        lint_ok = any(
            o["tool"] == "dev.run_linter" and o["result"]["clean"]
            for o in observations
        )

        if not tests_ok:
            return {"success": False, "reason": "Tests failed"}

        if not lint_ok:
            return {"success": False, "reason": "Lint failed"}

    return {"success": True, "reason": "All acceptance criteria met"}
