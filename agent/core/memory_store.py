from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class MemoryHit:
    source: str
    path: str
    snippet: str


class MemoryStore:
    def __init__(self, root: str = "memory") -> None:
        self.root = Path(root)

    def read_project_facts(self) -> Dict[str, Any]:
        path = self.root / "project_facts.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def write_project_facts(self, data: Dict[str, Any]) -> None:
        path = self.root / "project_facts.json"
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def append_decision(self, title: str, body: str) -> None:
        path = self.root / "decisions.md"
        existing = path.read_text(encoding="utf-8") if path.exists() else "# Decisions\n"
        entry = f"\n## {title}\n{body.strip()}\n"
        path.write_text(existing + entry, encoding="utf-8")


def _keyword_hits(text: str, keywords: List[str]) -> bool:
    t = text.lower()
    return all(k.lower() in t for k in keywords)


def keyword_retrieve(
    query: str,
    search_paths: List[str],
    max_hits: int = 6,
    max_chars: int = 700,
) -> List[MemoryHit]:
    """
    Deterministic keyword retrieval:
    - splits query into simple keywords
    - scans files under provided paths
    - returns small snippets
    """
    keywords = [k for k in query.strip().split() if len(k) >= 3]
    if not keywords:
        return []

    hits: List[MemoryHit] = []

    for base in search_paths:
        base_path = Path(base)
        if not base_path.exists():
            continue

        for p in base_path.rglob("*"):
            if p.is_dir():
                continue
            if p.suffix.lower() not in {".md", ".txt", ".json", ".py"}:
                continue

            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            if not _keyword_hits(content, keywords):
                continue

            # snippet: first occurrence window
            lower = content.lower()
            idx = min((lower.find(k.lower()) for k in keywords if lower.find(k.lower()) >= 0), default=-1)
            if idx == -1:
                idx = 0

            start = max(0, idx - 200)
            end = min(len(content), start + max_chars)
            snippet = content[start:end].strip()

            hits.append(MemoryHit(source=base, path=str(p), snippet=snippet))
            if len(hits) >= max_hits:
                return hits

    return hits
