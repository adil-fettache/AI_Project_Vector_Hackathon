"""Test evaluate_quality_rules — mocks DQM MCP, verifies per-rule results."""
from tests._helpers import parse_result
from tools import _define_quality_rules, _evaluate_quality_rules


def test_evaluate_returns_tool_name():
    _define_quality_rules("EvalDP", "completeness check")
    result = parse_result(_evaluate_quality_rules(product_name="EvalDP"))
    assert result["tool"] == "evaluate_quality_rules"


def test_evaluate_returns_per_rule_results():
    _define_quality_rules("RuleDP", "completeness and freshness check")
    result = parse_result(_evaluate_quality_rules(product_name="RuleDP"))
    assert isinstance(result["results"], list)
    assert len(result["results"]) >= 2


def test_evaluate_no_rules_returns_empty():
    result = parse_result(_evaluate_quality_rules(product_name="EmptyDP_no_rules_defined"))
    assert result["results"] == []
