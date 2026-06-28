"""Test validate_connection — mocks Connections MCP, verifies active status returned."""
from tests._helpers import parse_result
from tools import _validate_connection


def test_validate_returns_tool_name():
    result = parse_result(_validate_connection(connection_id="conn_001"))
    assert result["tool"] == "validate_connection"


def test_validate_captures_connection_id():
    result = parse_result(_validate_connection(connection_id="conn_abc"))
    assert result["connection_id"] == "conn_abc"


def test_validate_returns_status():
    result = parse_result(_validate_connection(connection_id="conn_001"))
    assert result["status"] == "active"
