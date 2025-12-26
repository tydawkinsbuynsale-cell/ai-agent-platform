from __future__ import annotations

from typing import Any


def run_job(job_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Minimal synchronous runner.
    For now, returns a deterministic result without touching your agent core.
    Next step will wire in your deterministic agent platform here (pass-through).
    """
    # Keep it deterministic and explicit.
    return {
        "job_type": job_type,
        "echo": payload,
        "message": "Job executed (internal sync runner)",
    }
