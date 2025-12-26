from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class EvalTask:
    """A deterministic evaluation task."""
    name: str
    description: str
    user_input: str
    mode: str  # "builder" or "reviewer"
    assertion: str  # Python expression to eval against result
