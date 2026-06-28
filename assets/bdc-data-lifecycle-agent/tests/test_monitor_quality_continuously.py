"""Test monitor_quality_continuously — mocks Monitoring MCP, verifies rules registered."""
from tests._helpers import parse_result
from tools import _define_quality_rules, _monitor_quality_continuously


def test_monitor_returns_tool_name():
    result = parse_result(_monitor_quality_continuously(product_name="MonitorDP"))
    assert result["tool"] == "monitor_quality_continuously"


def test_monitor_returns_monitoring_status():
    result = parse_result(_monitor_quality_continuously(product_name="MonitorDP"))
    assert result["status"] == "monitoring_registered"


def test_monitor_includes_registered_rules():
    _define_quality_rules("MonitoredRuleDP", "completeness check")
    result = parse_result(_monitor_quality_continuously(product_name="MonitoredRuleDP"))
    assert isinstance(result["registered_rules"], list)
    assert len(result["registered_rules"]) > 0
