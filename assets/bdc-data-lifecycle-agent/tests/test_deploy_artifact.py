"""Test deploy_artifact — refuses without confirmation; calls Tasks MCP when confirmed + gate passed."""
import logging
from tests._helpers import parse_result
from tools import _deploy_artifact, _quality_gate_results, _confirmed_actions


def test_deploy_refuses_without_confirmation():
    _confirmed_actions.discard("deploy_artifact:UnconfirmedArtifact")
    _quality_gate_results.pop("UnconfirmedArtifact", None)
    result = parse_result(_deploy_artifact(
        artifact_name="UnconfirmedArtifact",
        artifact_type="SQLView",
        space_id="space_01",
    ))
    assert "error" in result


def test_deploy_blocks_without_quality_gate():
    _quality_gate_results.pop("NoGateArtifact", None)
    result = parse_result(_deploy_artifact(
        artifact_name="NoGateArtifact",
        artifact_type="SQLView",
        space_id="space_01",
        confirmed=True,
    ))
    assert "error" in result
    assert "quality" in result["error"].lower()


def test_deploy_succeeds_when_confirmed_and_gate_passed():
    product = "ReadyArtifact"
    _quality_gate_results[product] = "PASS"
    result = parse_result(_deploy_artifact(
        artifact_name=product,
        artifact_type="SQLView",
        space_id="space_01",
        confirmed=True,
    ))
    assert result["tool"] == "deploy_artifact"
    assert result["status"] == "deployment_initiated"


def test_deploy_emits_m4_achieved_log(caplog):
    product = "M4ArtifactPass"
    _quality_gate_results[product] = "PASS"
    with caplog.at_level(logging.INFO):
        _deploy_artifact(artifact_name=product, artifact_type="SQLView", space_id="s1", confirmed=True)
    assert any("M4.achieved" in r.message for r in caplog.records)


def test_deploy_warns_m4_missed_when_refused(caplog):
    _confirmed_actions.discard("deploy_artifact:M4MissArtifact")
    _quality_gate_results.pop("M4MissArtifact", None)
    with caplog.at_level(logging.WARNING):
        _deploy_artifact(artifact_name="M4MissArtifact", artifact_type="SQLView", space_id="s1")
    assert any("M4.missed" in r.message for r in caplog.records)
