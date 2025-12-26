from __future__ import annotations
from pathlib import Path


def reset_patch_test_file() -> None:
    p = Path("docs/patch_test.txt")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "hello world\npatched successfully\neval added line\n",
        encoding="utf-8",
    )


def reset_memory_files() -> None:
    """Reset memory files to baseline state between evals."""
    memory_dir = Path("memory")
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    # Reset decisions.md to baseline
    decisions = memory_dir / "decisions.md"
    decisions.write_text(
        "# Decisions\n\n",
        encoding="utf-8",
    )
    
    # Clear summary if it exists
    summary = memory_dir / "decisions_summary.md"
    if summary.exists():
        summary.unlink()
