"""Shared test fixtures for HiveShip test suite."""

import os
import pathlib
import tempfile

import pytest

# Set TESTING flag before any hiveship imports to skip credential fast-fail
os.environ["TESTING"] = "1"


@pytest.fixture
def tmp_workspace(tmp_path):
    """Provide a temporary workspace directory for file I/O tests."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def tmp_artifacts(tmp_path):
    """Provide a temporary artifacts directory for DAG tests."""
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    return artifacts
