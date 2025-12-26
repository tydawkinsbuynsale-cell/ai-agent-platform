from __future__ import annotations

import json
from agent.registry import build_registry


def main() -> None:
    reg = build_registry()

    print("TOOLS:", json.dumps(reg.list_tools(), indent=2))

    # Change this path to a real file in your repo (README.md is usually safe)
    result = reg.call("fs.read_text", {"path": "README.md", "max_chars": 2000})
    print("RESULT:", json.dumps(result, indent=2)[:2000])


if __name__ == "__main__":
    main()
