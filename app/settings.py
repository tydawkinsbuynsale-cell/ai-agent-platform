from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_profile: str
    api_key: str | None
    debug: bool

    @property
    def is_cloud(self) -> bool:
        return self.app_profile == "cloud"

    @property
    def is_internal(self) -> bool:
        return self.app_profile == "internal"

    @property
    def auth_enabled(self) -> bool:
        # Keep simple: only require auth in cloud profile
        return self.is_cloud


def _normalize_profile(raw: str | None) -> str:
    profile = (raw or "api").strip().lower()
    if profile not in {"api", "internal", "cloud"}:
        raise ValueError(f"Invalid APP_PROFILE={profile!r}. Use: api | internal | cloud")
    return profile


def get_settings() -> Settings:
    profile = _normalize_profile(os.getenv("APP_PROFILE"))
    api_key = os.getenv("API_KEY")  # used only when auth_enabled=True
    debug = os.getenv("DEBUG", "0").strip() in {"1", "true", "yes", "on"}
    return Settings(app_profile=profile, api_key=api_key, debug=debug)
