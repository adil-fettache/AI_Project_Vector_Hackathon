"""Test propose_connection_plan — verifies plan presented, no registration called."""
from tests._helpers import parse_result
from tools import _propose_connection_plan


def test_propose_connection_returns_plan():
    result = parse_result(_propose_connection_plan(
        system_name="Jira",
        protocol="REST",
        connection_params='{"base_url": "https://jira.example.com"}',
        target_space="space_01",
    ))
    assert "AWAITING USER CONFIRMATION" in result["plan"]


def test_propose_connection_does_not_register():
    result = parse_result(_propose_connection_plan(
        system_name="PG",
        protocol="JDBC",
        connection_params='{"host": "db.example.com"}',
        target_space="space_02",
    ))
    assert result["tool"] == "propose_connection_plan"
    assert "register" not in str(result.get("status", ""))
