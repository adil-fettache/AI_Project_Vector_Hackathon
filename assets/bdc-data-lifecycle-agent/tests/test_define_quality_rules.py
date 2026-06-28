"""Test define_quality_rules — verifies rules structured and stored in context."""
from tests._helpers import parse_result
from tools import _define_quality_rules, _quality_rules


def test_define_rules_completeness():
    result = parse_result(_define_quality_rules(
        product_name="SalesDP",
        rules_description="Ensure completeness of all key fields",
    ))
    assert result["stored"] is True
    types = [r["type"] for r in result["rules"]]
    assert "completeness" in types


def test_define_rules_freshness():
    result = parse_result(_define_quality_rules(
        product_name="FresnessDP",
        rules_description="Check data freshness within 24 hours",
    ))
    types = [r["type"] for r in result["rules"]]
    assert "freshness" in types


def test_define_rules_referential_integrity():
    result = parse_result(_define_quality_rules(
        product_name="IntDP",
        rules_description="Ensure referential integrity of foreign keys",
    ))
    types = [r["type"] for r in result["rules"]]
    assert "referential_integrity" in types


def test_define_rules_stored_in_context():
    _quality_rules.pop("StoredDP", None)
    _define_quality_rules(product_name="StoredDP", rules_description="completeness check")
    assert "StoredDP" in _quality_rules
    assert len(_quality_rules["StoredDP"]) > 0


def test_define_rules_custom_fallback():
    result = parse_result(_define_quality_rules(
        product_name="CustomDP",
        rules_description="My custom rule with no keywords",
    ))
    types = [r["type"] for r in result["rules"]]
    assert "custom" in types
