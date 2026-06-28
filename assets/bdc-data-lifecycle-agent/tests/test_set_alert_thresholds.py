"""Test set_alert_thresholds — refuses without confirmation; calls Monitoring MCP when confirmed."""
from tests._helpers import parse_result
from tools import _set_alert_thresholds, _confirmed_actions


def test_set_thresholds_refuses_without_confirmation():
    _confirmed_actions.discard("set_alert_thresholds:UnconfirmedAlert")
    result = parse_result(_set_alert_thresholds(
        product_name="UnconfirmedAlert",
        thresholds='{"health_score_min": 80}',
    ))
    assert "error" in result


def test_set_thresholds_succeeds_when_confirmed():
    result = parse_result(_set_alert_thresholds(
        product_name="ConfirmedAlert",
        thresholds='{"health_score_min": 80}',
        confirmed=True,
    ))
    assert result["tool"] == "set_alert_thresholds"
    assert result["status"] == "thresholds_configured"


def test_set_thresholds_captures_product_name():
    result = parse_result(_set_alert_thresholds(
        product_name="MyAlertProduct",
        thresholds="{}",
        confirmed=True,
    ))
    assert result["product_name"] == "MyAlertProduct"
