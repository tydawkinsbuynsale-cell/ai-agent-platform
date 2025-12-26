from __future__ import annotations

import os
import requests
from dataclasses import dataclass
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class LLMResponse:
    text: str
    raw: Optional[Dict[str, Any]] = None


class OpenAIHTTPClient:
    """
    Minimal OpenAI client using the Responses API.
    Deterministic settings for planning.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        timeout_sec: int = 60,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

    def complete(self, prompt: str) -> LLMResponse:
        url = f"{self.base_url}/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": prompt,
            "temperature": 0,
        }

        r = requests.post(url, headers=headers, json=payload, timeout=self.timeout_sec)
        if r.status_code >= 400:
            raise RuntimeError(f"OpenAI error {r.status_code}: {r.text}")

        data = r.json()

        text_parts = []
        for item in data.get("output", []):
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    text_parts.append(c.get("text", ""))

        text = "\n".join(text_parts).strip()
        if not text:
            raise RuntimeError("Empty LLM response")

        return LLMResponse(text=text, raw=data)
