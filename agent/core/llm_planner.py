from __future__ import annotations

import json
from typing import Any, Dict

from agent.tools.base import ToolInputError


def build_planner_prompt(user_input: str, tool_schemas: Dict[str, Dict]) -> str:
    tool_lines = []
    for name, schema in tool_schemas.items():
        params = json.dumps(schema["parameters"], indent=2)
        required = schema.get("required", [])
        tool_lines.append(f"{name}:\n  Description: {schema['description']}\n  Parameters: {params}\n  Required: {required}")

    tools_text = "\n\n".join(tool_lines)

    return f"""You are a planning module.
Return ONLY valid JSON. No markdown. No explanations.

User request:
{user_input}

Available tools:
{tools_text}

CRITICAL: Use the EXACT parameter names shown above.

JSON schema:
{{
  "goal": "string",
  "steps": [
    {{
      "tool": "tool.name",
      "args": {{}},
      "acceptance": "string"
    }}
  ]
}}
"""


def parse_plan_json(text: str) -> Dict[str, Any]:
    try:
        obj = json.loads(text)
    except Exception as e:
        raise ToolInputError(f"Planner returned invalid JSON: {e}") from e

    if not isinstance(obj, dict):
        raise ToolInputError("Planner output must be a JSON object")

    if not isinstance(obj.get("goal"), str):
        raise ToolInputError("Missing or invalid 'goal'")

    steps = obj.get("steps")
    if not isinstance(steps, list):
        raise ToolInputError("'steps' must be a list")

    for s in steps:
        if not isinstance(s, dict):
            raise ToolInputError("Each step must be an object")
        if not isinstance(s.get("tool"), str):
            raise ToolInputError("Step.tool must be a string")
        if not isinstance(s.get("args"), dict):
            raise ToolInputError("Step.args must be an object")

    return obj
