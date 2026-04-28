"""Unit tests for workspace repo utilities."""

from hiveship.workspace.repo import sanitize_branch_name


def test_sanitize_branch_name_removes_special_chars():
    assert sanitize_branch_name("feat: add stuff!") == "feat-add-stuff"


def test_sanitize_branch_name_truncates():
    long_name = "a" * 100
    result = sanitize_branch_name(long_name)
    assert len(result) <= 50


def test_sanitize_branch_name_collapses_dashes():
    assert sanitize_branch_name("a---b---c") == "a-b-c"
