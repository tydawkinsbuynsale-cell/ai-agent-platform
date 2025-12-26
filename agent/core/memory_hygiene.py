from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass(frozen=True)
class HygienePolicy:
    keep_last_n_decisions: int = 30
    max_decisions_chars: int = 25_000  # hard cap for decisions.md size


def _split_decisions(md: str) -> List[str]:
    # assumes decisions use headings "## ..."
    parts = md.split("\n## ")
    if not parts:
        return []
    out = []
    # first part includes "# Decisions" header
    out.append(parts[0].strip())
    for p in parts[1:]:
        out.append("## " + p.strip())
    return [x for x in out if x.strip()]


def _extract_entries(chunks: List[str]) -> Tuple[str, List[str]]:
    header = chunks[0] if chunks else "# Decisions"
    entries = [c for c in chunks[1:] if c.startswith("## ")]
    return header, entries


def summarize_and_prune_decisions(
    decisions_path: str = "memory/decisions.md",
    summary_path: str = "memory/decisions_summary.md",
    policy: HygienePolicy = HygienePolicy(),
) -> dict:
    dpath = Path(decisions_path)
    spath = Path(summary_path)

    if not dpath.exists():
        return {"changed": False, "reason": "decisions.md not found"}

    text = dpath.read_text(encoding="utf-8", errors="replace")
    chunks = _split_decisions(text)
    header, entries = _extract_entries(chunks)

    if len(text) <= policy.max_decisions_chars and len(entries) <= policy.keep_last_n_decisions:
        return {"changed": False, "reason": "within limits"}

    # Keep last N entries, summarize the rest (deterministic)
    keep = entries[-policy.keep_last_n_decisions :] if entries else []
    old = entries[: max(0, len(entries) - len(keep))]

    # Write/append summary deterministically (no LLM)
    if old:
        existing_summary = spath.read_text(encoding="utf-8", errors="replace") if spath.exists() else "# Decisions Summary\n"
        summary_block = "\n\n## Archived decisions (pruned)\n" + "\n".join(
            f"- {e.splitlines()[0].replace('## ', '').strip()}"
            for e in old
        )
        spath.write_text(existing_summary + summary_block, encoding="utf-8")

    # Rewrite decisions.md with header + kept entries only
    new_text = header.rstrip() + "\n\n" + "\n\n".join(keep).rstrip() + "\n"
    dpath.write_text(new_text, encoding="utf-8")

    return {
        "changed": True,
        "pruned_count": len(old),
        "kept_count": len(keep),
        "decisions_chars": len(new_text),
    }
