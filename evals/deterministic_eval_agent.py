from __future__ import annotations

from agent.core.agent_loop import Agent, AgentMode
from agent.core.deterministic_planner import simple_read_plan


class DeterministicEvalAgent(Agent):
    """Agent with hardcoded deterministic planner for evals."""
    
    def plan(self, user_input: str):
        if user_input == "generate too many steps":
            return {
                "goal": "Overflow steps",
                "steps": [
                    {"tool": "fs.read_text", "args": {"path": "docs/patch_test.txt"}, "acceptance": "x"}
                    for _ in range(100)
                ],
            }
        if user_input == "apply patch":
            return {
                "goal": "Apply patch",
                "steps": [
                    {
                        "tool": "fs.apply_patch",
                        "args": {
                            "patch": """--- a/docs/patch_test.txt
+++ b/docs/patch_test.txt
@@ -1,3 +1,4 @@
 hello world
 patched successfully
 eval added line
+builder eval wrote this line
""",
                            "base_dir": ".",
                        },
                        "acceptance": "Patch applied cleanly",
                    },
                    {
                        "tool": "dev.run_linter",
                        "args": {"command": "python -c \"import sys; sys.exit(0)\""},
                        "acceptance": "Lint ok",
                    },
                    {
                        "tool": "dev.run_tests",
                        "args": {"command": "python -c \"import sys; sys.exit(0)\""},
                        "acceptance": "Tests ok",
                    },
                ],
            }
        if user_input == "verified patch with memory":
            return {
                "goal": "Apply patch and record decision",
                "steps": [
                    {
                        "tool": "fs.apply_patch",
                        "args": {
                            "patch": """--- a/docs/patch_test.txt
+++ b/docs/patch_test.txt
@@ -1,3 +1,4 @@
 hello world
 patched successfully
 eval added line
+memory write-back test
""",
                            "base_dir": ".",
                        },
                        "acceptance": "Patch applied",
                    },
                    {
                        "tool": "dev.run_linter",
                        "args": {"command": "python -c \"import sys; sys.exit(0)\""},
                        "acceptance": "Lint ok",
                    },
                    {
                        "tool": "dev.run_tests",
                        "args": {"command": "python -c \"import sys; sys.exit(0)\""},
                        "acceptance": "Tests ok",
                    },
                ],
            }
        if user_input == "trigger hygiene":
            steps = []
            # Append 11 decisions with short bodies
            # This will exceed the 10-decision baseline and trigger pruning
            for i in range(11):
                steps.append({
                    "tool": "memory.append_decision",
                    "args": {"title": f"Load test decision {i}", "body": f"Decision body {i}"},
                    "acceptance": "Appended",
                })
            steps.append({
                "tool": "memory.hygiene",
                "args": {},
                "acceptance": "Hygiene executed",
            })
            return {"goal": "Trigger memory hygiene", "steps": steps}
        return simple_read_plan(user_input)
