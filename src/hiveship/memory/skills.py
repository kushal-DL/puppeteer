"""Skill store — reusable procedural knowledge as YAML+Markdown files.

Skills are SKILL.md files with YAML frontmatter stored in:
- Per-repo: {workspace}/.hiveship/skills/{name}/SKILL.md
- Global:   ~/.hiveship/global_skills/{name}/SKILL.md

Inspired by hermes-agent's skills system.
"""

import logging
import os
import pathlib
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_SKILLS_DIR = "skills"
_SKILL_FILE = "SKILL.md"
_GLOBAL_SKILLS_DIR = pathlib.Path(
    os.environ.get("HIVESHIP_GLOBAL_SKILLS", "")
    or str(pathlib.Path.home() / ".hiveship" / "global_skills")
)

# Budget for total skill content injected into a single prompt
SKILL_INJECTION_BUDGET = 5000

# Prompt for extracting a new skill after a complex successful job
SKILL_EXTRACTION_PROMPT = (
    "A complex task was just completed successfully. Analyze the approach "
    "taken and extract a reusable PROCEDURE as a skill file.\n\n"
    "Goal: {goal}\n"
    "Agents used ({agent_count}):\n{agent_summary}\n"
    "Files delivered:\n{file_list}\n\n"
    "Create a SKILL.md with YAML frontmatter and Markdown body.\n"
    "Format:\n"
    "```\n"
    "---\n"
    "name: short-kebab-case-name\n"
    "description: One-line description (max 120 chars)\n"
    "version: 1.0.0\n"
    "tags: [relevant, tags]\n"
    "---\n"
    "\n"
    "# Procedure Title\n"
    "\n"
    "Step-by-step instructions for replicating this approach...\n"
    "```\n\n"
    "RULES:\n"
    "- Focus on the PROCESS, not the specific content.\n"
    "- Include file structure patterns, naming conventions, key decisions.\n"
    "- Keep under 2000 chars total.\n"
    "- The skill should be useful for SIMILAR future tasks, not just this one.\n\n"
    "Return ONLY the SKILL.md content (including --- frontmatter delimiters)."
)

# Prompt for patching a skill after a review fix
SKILL_PATCH_PROMPT = (
    "A skill was used during a task but the reviewer found issues that "
    "required fixes. Update the skill to incorporate the lesson learned.\n\n"
    "Current skill content:\n```\n{skill_content}\n```\n\n"
    "Review issues that were fixed:\n{issues}\n\n"
    "Return the COMPLETE updated SKILL.md content (including --- frontmatter). "
    "Increment the version patch number. Keep changes minimal."
)


@dataclass
class SkillSummary:
    """Lightweight skill metadata for index injection."""
    name: str
    description: str
    version: str
    tags: List[str]
    source: str  # "repo" or "global"
    path: pathlib.Path


@dataclass
class Skill:
    """Full skill with content."""
    name: str
    description: str
    version: str
    tags: List[str]
    content: str  # Full Markdown body (after frontmatter)
    raw: str  # Full file content including frontmatter
    source: str
    path: pathlib.Path


def _parse_frontmatter(raw: str) -> tuple:
    """Parse YAML frontmatter from a SKILL.md file.

    Returns (metadata_dict, body_text). Uses simple parsing to avoid
    PyYAML dependency.
    """
    if not raw.startswith("---"):
        return {}, raw

    end_match = re.search(r"\n---\s*\n", raw[3:])
    if not end_match:
        return {}, raw

    fm_text = raw[3:end_match.start() + 3]
    body = raw[end_match.end() + 3:].strip()

    # Simple YAML-subset parser (key: value and key: [list])
    meta: Dict[str, object] = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^(\w[\w-]*)\s*:\s*(.*)$", line)
        if match:
            key, val = match.group(1), match.group(2).strip()
            # Array value: [a, b, c]
            if val.startswith("[") and val.endswith("]"):
                items = [i.strip().strip("'\"") for i in val[1:-1].split(",") if i.strip()]
                meta[key] = items
            else:
                meta[key] = val.strip("'\"")
    return meta, body


