"""Test publish_to_sac — refuses without confirmation; calls SAC MCP when confirmed; M5 log."""
import logging
from tests._helpers import parse_result
from tools import _publish_to_sac, _confirmed_actions


def test_publish_refuses_without_confirmation():
    _confirmed_actions.discard("publish_to_sac:UnconfirmedSAC")
    result = parse_result(_publish_to_sac(product_name="UnconfirmedSAC"))
    assert "error" in result


def test_publish_succeeds_when_confirmed():
    result = parse_result(_publish_to_sac(product_name="ConfirmedSAC", confirmed=True))
    assert result["tool"] == "publish_to_sac"
    assert result["status"] == "published"


def test_publish_returns_sac_url():
    result = parse_result(_publish_to_sac(product_name="MyProduct", confirmed=True))
    assert "sac_url" in result
    assert "myproduct" in result["sac_url"].lower()


def test_publish_emits_m5_achieved_log(caplog):
    with caplog.at_level(logging.INFO):
        _publish_to_sac(product_name="M5Product", confirmed=True)
    assert any("M5.achieved" in r.message for r in caplog.records)


def test_publish_warns_m5_missed_when_refused(caplog):
    _confirmed_actions.discard("publish_to_sac:M5MissProduct")
    with caplog.at_level(logging.WARNING):
        _publish_to_sac(product_name="M5MissProduct")
    assert any("M5.missed" in r.message for r in caplog.records)
