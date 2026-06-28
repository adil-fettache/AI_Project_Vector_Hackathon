"""Test get_data_product_health — mocks Monitoring Query MCP, verifies health score."""
from tests._helpers import parse_result
from tools import _get_data_product_health


def test_health_returns_tool_name():
    result = parse_result(_get_data_product_health(product_name="SalesOrder"))
    assert result["tool"] == "get_data_product_health"


def test_health_returns_score():
    result = parse_result(_get_data_product_health(product_name="SalesOrder"))
    assert "health_score" in result
    assert isinstance(result["health_score"], (int, float))


def test_health_returns_violations():
    result = parse_result(_get_data_product_health(product_name="SalesOrder"))
    assert "active_violations" in result


def test_health_returns_timestamp():
    result = parse_result(_get_data_product_health(product_name="SalesOrder"))
    assert "last_check_timestamp" in result
