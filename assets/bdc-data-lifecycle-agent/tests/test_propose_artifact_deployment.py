"""Test propose_artifact_deployment — verifies plan presented, no deployment called."""
from tests._helpers import parse_result
from tools import _propose_artifact_deployment


def test_propose_deployment_returns_plan():
    result = parse_result(_propose_artifact_deployment(
        artifact_name="RevenueView",
        artifact_type="SQLView",
        space_id="space_01",
        artifact_definition='{"type": "SQLView"}',
    ))
    assert "AWAITING USER CONFIRMATION" in result["plan"]


def test_propose_deployment_does_not_deploy():
    result = parse_result(_propose_artifact_deployment(
        artifact_name="TestArtifact",
        artifact_type="GraphicalView",
        space_id="space_02",
        artifact_definition="{}",
    ))
    assert result["tool"] == "propose_artifact_deployment"
    assert "deployment_initiated" not in str(result)
