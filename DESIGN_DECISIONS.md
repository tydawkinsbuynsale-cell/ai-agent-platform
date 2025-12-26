# Design Decisions

This document explains the key architectural choices in the AI Job Orchestrator and why they were made.

## Goals

- Provide a dependable interface for running "AI jobs" (review, summarize, validate, etc.)
- Keep execution controlled (bounded steps, predictable behavior)
- Make it easy to demo locally and operate as an internal tool
- Preserve a clear path to production hardening (auth, rate limits, persistence, async workers)

Non-goals (for now):
- Building a full frontend UI
- Adding a database and durable job history
- Adding background workers/queues
- Expanding job types beyond a minimal set

## API-first contract

Decision: expose the system primarily through an HTTP API (`POST /jobs`, `GET /jobs/{id}`, `GET /health`).

Why:
- The API is the single source of truth for behavior.
- Any interface (CLI, future UI, integrations) can reuse the same contract.
- Makes the system testable and automatable (curl, CI, deterministic evals).

Tradeoffs:
- Slightly more setup than a single script.
- Requires a running server process for CLI interactions.

## Profiles (`APP_PROFILE`)

Decision: use `APP_PROFILE` (`api | internal | cloud`) to control operational behavior without changing core logic.

Why:
- Local dev and internal usage prioritize speed and simplicity.
- Cloud usage requires safer defaults (auth/rate limits/stricter timeouts).
- Keeps one codebase while supporting multiple deployment contexts.

Rules:
- Profiles may change operational knobs (auth, rate limiting, logging).
- Profiles must not change job semantics or core agent logic.

## Internal synchronous execution

Decision: in `internal` profile, execute jobs synchronously on submission (immediate result); in `api/cloud`, accept jobs and return `queued` until async execution is added.

Why:
- Provides a working end-to-end demo immediately, without adding queue/worker/db complexity.
- Keeps the system deterministic and easy to debug.
- Preserves a clean extension path to async execution later.

Tradeoffs:
- Synchronous mode doesn't model production throughput.
- Long jobs can block request threads (acceptable in internal-only mode).

## In-memory job store (dev-only)

Decision: store job state/results in an in-memory dictionary.

Why:
- Fast iteration and minimal dependencies.
- Keeps scope tight while interfaces stabilize.

Tradeoffs:
- Not durable across restarts.
- Not suitable for multi-process/multi-instance deployments.

Planned upgrade path:
- Add a persistence layer (SQLite/Postgres) behind a small storage interface.
- Keep API contract stable while swapping storage implementation.

## CLI as the "internal tool"

Decision: provide a Typer CLI that calls the API, instead of implementing logic directly in the CLI.

Why:
- Prevents duplicated behavior between CLI and API.
- Ensures internal tool usage exercises the same contract and code paths.
- Makes it easy to automate in scripts/CI.

## Failure semantics and exit codes

Decision: CLI `run` returns:
- `0` on success
- `1` on job failure
- `2` on timeout

Why:
- Works cleanly in automation, CI pipelines, and shell scripts.
- Makes failure states explicit and machine-readable.

## Minimal surface area first

Decision: prefer the smallest set of endpoints and features to prove correctness before expanding.

Why:
- Reduces risk of scope creep.
- Increases confidence that each layer is correct (settings → API → router → runner → CLI).
- Keeps the project reviewable and production-oriented.

## Roadmap (tight, non-creeping)

Next steps that preserve the current architecture:
1. Wire `runner.run_job()` to the deterministic agent core (pass-through)
2. Add optional auth in `cloud` profile (API key)
3. Add storage interface + persistent implementation
4. Add async execution (worker) only after storage and contracts are stable
