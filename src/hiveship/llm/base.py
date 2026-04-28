"""Abstract base for LLM model adapters, usage tracking, and cost estimation."""

import time
from dataclasses import dataclass, field
from typing import Dict, Protocol, runtime_checkable


@runtime_checkable
class LLMModel(Protocol):
    """Protocol that all LLM adapters must satisfy."""

    def generate_content(self, prompt: str, generation_config: dict | None = None):
        """Generate content from a prompt. Returns a response with .candidates."""
        ...


@dataclass
class UsageRecord:
    """Token usage and cost data from a single LLM call."""
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    estimated_cost_usd: float = 0.0
    timestamp: float = field(default_factory=time.time)


# Per-model pricing (cost per 1M tokens in USD)
# Source: official docs snapshots as of 2025
PRICING: Dict[str, Dict[str, float]] = {
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    # Ollama / local models are free
    "ollama": {"input": 0.0, "output": 0.0},
}


def estimate_cost(usage: UsageRecord) -> float:
    """Estimate USD cost for a usage record based on PRICING table."""
    # Find best matching model key
    model_lower = usage.model.lower()
    prices = PRICING.get(usage.model, None)
    if prices is None:
        # Try prefix matching
        for key, p in PRICING.items():
            if model_lower.startswith(key) or key in model_lower:
                prices = p
                break
    if prices is None:
        prices = PRICING.get("ollama", {"input": 0.0, "output": 0.0})

    cost = (
        (usage.input_tokens / 1_000_000) * prices["input"]
        + (usage.output_tokens / 1_000_000) * prices["output"]
    )
    return round(cost, 8)


def make_usage(
    input_tokens: int = 0,
    output_tokens: int = 0,
    model: str = "",
) -> UsageRecord:
    """Create a UsageRecord with auto-calculated cost."""
    rec = UsageRecord(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=model,
    )
    rec.estimated_cost_usd = estimate_cost(rec)
    return rec
