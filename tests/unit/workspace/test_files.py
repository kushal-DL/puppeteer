"""Unit tests for workspace file operations."""

import pathlib

import pytest

from hiveship.models import FileArtifact
from hiveship.workspace.files import validate_files, write_files, validate_cross_references


def test_validate_files_blocks_path_traversal(tmp_workspace):
    """Path traversal attempts should be rejected."""
    files = [FileArtifact(path="../escape.py", content="bad")]
    with pytest.raises(ValueError, match="Path traversal"):
        validate_files(files, tmp_workspace)


def test_validate_files_blocks_protected_paths(tmp_workspace):
    """Writes to .git, .env, .github should be rejected."""
    files = [FileArtifact(path=".env", content="SECRET=bad")]
    with pytest.raises(ValueError, match="Protected path"):
        validate_files(files, tmp_workspace)


def test_write_files_creates_nested_dirs(tmp_workspace):
    """write_files should create intermediate directories."""
    files = [FileArtifact(path="deep/nested/file.py", content="# hello")]
    validate_files(files, tmp_workspace)
    write_files(files, tmp_workspace)
    assert (tmp_workspace / "deep" / "nested" / "file.py").read_text() == "# hello"


def test_validate_cross_references_catches_missing_import():
    """Should detect imports of modules not in the delivery."""
    files = [
        FileArtifact(path="main.py", content="from helpers import do_thing\n"),
    ]
    issues = validate_cross_references(files)
    assert any("helpers" in i for i in issues)


def test_validate_cross_references_passes_valid_delivery():
    """Should pass when all cross-references resolve."""
    files = [
        FileArtifact(path="main.py", content="from helpers import do_thing\n"),
        FileArtifact(path="helpers.py", content="def do_thing(): pass\n"),
    ]
    issues = validate_cross_references(files)
    assert len(issues) == 0
