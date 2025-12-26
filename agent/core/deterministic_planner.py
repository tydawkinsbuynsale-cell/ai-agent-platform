from __future__ import annotations

from typing import Dict, List


def simple_read_plan(user_input: str) -> Dict:
    """
    Very simple deterministic planner:
    expects: "read <path>"
    """
    parts = user_input.strip().split(maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "read":
        raise ValueError("Expected input: read <path>")

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
