from __future__ import annotations

import json
from agent.registry import build_registry


def main():
    reg = build_registry()

    facts = reg.call("memory.read_project_facts", {})
    print("FACTS:", json.dumps(facts, indent=2))

    res = reg.call(
        "memory.append_decision",
        {
            "title": "2025-12-26 — Memory tools exposed",
            "body": "Memory read/write is now available as schema-validated tools.",
        },
    )
    print("APPEND RESULT:", res)


if __name__ == "__main__":
    main()
