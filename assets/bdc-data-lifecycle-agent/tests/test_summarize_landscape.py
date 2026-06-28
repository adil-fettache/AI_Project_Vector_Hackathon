"""Test summarize_landscape tool — verifies M1 milestone log is emitted."""
import logging
from tests._helpers import parse_result
from tools import _summarize_landscape


def test_summarize_landscape_returns_tool_name():
    result = parse_result(_summarize_landscape())
    assert result["tool"] == "summarize_landscape"


def test_summarize_landscape_milestone_key():
    result = parse_result(_summarize_landscape())
    assert result["milestone"] == "M1"


def test_summarize_landscape_emits_m1_log(caplog):
    with caplog.at_level(logging.INFO):
        _summarize_landscape()
    assert any("M1.achieved" in r.message for r in caplog.records)
