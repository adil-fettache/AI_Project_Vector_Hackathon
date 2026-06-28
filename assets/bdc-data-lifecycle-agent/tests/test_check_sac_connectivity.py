"""Test check_sac_connectivity — mocks SAC MCP, verifies connectivity status."""
from tests._helpers import parse_result
from tools import _check_sac_connectivity


def test_check_sac_returns_tool_name():
    result = parse_result(_check_sac_connectivity())
    assert result["tool"] == "check_sac_connectivity"


def test_check_sac_returns_status():
    result = parse_result(_check_sac_connectivity())
    assert result["status"] == "connected"


def test_check_sac_returns_capabilities():
    result = parse_result(_check_sac_connectivity())
    assert isinstance(result["capabilities"], list)
    assert len(result["capabilities"]) > 0
