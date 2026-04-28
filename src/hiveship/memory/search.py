"""Session search — find relevant past jobs via FTS5 with smart windowing.

Inspired by hermes-agent's session_search_tool: groups results by job,
uses windowed context (25% before / 75% after match), returns focused
summaries rather than raw transcripts.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from hiveship.memory.history import JobHistoryDB

logger = logging.getLogger(__name__)


@dataclass
class JobSearchResult:
    """A single past job that matched the search query."""
    job_id: str
    goal: str
    status: str
    repo_owner: str
    repo_name: str
    snippets: List[str]  # Relevant response_summary extracts


def search_past_jobs(
    db: JobHistoryDB,
    query: str,
    repo_owner: str = "",
    repo_name: str = "",
    top_n: int = 3,
    snippet_chars: int = 500,
) -> List[JobSearchResult]:
    """Search past jobs for relevant context.

    Groups FTS5 results by job_id, takes top N unique jobs,
    and extracts windowed snippets around match positions.

    Args:
        db: The job history database.
        query: Search query string.
        repo_owner: Filter by repo owner (optional).
        repo_name: Filter by repo name (optional).
        top_n: Maximum number of unique jobs to return.
        snippet_chars: Max chars per snippet.

    Returns:
        List of JobSearchResult with relevant snippets.
    """
    if not query.strip():
        return []

    raw_results = db.search_messages(
        query, repo_owner=repo_owner, repo_name=repo_name, limit=top_n * 5,
    )

    if not raw_results:
        return []

    # Group by job_id, preserving order (first match = most relevant)
    job_groups: dict = {}
    for row in raw_results:
        jid = row["job_id"]
        if jid not in job_groups:
            job_groups[jid] = {
                "goal": row.get("goal", ""),
                "status": row.get("job_status", ""),
                "repo_owner": row.get("repo_owner", ""),
                "repo_name": row.get("repo_name", ""),
                "snippets": [],
            }
        if len(job_groups[jid]["snippets"]) < 3:  # Max 3 snippets per job
            summary = row.get("response_summary", "")
            snippet = _extract_window(summary, query, snippet_chars)
            if snippet:
                job_groups[jid]["snippets"].append(snippet)

    # Take top N jobs
    results = []
    for jid, data in list(job_groups.items())[:top_n]:
        results.append(JobSearchResult(
            job_id=jid,
            goal=data["goal"],
            status=data["status"],
            repo_owner=data["repo_owner"],
            repo_name=data["repo_name"],
            snippets=data["snippets"],
        ))
    return results


def _extract_window(text: str, query: str, max_chars: int) -> str:
    """Extract a windowed snippet around the query match.

    Uses hermes pattern: 25% before match, 75% after.
    """
    if not text:
        return ""

    lower_text = text.lower()
    lower_query = query.lower()
    pos = lower_text.find(lower_query)

    if pos == -1:
        # No exact match, return start of text
        return text[:max_chars] + ("..." if len(text) > max_chars else "")

    # 25% budget before, 75% after
    before_budget = max_chars // 4
    after_budget = max_chars - before_budget

    start = max(0, pos - before_budget)
    end = min(len(text), pos + len(query) + after_budget)

    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet


def format_search_results_for_prompt(results: List[JobSearchResult]) -> str:
    """Format search results into a concise block for prompt injection."""
    if not results:
        return ""

    lines = ["Past Related Work:"]
    for r in results:
        status_icon = "\u2705" if r.status == "complete" else "\u274c"
        lines.append(f"\n{status_icon} Job {r.job_id}: \"{r.goal}\" [{r.status}]")
        for snippet in r.snippets:
            # Indent snippets and cap length
            lines.append(f"  > {snippet[:300]}")

    return "\n".join(lines)
