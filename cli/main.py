from __future__ import annotations

import os
import time
from typing import Any

import httpx
import typer

app = typer.Typer(help="Internal CLI for the AI Job Orchestrator (calls the API).")


def _base_url() -> str:
    return os.getenv("AJO_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


@app.command()
def submit(
    job_type: str = typer.Argument(..., help="Job type (e.g. review, summarize)"),
    payload: str = typer.Option("{}", "--payload", "-p", help="JSON payload string"),
) -> None:
    """
    Submit a job. Prints job_id.
    """
    import json

    try:
        payload_obj: dict[str, Any] = json.loads(payload)
        if not isinstance(payload_obj, dict):
            raise ValueError("payload must be a JSON object")
    except Exception as e:
        raise typer.BadParameter(f"Invalid JSON for --payload: {e}")

    url = f"{_base_url()}/jobs"
    r = httpx.post(url, json={"job_type": job_type, "payload": payload_obj}, timeout=20)
    r.raise_for_status()
    data = r.json()
    typer.echo(data["job_id"])


@app.command()
def status(job_id: str) -> None:
    """
    Get job status by id. Prints JSON.
    """
    url = f"{_base_url()}/jobs/{job_id}"
    r = httpx.get(url, timeout=20)
    r.raise_for_status()
    typer.echo(r.text)


@app.command()
def run(
    job_type: str = typer.Argument(...),
    payload: str = typer.Option("{}", "--payload", "-p"),
    poll_interval: float = typer.Option(0.5, "--poll-interval"),
    timeout_s: float = typer.Option(30.0, "--timeout"),
) -> None:
    """
    Submit then poll until done/failed (for now it will stay queued).
    """
    job_id = submit.callback(job_type=job_type, payload=payload)  # type: ignore
    # submit.callback prints; we want the value, so do it directly instead:
    raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
