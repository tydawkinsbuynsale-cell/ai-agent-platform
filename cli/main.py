from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx
import typer

app = typer.Typer(help="Internal CLI for the AI Job Orchestrator (calls the API).")


def _base_url() -> str:
    return os.getenv("AJO_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _parse_payload(payload: str) -> dict[str, Any]:
    try:
        obj = json.loads(payload)
        if not isinstance(obj, dict):
            raise ValueError("payload must be a JSON object")
        return obj
    except Exception as e:
        raise typer.BadParameter(f"Invalid JSON for --payload: {e}")


def _submit(job_type: str, payload_obj: dict[str, Any]) -> dict[str, Any]:
    url = f"{_base_url()}/jobs"
    r = httpx.post(url, json={"job_type": job_type, "payload": payload_obj}, timeout=20)
    r.raise_for_status()
    return r.json()


def _get_status(job_id: str) -> dict[str, Any]:
    url = f"{_base_url()}/jobs/{job_id}"
    r = httpx.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


@app.command()
def submit(
    job_type: str = typer.Argument(..., help="Job type (e.g. review, summarize)"),
    payload: str = typer.Option("{}", "--payload", "-p", help="JSON payload string"),
) -> None:
    """Submit a job. Prints job_id."""
    payload_obj = _parse_payload(payload)
    data = _submit(job_type, payload_obj)
    typer.echo(data["job_id"])


@app.command()
def status(job_id: str) -> None:
    """Get job status by id. Prints JSON."""
    data = _get_status(job_id)
    typer.echo(json.dumps(data, indent=2))


@app.command()
def run(
    job_type: str = typer.Argument(..., help="Job type (e.g. review, summarize)"),
    payload: str = typer.Option("{}", "--payload", "-p", help="JSON payload string"),
    poll_interval: float = typer.Option(0.5, "--poll-interval", min=0.1),
    timeout_s: float = typer.Option(30.0, "--timeout", min=1.0),
) -> None:
    """
    Submit then poll until job is succeeded/failed, then print the final JSON.
    In internal profile this should usually return immediately.
    """
    payload_obj = _parse_payload(payload)

    created = _submit(job_type, payload_obj)
    job_id = created["job_id"]

    start = time.time()
    while True:
        data = _get_status(job_id)
        status_val = data.get("status")

        if status_val in {"succeeded", "failed"}:
            typer.echo(json.dumps(data, indent=2))
            raise typer.Exit(code=0 if status_val == "succeeded" else 1)

        if time.time() - start > timeout_s:
            typer.echo(json.dumps(data, indent=2))
            raise typer.Exit(code=2)

        time.sleep(poll_interval)


if __name__ == "__main__":
    app()
