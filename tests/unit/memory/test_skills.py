"""Tests for hiveship.memory.skills — SkillStore discover, load, create, patch."""

import pytest

from hiveship.memory.skills import (
    SkillStore,
    _parse_frontmatter,
    build_skill_index_for_prompt,
    build_skill_content_for_agent,
)


@pytest.fixture
def skill_store(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    return SkillStore(ws)


SAMPLE_SKILL = """---
name: add-api-endpoint
description: How to add a new REST API endpoint
version: 1.0.0
tags: [api, backend]
---

# Add API Endpoint

1. Create route file in src/routes/
2. Register in app.py
3. Add tests in tests/
"""


def test_parse_frontmatter():
    """YAML frontmatter is parsed correctly."""
    meta, body = _parse_frontmatter(SAMPLE_SKILL)
    assert meta["name"] == "add-api-endpoint"
    assert meta["version"] == "1.0.0"
    assert meta["tags"] == ["api", "backend"]
    assert "Create route file" in body


def test_parse_frontmatter_no_yaml():
    """Content without frontmatter returns empty metadata."""
    meta, body = _parse_frontmatter("# Just markdown\n\nSome text")
    assert meta == {}
    assert "Just markdown" in body


def test_create_and_discover(skill_store):
    """Created skills are discoverable."""
    skill_store.create("test-skill", SAMPLE_SKILL)
    skills = skill_store.discover()
    assert len(skills) == 1
    assert skills[0].name == "add-api-endpoint"
    assert skills[0].description == "How to add a new REST API endpoint"
    assert skills[0].source == "repo"


def test_load(skill_store):
    """Loading a skill returns full content."""
    skill_store.create("test-skill", SAMPLE_SKILL)
    skill = skill_store.load("test-skill")
    assert skill is not None
    assert skill.name == "add-api-endpoint"
    assert "Create route file" in skill.content
    assert skill.version == "1.0.0"


def test_load_nonexistent(skill_store):
    """Loading a non-existent skill returns None."""
    assert skill_store.load("nope") is None


def test_patch(skill_store):
    """Patch updates content via find/replace."""
    skill_store.create("test-skill", SAMPLE_SKILL)
    success = skill_store.patch("test-skill", "version: 1.0.0", "version: 1.0.1")
    assert success
    skill = skill_store.load("test-skill")
    assert skill.version == "1.0.1"


def test_patch_nonexistent(skill_store):
    """Patching a non-existent skill returns False."""
    assert not skill_store.patch("nope", "old", "new")


def test_update(skill_store):
    """Full rewrite of skill content."""
    skill_store.create("test-skill", SAMPLE_SKILL)
    new_content = SAMPLE_SKILL.replace("1.0.0", "2.0.0")
    success = skill_store.update("test-skill", new_content)
    assert success
    skill = skill_store.load("test-skill")
    assert skill.version == "2.0.0"


def test_delete(skill_store):
    """Delete removes skill directory."""
    skill_store.create("test-skill", SAMPLE_SKILL)
    assert skill_store.delete("test-skill")
    assert skill_store.load("test-skill") is None


def test_build_skill_index(skill_store):
    """Skill index is formatted for planner prompt."""
    skill_store.create("test-skill", SAMPLE_SKILL)
    skills = skill_store.discover()
    index = build_skill_index_for_prompt(skills)
    assert "add-api-endpoint" in index
    assert "Available Procedures" in index


def test_build_skill_index_empty(skill_store):
    """Empty skill list produces empty index."""
    assert build_skill_index_for_prompt([]) == ""


def test_build_skill_content_for_agent(skill_store):
    """Full skill content loaded for agent injection."""
    skill_store.create("test-skill", SAMPLE_SKILL)
    content = build_skill_content_for_agent(["test-skill"], skill_store)
    assert "Create route file" in content
    assert "[Skill: add-api-endpoint" in content


def test_build_skill_content_budget(skill_store):
    """Skill content respects budget limit."""
    long_content = "---\nname: big\ndescription: big skill\nversion: 1.0.0\n---\n" + "x" * 10000
    skill_store.create("big-skill", long_content)
    content = build_skill_content_for_agent(["big-skill"], skill_store, budget=500)
    assert len(content) <= 600  # Some overhead from header
