"""Unit tests for Pydantic models."""

import pytest

from hiveship.models import (
    AgentTask,
    DeliveryPlan,
    FileArtifact,
    WorkflowPlan,
)


def test_workflow_plan_rejects_cycles():
    """DAG validator should reject circular dependencies."""
    with pytest.raises(ValueError, match="cycle"):
        WorkflowPlan(
            team_name="test",
            agents=[
                AgentTask(
                    agent_name="a", role_description="r",
                    depends_on=["b"], input_keys=["x"], output_format="text",
                ),
                AgentTask(
                    agent_name="b", role_description="r",
                    depends_on=["a"], input_keys=["x"], output_format="text",
                ),
            ],
        )


def test_workflow_plan_rejects_unknown_dep():
    """DAG validator should reject references to non-existent agents."""
    with pytest.raises(ValueError, match="unknown agent"):
        WorkflowPlan(
            team_name="test",
            agents=[
                AgentTask(
                    agent_name="a", role_description="r",
                    depends_on=["nonexistent"], input_keys=["x"], output_format="text",
                ),
            ],
        )


def test_file_artifact_rejects_oversized_content():
    """FileArtifact should reject content exceeding 100k chars."""
    with pytest.raises(ValueError, match="too large"):
        FileArtifact(path="test.py", content="x" * 100_001)


def test_delivery_plan_truncates_commit_msg():
    """commit_message should be truncated to 500 chars."""
    plan = DeliveryPlan(
        files=[],
        commit_message="x" * 600,
        pr_title="title",
    )
    assert len(plan.commit_message) <= 500
