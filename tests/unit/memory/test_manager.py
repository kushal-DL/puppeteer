"""Tests for hiveship.memory.manager — MemoryManager lifecycle."""

import pytest

from hiveship.memory.manager import MemoryManager


@pytest.fixture
def mgr(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    return MemoryManager(ws)


def test_prefetch_empty(mgr):
    """Prefetch on empty workspace returns empty string."""
    result = mgr.prefetch()
    assert result == ""
    assert not mgr.has_memory()


def test_prefetch_loads_existing(mgr):
    """Prefetch loads existing memory.md."""
    mem_dir = mgr.store.workspace / ".hiveship"
    mem_dir.mkdir(parents=True)
    (mem_dir / "memory.md").write_text(
        "- Uses pytest\n- CI requires Node 18\n", encoding="utf-8"
    )
    result = mgr.prefetch()
    assert "pytest" in result
    assert mgr.has_memory()


def test_build_memory_context_block_empty(mgr):
    """Empty memory produces empty context block."""
    mgr.prefetch()
    block = mgr.build_memory_context_block()
    assert block == ""


def test_build_memory_context_block_with_content(mgr):
    """Non-empty memory is wrapped in safety fences."""
    mgr.store.add("Uses pytest")
    mgr.prefetch()
    block = mgr.build_memory_context_block()
    assert "<memory-context>" in block
    assert "</memory-context>" in block
    assert "NOT new user input" in block
    assert "Uses pytest" in block


def test_frozen_snapshot(mgr):
    """Snapshot is frozen at prefetch time — mutations don't affect it."""
    mgr.store.add("Original fact")
    mgr.prefetch()
    mgr.store.add("New fact added mid-run")
    block = mgr.build_memory_context_block()
    assert "Original fact" in block
    assert "New fact added mid-run" not in block


def test_build_extraction_prompt(mgr):
    """Extraction prompt includes goal and file paths."""
    mgr.prefetch()
    prompt = mgr.build_extraction_prompt("Add REST API", ["src/app.py", "src/routes.py"])
    assert "Add REST API" in prompt
    assert "src/app.py" in prompt
    assert "JSON array" in prompt


def test_apply_extracted_entries(mgr):
    """Extracted entries are added to store (max 5)."""
    entries = [f"Fact {i}" for i in range(8)]
    errors = mgr.apply_extracted_entries(entries)
    assert len(errors) == 0
    assert len(mgr.store) == 5  # Capped at 5
