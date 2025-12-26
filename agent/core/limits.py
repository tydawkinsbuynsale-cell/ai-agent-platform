from dataclasses import dataclass


@dataclass(frozen=True)
class RunLimits:
    max_steps: int = 12
    max_planner_attempts: int = 3
    max_total_seconds: int = 180
    max_tool_seconds: int = 120
