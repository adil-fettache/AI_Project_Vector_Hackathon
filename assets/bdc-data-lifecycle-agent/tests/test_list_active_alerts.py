"""Test list_active_alerts — mocks Monitoring MCP, verifies alert list returned."""
from tests._helpers import parse_result
from tools import _list_active_alerts


def test_list_alerts_returns_tool_name():
    result = parse_result(_list_active_alerts(product_name="SalesOrder"))
    assert result["tool"] == "list_active_alerts"


def test_list_alerts_returns_list():
    result = parse_result(_list_active_alerts(product_name="SalesOrder"))
    assert isinstance(result["alerts"], list)


def test_list_alerts_respects_top():
    result = parse_result(_list_active_alerts(product_name="SalesOrder", top=500))
    assert "top=100" in result["note"] or result.get("count", 0) <= 100
