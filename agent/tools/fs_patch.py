from __future__ import annotations

import re
from pathlib import Path
from pydantic import BaseModel, Field

from agent.tools.base import ToolExecutionError, ToolSpec


UNIFIED_DIFF_HEADER = re.compile(r"^---\s+.+\n\+\+\+\s+.+\n", re.M)


class ApplyPatchIn(BaseModel):
    patch: str = Field(..., description="Unified diff patch")
    base_dir: str = Field(".", description="Base directory for relative paths")
    max_files: int = Field(10, ge=1, le=50)
    max_chars: int = Field(200_000, ge=1, le=1_000_000)


class ApplyPatchOut(BaseModel):
    files_changed: int
    hunks_applied: int


def _apply_unified_diff(text: str, base_dir: Path, max_files: int) -> tuple[int, int]:
    """
    Minimal unified diff applier.
    - Supports ---/+++ headers
    - Applies hunks sequentially
    - Fails fast on mismatch
    """
    if not UNIFIED_DIFF_HEADER.search(text):
        raise ToolExecutionError("Patch must be a unified diff with ---/+++ headers")

    # Split per-file by '--- ' headers
    parts = re.split(r"(?=^---\s)", text, flags=re.M)
    files_changed = 0
    hunks_applied = 0

    for part in parts:
        if not part.strip():
            continue
        if files_changed >= max_files:
            raise ToolExecutionError("Patch exceeds max_files limit")

        lines = part.splitlines()
        if len(lines) < 2:
            raise ToolExecutionError("Invalid unified diff segment")

        # Parse headers
        if not lines[0].startswith("--- ") or not lines[1].startswith("+++ "):
            raise ToolExecutionError("Missing ---/+++ headers")

        old_path = lines[0][4:].strip().split("\t")[0]
        new_path = lines[1][4:].strip().split("\t")[0]

        # Handle a/ b/ prefixes
        if old_path.startswith("a/"):
            old_path = old_path[2:]
        if new_path.startswith("b/"):
            new_path = new_path[2:]

        target = base_dir / new_path
        if not target.exists():
            raise ToolExecutionError(f"Target file does not exist: {target}")

        original = target.read_text(encoding="utf-8", errors="replace").splitlines()
        out = []
        i = 2  # start after headers
        src_idx = 0

        while i < len(lines):
            line = lines[i]
            if line.startswith("@@"):
                # Parse hunk header @@ -l,s +l,s @@
                m = re.match(r"@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,(\d+))?\s+@@", line)
                if not m:
                    raise ToolExecutionError("Invalid hunk header")
                start_new = int(m.group(1)) - 1

                # Copy unchanged lines up to hunk start
                while src_idx < start_new:
                    out.append(original[src_idx])
                    src_idx += 1

                i += 1
                while i < len(lines) and not lines[i].startswith("@@"):
                    h = lines[i]
                    if h.startswith(" "):
                        if src_idx >= len(original) or original[src_idx] != h[1:]:
                            raise ToolExecutionError("Context mismatch while applying patch")
                        out.append(original[src_idx])
                        src_idx += 1
                    elif h.startswith("-"):
                        if src_idx >= len(original) or original[src_idx] != h[1:]:
                            raise ToolExecutionError("Deletion mismatch while applying patch")
                        src_idx += 1
                    elif h.startswith("+"):
                        out.append(h[1:])
                    else:
                        raise ToolExecutionError("Invalid hunk line")
                    i += 1
                hunks_applied += 1
            else:
                raise ToolExecutionError("Unexpected diff content")
        # Append remaining lines
        out.extend(original[src_idx:])

        target.write_text("\n".join(out) + "\n", encoding="utf-8")
        files_changed += 1

    return files_changed, hunks_applied


def _apply_patch_handler(inp: ApplyPatchIn) -> ApplyPatchOut:
    patch = inp.patch
    if len(patch) > inp.max_chars:
        raise ToolExecutionError("Patch exceeds max_chars limit")

    base = Path(inp.base_dir).resolve()
    if not base.exists():
        raise ToolExecutionError("Base directory does not exist")

    files, hunks = _apply_unified_diff(patch, base, inp.max_files)
    return ApplyPatchOut(files_changed=files, hunks_applied=hunks)


APPLY_PATCH_TOOL = ToolSpec(
    name="fs.apply_patch",
    description="Apply a unified diff patch to existing files (safe, minimal edits).",
    input_model=ApplyPatchIn,
    output_model=ApplyPatchOut,
    handler=_apply_patch_handler,
)
