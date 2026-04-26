import pathlib
import re
from typing import Dict, List

from config import ARTIFACT_CHAR_LIMIT, BLOCKED_PATHS, KEY_FILES, MAX_READ_FILES, READ_BUDGET
from models import FileArtifact


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


def validate_files(files: List[FileArtifact], workspace: pathlib.Path) -> None:
    """Guard against path traversal and writes to protected paths."""
    for f in files:
        target = (workspace / f.path).resolve()
        if not str(target).startswith(str(workspace.resolve())):
            raise ValueError(f"Path traversal blocked: {f.path}")
        if any(part in BLOCKED_PATHS for part in pathlib.PurePosixPath(f.path).parts):
            raise ValueError(f"Protected path blocked: {f.path}")


def write_files(files: List[FileArtifact], workspace: pathlib.Path) -> None:
    """Write validated file artifacts to disk."""
    for f in files:
        target = (workspace / f.path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f.content, encoding="utf-8")


def read_agent_files(
    agent_read_files: List[str],
    workspace: pathlib.Path,
) -> Dict[str, str]:
    """Read specific files from the workspace with a budget cap."""
    file_context: Dict[str, str] = {}
    budget = READ_BUDGET
    for fp in agent_read_files[:MAX_READ_FILES]:
        if budget <= 0:
            break
        full = (workspace / fp).resolve()
        if str(full).startswith(str(workspace.resolve())) and full.exists():
            content = full.read_text(errors="replace")[: min(ARTIFACT_CHAR_LIMIT, budget)]
            file_context[fp] = content
            budget -= len(content)
    return file_context


def read_artifact_context(
    keys: List[str],
    artifacts_dir: pathlib.Path,
) -> Dict[str, str]:
    """Read agent outputs from the file-based artifact store.

    Each file is capped at ARTIFACT_CHAR_LIMIT independently; a total
    READ_BUDGET cap prevents prompt explosion.
    """
    context: Dict[str, str] = {}
    total = 0
    for key in keys:
        if total >= READ_BUDGET:
            break
        fp = artifacts_dir / f"{key}.txt"
        if fp.exists():
            chunk = fp.read_text(errors="replace")[
                : min(ARTIFACT_CHAR_LIMIT, READ_BUDGET - total)
            ]
            context[key] = chunk
            total += len(chunk)
    return context


def validate_cross_references(files: List[FileArtifact]) -> List[str]:
    """Check that Python imports between delivered files actually resolve.

    Returns a list of human-readable issue strings. An empty list means
    all cross-references look OK. Only checks imports that reference
    other files in the delivery — stdlib and pip packages are ignored.
    """
    import re as _re

    delivered_modules = set()
    for f in files:
        p = pathlib.PurePosixPath(f.path)
        if p.suffix == ".py":
            # "src/game.py" → {"game", "src.game"}
            stem = p.with_suffix("")
            delivered_modules.add(stem.name)
            delivered_modules.add(str(stem).replace("/", "."))

    issues: List[str] = []
    import_re = _re.compile(
        r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", _re.MULTILINE,
    )
    for f in files:
        if not f.path.endswith(".py"):
            continue
        for m in import_re.finditer(f.content):
            module = (m.group(1) or m.group(2)).split(".")[0]
            # Skip obvious stdlib / pip names
            if module in _COMMON_STDLIB:
                continue
            # If the module name looks like it should be a co-delivered file
            # but isn't in the delivery, flag it.
            if module not in delivered_modules and _looks_local(module, f.content):
                issues.append(
                    f"'{f.path}' imports '{module}' which is not delivered "
                    f"as a .py file in this plan. Either add '{module}.py' "
                    f"to the delivery or inline the code."
                )
    return issues


# Known stdlib/builtin top-level modules (non-exhaustive but covers common cases)
_COMMON_STDLIB = frozenset({
    "abc", "argparse", "ast", "asyncio", "base64", "bisect", "builtins",
    "calendar", "cgi", "cmd", "codecs", "collections", "colorsys",
    "configparser", "contextlib", "copy", "csv", "ctypes", "dataclasses",
    "datetime", "decimal", "difflib", "dis", "email", "enum", "errno",
    "fcntl", "fileinput", "fnmatch", "fractions", "ftplib", "functools",
    "gc", "getpass", "glob", "gzip", "hashlib", "heapq", "hmac", "html",
    "http", "importlib", "inspect", "io", "ipaddress", "itertools", "json",
    "logging", "lzma", "math", "mimetypes", "multiprocessing", "numbers",
    "operator", "os", "pathlib", "pickle", "platform", "pprint",
    "queue", "random", "re", "readline", "reprlib", "secrets", "select",
    "shelve", "shlex", "shutil", "signal", "site", "smtplib", "socket",
    "sqlite3", "ssl", "stat", "statistics", "string", "struct",
    "subprocess", "sys", "syslog", "tempfile", "textwrap", "threading",
    "time", "timeit", "tkinter", "token", "tokenize", "tomllib", "trace",
    "traceback", "tracemalloc", "turtle", "types", "typing",
    "unicodedata", "unittest", "urllib", "uuid", "venv", "warnings",
    "wave", "weakref", "webbrowser", "xml", "xmlrpc", "zipfile", "zipimport",
    "zlib",
    # Common pip packages
    "flask", "django", "fastapi", "uvicorn", "gunicorn", "requests",
    "httpx", "aiohttp", "numpy", "pandas", "scipy", "matplotlib",
    "seaborn", "plotly", "sklearn", "tensorflow", "torch", "pydantic",
    "sqlalchemy", "alembic", "celery", "redis", "boto3", "google",
    "openai", "anthropic", "pytest", "click", "typer", "rich",
    "yaml", "toml", "dotenv", "jwt", "cryptography", "paramiko",
    "PIL", "cv2", "pygame", "chess",
})


def _looks_local(module_name: str, file_content: str) -> bool:
    """Heuristic: does this import look like it refers to a local module?"""
    # If the module name appears as a filename reference elsewhere, it's local
    if f"{module_name}.py" in file_content:
        return True
    # snake_case names that aren't in stdlib are likely local
    if "_" in module_name and module_name.islower():
        return True
    # Short single-word lowercase names not in stdlib — likely local
    if module_name.islower() and len(module_name) <= 20:
        return True
    return False
