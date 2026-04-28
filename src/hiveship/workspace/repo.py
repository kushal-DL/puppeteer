import pathlib
import re
from typing import Dict

from hiveship.config import KEY_FILES


def sanitize_branch_name(raw: str) -> str:
    """Convert arbitrary text into a valid git branch segment."""
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "-", raw)
    return re.sub(r"-{2,}", "-", sanitized).strip("-")[:50]


def get_repo_summary(workspace: pathlib.Path, max_chars: int = 3000) -> str:
    """Build a lightweight repo map using pure Python (no subprocess)."""
    files = sorted(
        str(p.relative_to(workspace))
        for p in workspace.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(workspace).parts
    )
    file_list = "\n".join(files)
    if len(file_list) > 3000:
        file_list = file_list[:3000] + "\n...[tree truncated]..."

    summary = f"Repository file tree:\n{file_list}\n"
    budget = max_chars - len(summary)
    for kf in KEY_FILES:
        fp = workspace / kf
        if fp.exists() and budget > 0:
            content = fp.read_text(errors="replace")[:budget]
            summary += f"\n--- {kf} ---\n{content}\n"
            budget -= len(content)
    return summary[:max_chars]
