"""Test activate_data_product — refuses without confirmation; activates when confirmed."""
import logging
from tests._helpers import parse_result
from tools import _activate_data_product, _quality_gate_results, _confirmed_actions


def test_activate_refuses_without_confirmation():
    # Clear any previous confirmation
    _confirmed_actions.discard("activate_data_product:UnconfirmedProduct")
    _quality_gate_results.pop("UnconfirmedProduct", None)
    result = parse_result(_activate_data_product(product_name="UnconfirmedProduct", target_space="space_01"))
    assert "error" in result


def test_activate_blocks_without_quality_gate(caplog):
    """Even with confirmed=True, blocks if quality gate not passed."""
    _quality_gate_results.pop("NoGateProduct", None)
    result = parse_result(_activate_data_product(
        product_name="NoGateProduct", target_space="space_01", confirmed=True
    ))
    assert "error" in result
    assert "quality" in result["error"].lower()


def test_activate_succeeds_when_confirmed_and_gate_passed():
    product = "ConfirmedProduct"
    _quality_gate_results[product] = "PASS"
    result = parse_result(_activate_data_product(
        product_name=product, target_space="space_01", confirmed=True
    ))
    assert result["tool"] == "activate_data_product"
    assert result["status"] == "activation_initiated"


def test_activate_warns_m2_missed_when_no_confirmation(caplog):
    _confirmed_actions.discard("activate_data_product:MissProduct")
    _quality_gate_results.pop("MissProduct", None)
    with caplog.at_level(logging.WARNING):
        _activate_data_product(product_name="MissProduct", target_space="space_01")
    assert any("M2.missed" in r.message for r in caplog.records)
