"""Test run_quality_gate — PASS on no critical violations; BLOCK on critical violation; M4 log."""
import logging
from tests._helpers import parse_result
from tools import (
    _define_quality_rules, _run_quality_gate, _quality_rules, _quality_gate_results
)


def test_quality_gate_passes_with_no_critical_violations():
    # Define only info-severity rules (no critical)
    _quality_rules["PassDP"] = [{"type": "info_check", "severity": "info", "description": "info rule"}]
    result = parse_result(_run_quality_gate(product_name="PassDP"))
    assert result["gate_status"] == "PASS"
    assert result["critical_violations"] == 0


def test_quality_gate_blocks_with_critical_violation():
    # Inject a critical rule that FAILS evaluation
    # Manually set a failing rule to force BLOCK
    import json
    # Override evaluate to return a critical failure by setting a rule with critical + non-pass status
    # We need to patch _evaluate_quality_rules to return a critical failure
    # Instead: directly set gate result via a product with no rules (returns pass)
    # For BLOCK, we mock the evaluate result indirectly by patching
    from unittest.mock import patch
    critical_results = json.dumps({
        "tool": "evaluate_quality_rules",
        "product_name": "BlockDP",
        "results": [
            {"rule_type": "completeness", "severity": "critical", "status": "fail", "detail": "Null values found"}
        ],
    })
    with patch("tools._evaluate_quality_rules", return_value=critical_results):
        result = parse_result(_run_quality_gate(product_name="BlockDP"))
    assert result["gate_status"] == "BLOCK"
    assert result["critical_violations"] > 0


def test_quality_gate_emits_m4_achieved_on_pass(caplog):
    _quality_rules["M4PassDP"] = []
    with caplog.at_level(logging.INFO):
        _run_quality_gate(product_name="M4PassDP")
    assert any("M4.achieved" in r.message for r in caplog.records)


def test_quality_gate_emits_m4_missed_on_block(caplog):
    import json
    from unittest.mock import patch
    critical_results = json.dumps({
        "tool": "evaluate_quality_rules",
        "product_name": "M4BlockDP",
        "results": [
            {"rule_type": "completeness", "severity": "critical", "status": "fail", "detail": "Failed"}
        ],
    })
    with patch("tools._evaluate_quality_rules", return_value=critical_results):
        with caplog.at_level(logging.WARNING):
            _run_quality_gate(product_name="M4BlockDP")
    assert any("M4.missed" in r.message for r in caplog.records)


def test_quality_gate_result_stored():
    _quality_rules["StoredGateDP"] = []
    _run_quality_gate(product_name="StoredGateDP")
    assert _quality_gate_results.get("StoredGateDP") == "PASS"
