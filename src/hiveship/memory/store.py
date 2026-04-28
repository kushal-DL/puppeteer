"""Persistent per-repo memory store — declarative facts about a repository.

Manages a `.hiveship/memory.md` file in the workspace root. Entries are
bullet-point declarative facts (e.g. "This repo uses pytest with coverage").
Includes prompt-injection scanning on write.
"""

import logging
import pathlib
import re
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

MEMORY_CHAR_LIMIT = 3000
MEMORY_DIR = ".hiveship"
MEMORY_FILE = "memory.md"

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
    re.compile(r"override\s+(the\s+)?system", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(prior|previous|above)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all|your)", re.IGNORECASE),
    # Exfiltration patterns
    re.compile(r"curl\s+.*\$\{?\w*(key|token|secret|password)", re.IGNORECASE),
    re.compile(r"wget\s+.*\$\{?\w*(key|token|secret|password)", re.IGNORECASE),
    # Invisible unicode (zero-width chars used for hidden instructions)
    re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]"),
]


def _scan_for_injection(text: str) -> Optional[str]:
    """Return the first matched injection pattern description, or None if clean."""
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return f"Blocked: content matches injection pattern '{pattern.pattern}'"
    return None


@dataclass
class MemoryStore:
    """Manages persistent declarative memory for a repository.

    Memory is stored as bullet points in `.hiveship/memory.md` within the
    workspace. Character limit is enforced — oldest entries are trimmed first
    when the limit is exceeded.
    """

    workspace: pathlib.Path
    char_limit: int = MEMORY_CHAR_LIMIT
    entries: List[str] = field(default_factory=list)

    @property
    def memory_path(self) -> pathlib.Path:
        return self.workspace / MEMORY_DIR / MEMORY_FILE

    def load(self) -> None:
        """Load memory entries from disk."""
        if not self.memory_path.exists():
            self.entries = []
            return
        raw = self.memory_path.read_text(encoding="utf-8", errors="replace")
        self.entries = [
            line.lstrip("- ").strip()
            for line in raw.splitlines()
            if line.strip() and line.strip().startswith("- ")
        ]

    def save(self) -> None:
        """Persist current entries to disk, enforcing char limit."""
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        content = self._render_entries()
        # Trim oldest entries if over limit
        while len(content) > self.char_limit and len(self.entries) > 1:
            self.entries.pop(0)
            content = self._render_entries()
        self.memory_path.write_text(content, encoding="utf-8")

    def add(self, entry: str) -> Optional[str]:
        """Add a new entry. Returns error string if blocked, None on success."""
        entry = entry.strip()
        if not entry:
            return "Empty entry"
        blocked = _scan_for_injection(entry)
        if blocked:
            logger.warning(f"Memory injection blocked: {blocked}")
            return blocked
        # Deduplicate (case-insensitive)
        if any(e.lower() == entry.lower() for e in self.entries):
            return None  # silently skip duplicate
        self.entries.append(entry)
        self.save()
        return None

    def add_many(self, entries: List[str]) -> List[str]:
        """Add multiple entries, returning list of any errors."""
        errors = []
        for entry in entries:
            err = self.add(entry)
            if err:
                errors.append(err)
        return errors

    def remove(self, substring: str) -> bool:
        """Remove the first entry containing the substring. Returns True if removed."""
        lower_sub = substring.lower()
        for i, entry in enumerate(self.entries):
            if lower_sub in entry.lower():
                self.entries.pop(i)
                self.save()
                return True
        return False

    def replace(self, old_substring: str, new_text: str) -> Optional[str]:
        """Replace text in the first matching entry. Returns error or None."""
        blocked = _scan_for_injection(new_text)
        if blocked:
            return blocked
        lower_old = old_substring.lower()
        for i, entry in enumerate(self.entries):
            if lower_old in entry.lower():
                # Do case-insensitive find and replace the actual span
                idx = entry.lower().index(lower_old)
                self.entries[i] = entry[:idx] + new_text + entry[idx + len(old_substring):]
                self.save()
                return None
        return f"No entry matching '{old_substring}'"

    def render(self) -> str:
        """Render all entries as a readable block for prompt injection."""
        if not self.entries:
            return ""
        return self._render_entries()

    def _render_entries(self) -> str:
        return "\n".join(f"- {e}" for e in self.entries) + "\n"

    def __len__(self) -> int:
        return len(self.entries)
