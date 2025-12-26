from fastapi import FastAPI
from app.settings import get_settings
from app.jobs.router import router as jobs_router


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="AI Job Orchestrator",
        debug=settings.debug,
    )

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "profile": settings.app_profile,
        }

    app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
    return app


app = create_app()
