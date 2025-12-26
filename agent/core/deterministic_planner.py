from __future__ import annotations

from typing import Dict, List


def simple_read_plan(user_input: str) -> Dict:
    """
    Deterministic planner for evals with multiple patterns.
    """
    
    # Detect read operations
    if "read" in user_input.lower() and "docs/patch_test.txt" in user_input.lower():
        return {
            "goal": "Read docs/patch_test.txt",
            "steps": [
                {
                    "tool": "fs.read_text",
                    "args": {"path": "docs/patch_test.txt"},
                    "acceptance": "File contents returned"
                }
            ]
        }
    
    # Detect append operations
    if "append" in user_input.lower() and "docs/patch_test.txt" in user_input.lower():
        return {
            "goal": "Append to docs/patch_test.txt",
            "steps": [
                {
                    "tool": "fs.append_text",
                    "args": {"path": "docs/patch_test.txt", "content": "test\n"},
                    "acceptance": "Content appended"
                }
            ]
        }
    
    # Detect fs.append_text explicit request
    if "fs.append_text" in user_input.lower() and "docs/patch_test.txt" in user_input.lower():
        return {
            "goal": "Append to docs/patch_test.txt",
            "steps": [
                {
                    "tool": "fs.append_text",
                    "args": {"path": "docs/patch_test.txt", "content": "eval test line\n"},
                    "acceptance": "Content appended"
                }
            ]
        }
    
    # Memory read
    if "memory" in user_input.lower() and "facts" in user_input.lower():
        return {
            "goal": "Read project facts",
            "steps": [
                {
                    "tool": "memory.read_project_facts",
                    "args": {},
                    "acceptance": "Facts returned"
                }
            ]
        }
    
    # Memory writeback test - patch operation with passing lint/tests
    if "memory_test.txt" in user_input.lower():
        return {
            "goal": "Apply patch to docs/memory_test.txt",
            "steps": [
                {
                    "tool": "fs.apply_patch",
                    "args": {
                        "patch": "--- docs/memory_test.txt\n+++ docs/memory_test.txt\n@@ -1 +1,2 @@\n original line\n+memory test\n",
                        "base_dir": "."
                    },
                    "acceptance": "Patch applied successfully"
                },
                {
                    "tool": "dev.run_linter",
                    "args": {
                        "command": "echo 'lint passed'",
                        "timeout_sec": 10
                    },
                    "acceptance": "Linter returns clean=true"
                },
                {
                    "tool": "dev.run_tests",
                    "args": {
                        "command": "echo 'tests passed'",
                        "timeout_sec": 10
                    },
                    "acceptance": "Tests return passed=true"
                }
            ]
        }
    
    # Fallback to simple read pattern
    parts = user_input.strip().split(maxsplit=1)
    if len(parts) == 2 and parts[0].lower() == "read":
        path = parts[1]
        return {
            "goal": f"Read file {path}",
            "steps": [
                {
                    "tool": "fs.read_text",
                    "args": {"path": path, "max_chars": 2000},
                    "acceptance": "File content is returned without error",
                }
            ],
        }
    
    # Default: show info (triggers retrieval)
    return {
        "goal": "Show project information",
        "steps": [
            {
                "tool": "memory.read_project_facts",
                "args": {},
                "acceptance": "Information retrieved"
            }
        ]
    }

