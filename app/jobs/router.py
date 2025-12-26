from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from uuid import uuid4

router = APIRouter()

# Minimal in-memory job store (dev-only)
_JOBS: dict[str, dict] = {}


class JobCreateRequest(BaseModel):
    job_type: str = Field(..., min_length=1, description="Type of job to run (e.g., 'review', 'summarize').")
    payload: dict = Field(default_factory=dict, description="Arbitrary JSON payload for the job.")


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: dict | None = None


@router.post("", response_model=JobCreateResponse)
def create_job(req: JobCreateRequest) -> JobCreateResponse:
    from app.settings import get_settings
    from app.jobs.runner import run_job

    job_id = str(uuid4())
    _JOBS[job_id] = {"status": "queued", "job_type": req.job_type, "payload": req.payload, "result": None}

    settings = get_settings()
    if settings.is_internal:
        try:
            result = run_job(req.job_type, req.payload)
            _JOBS[job_id]["status"] = "succeeded"
            _JOBS[job_id]["result"] = result
        except Exception as e:
            _JOBS[job_id]["status"] = "failed"
            _JOBS[job_id]["result"] = {"error": str(e)}

    return JobCreateResponse(job_id=job_id, status=_JOBS[job_id]["status"])


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str) -> JobStatusResponse:
    job = _JOBS.get(job_id)
    if not job:
        # FastAPI will return 404 if we raise
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(job_id=job_id, status=job["status"], result=job["result"])
