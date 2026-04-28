"""Trajectory compression — protect head+tail, summarize middle.

When agent context grows beyond READ_BUDGET, this module compresses the
middle section via LLM summarization while preserving the head (goal/plan)
and tail (recent actions).

Inspired by hermes-agent's context_compressor.py.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Default compression settings
COMPRESSION_TARGET = 30_000  # Target chars after compression
HEAD_PROTECT = 2             # Protect first N context entries (goal + plan)
TAIL_PROTECT = 3             # Protect last N context entries (recent work)

_COMPRESSION_MARKER = "[COMPRESSED: {count} artifacts summarized]"

_SUMMARY_PROMPT = (
    "Summarize the following intermediate agent outputs into a concise "
    "reference document. Preserve:\n"
    "- Key decisions and approaches taken\n"
    "- Important findings or data\n"
    "- File paths and structure information\n"
    "- Any constraints or blockers discovered\n\n"
    "Keep under {target_chars} chars. Be factual and dense.\n\n"
    "Artifacts to summarize:\n{artifacts}"
)


def should_compress(context: Dict[str, str], target: int = COMPRESSION_TARGET) -> bool:
    """Check if the total context exceeds the compression threshold."""
    total = sum(len(v) for v in context.values())
    return total > target


def compress_context(
    context: Dict[str, str],
    llm_fn=None,
    target: int = COMPRESSION_TARGET,
    head_protect: int = HEAD_PROTECT,
    tail_protect: int = TAIL_PROTECT,
) -> Dict[str, str]:
    """Compress context by summarizing middle entries.

    Args:
        context: Dict of {key: content} from artifact files.
        llm_fn: Callable(prompt) -> str for summarization. If None, uses truncation.
        target: Target total chars after compression.
        head_protect: Number of initial entries to protect.
        tail_protect: Number of final entries to protect.

    Returns:
        Compressed context dict with the same keys structure.
    """
    keys = list(context.keys())
    if len(keys) <= head_protect + tail_protect:
        # Nothing to compress — all entries are protected
        return context

    head_keys = keys[:head_protect]
    tail_keys = keys[-tail_protect:] if tail_protect > 0 else []
    middle_keys = [k for k in keys if k not in head_keys and k not in tail_keys]

    if not middle_keys:
        return context

    # Calculate how much space head+tail already use
    protected_size = sum(
        len(context[k]) for k in head_keys + tail_keys
    )
    summary_budget = max(target - protected_size, 500)

    # Build summary of middle section
    middle_text = "\n\n".join(
        f"[{k}]:\n{context[k][:3000]}" for k in middle_keys
    )

    if llm_fn:
        try:
            prompt = _SUMMARY_PROMPT.format(
                target_chars=summary_budget,
                artifacts=middle_text[:20_000],  # Cap input to summarizer
            )
            summary = llm_fn(prompt)
            summary = summary[:summary_budget]
        except Exception as e:
            logger.warning(f"Compression LLM call failed, using truncation: {e}")
            summary = _truncate_middle(middle_text, summary_budget)
    else:
        summary = _truncate_middle(middle_text, summary_budget)

    # Rebuild context
    result: Dict[str, str] = {}
    for k in head_keys:
        result[k] = context[k]

    # Insert compressed summary as a single entry
    marker = _COMPRESSION_MARKER.format(count=len(middle_keys))
    result["_compressed_context"] = f"{marker}\n\n{summary}"

    for k in tail_keys:
        result[k] = context[k]

    return result


def _truncate_middle(text: str, budget: int) -> str:
    """Simple truncation fallback when LLM is unavailable."""
    if len(text) <= budget:
        return text
    # Keep first 40% and last 40%, truncate middle
    head = budget * 2 // 5
    tail = budget * 2 // 5
    return (
        text[:head]
        + f"\n\n...[{len(text) - head - tail} chars omitted]...\n\n"
        + text[-tail:]
    )