class SkillStore:
    """Manages skill discovery, loading, creation, and patching.

    Searches two locations:
    1. Per-repo: {workspace}/.hiveship/skills/
    2. Global:   ~/.hiveship/global_skills/
    """

    def __init__(self, workspace: pathlib.Path):
        self._workspace = workspace
        self._repo_skills_dir = workspace / ".hiveship" / _SKILLS_DIR
        self._global_skills_dir = _GLOBAL_SKILLS_DIR

    def discover(self) -> List[SkillSummary]:
        """Find all available skills (repo + global). Returns index of summaries."""
        skills: List[SkillSummary] = []

        # Repo skills take priority
        for skill in self._scan_dir(self._repo_skills_dir, "repo"):
            skills.append(skill)

        # Global skills (skip if name already found in repo)
        repo_names = {s.name for s in skills}
        for skill in self._scan_dir(self._global_skills_dir, "global"):
            if skill.name not in repo_names:
                skills.append(skill)

        return skills

    def _scan_dir(self, base: pathlib.Path, source: str) -> List[SkillSummary]:
        """Scan a directory for SKILL.md files."""
        results = []
        if not base.exists():
            return results

        for skill_dir in sorted(base.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / _SKILL_FILE
            if not skill_file.exists():
                continue
            try:
                raw = skill_file.read_text(encoding="utf-8", errors="replace")
                meta, _ = _parse_frontmatter(raw)
                results.append(SkillSummary(
                    name=str(meta.get("name", skill_dir.name)),
                    description=str(meta.get("description", ""))[:120],
                    version=str(meta.get("version", "1.0.0")),
                    tags=meta.get("tags", []) if isinstance(meta.get("tags"), list) else [],
                    source=source,
                    path=skill_file,
                ))
            except Exception as e:
                logger.warning(f"Failed to parse skill at {skill_file}: {e}")
        return results

    def load(self, name: str) -> Optional[Skill]:
        """Load a full skill by name. Checks repo first, then global."""
        for base, source in [
            (self._repo_skills_dir, "repo"),
            (self._global_skills_dir, "global"),
        ]:
            skill_file = base / name / _SKILL_FILE
            if skill_file.exists():
                raw = skill_file.read_text(encoding="utf-8", errors="replace")
                meta, body = _parse_frontmatter(raw)
                return Skill(
                    name=str(meta.get("name", name)),
                    description=str(meta.get("description", "")),
                    version=str(meta.get("version", "1.0.0")),
                    tags=meta.get("tags", []) if isinstance(meta.get("tags"), list) else [],
                    content=body,
                    raw=raw,
                    source=source,
                    path=skill_file,
                )
        return None

    def create(self, name: str, content: str, global_skill: bool = False) -> pathlib.Path:
        """Create a new skill. Returns the path to the created SKILL.md."""
        base = self._global_skills_dir if global_skill else self._repo_skills_dir
        skill_dir = base / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / _SKILL_FILE
        skill_file.write_text(content, encoding="utf-8")
        logger.info(f"Created skill '{name}' at {skill_file}")
        return skill_file

    def patch(self, name: str, old_str: str, new_str: str) -> bool:
        """Patch a skill's content with find/replace. Returns success."""
        skill = self.load(name)
        if not skill:
            return False
        if old_str not in skill.raw:
            return False
        updated = skill.raw.replace(old_str, new_str, 1)
        skill.path.write_text(updated, encoding="utf-8")
        logger.info(f"Patched skill '{name}'")
        return True

    def update(self, name: str, full_content: str) -> bool:
        """Full rewrite of a skill. Returns success."""
        skill = self.load(name)
        if not skill:
            return False
        skill.path.write_text(full_content, encoding="utf-8")
        logger.info(f"Updated skill '{name}'")
        return True

    def delete(self, name: str) -> bool:
        """Delete a skill directory. Returns success."""
        import shutil
        for base in [self._repo_skills_dir, self._global_skills_dir]:
            skill_dir = base / name
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
                logger.info(f"Deleted skill '{name}' from {base}")
                return True
        return False


def build_skill_index_for_prompt(skills: List[SkillSummary]) -> str:
    """Build a compact skill index for the planner prompt."""
    if not skills:
        return ""
    lines = ["Available Procedures (reference by name in agent system_instruction):"]
    for s in skills:
        tag_str = f" [{', '.join(s.tags)}]" if s.tags else ""
        lines.append(f"- {s.name}: {s.description}{tag_str}")
    return "\n".join(lines)


def build_skill_content_for_agent(
    skill_names: List[str],
    store: SkillStore,
    budget: int = SKILL_INJECTION_BUDGET,
) -> str:
    """Load full skill content for injection into an agent prompt."""
    if not skill_names:
        return ""
    parts = []
    remaining = budget
    for name in skill_names:
        if remaining <= 0:
            break
        skill = store.load(name)
        if not skill:
            continue
        chunk = skill.content[:remaining]
        parts.append(f"[Skill: {skill.name} v{skill.version}]\n{chunk}")
        remaining -= len(chunk)
    return "\n\n".join(parts) if parts else ""
