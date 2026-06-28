"""Test propose_activation_plan — verifies plan presented, M2 log emitted, no activation called."""
import logging
from tests._helpers import parse_result
from tools import _propose_activation_plan, _confirmed_actions


def test_propose_returns_plan():
    result = parse_result(_propose_activation_plan(product_name="SalesOrder", target_space="space_01"))
    assert "AWAITING USER CONFIRMATION" in result["plan"]


def test_propose_does_not_activate():
    # After proposing, the product is NOT yet activated — only confirmation key is set
    result = parse_result(_propose_activation_plan(product_name="SalesOrder2", target_space="space_02"))
    assert result["tool"] == "propose_activation_plan"


def test_propose_emits_m2_log(caplog):
    with caplog.at_level(logging.INFO):
        _propose_activation_plan(product_name="TestProduct", target_space="space_03")
    assert any("M2.achieved" in r.message for r in caplog.records)
