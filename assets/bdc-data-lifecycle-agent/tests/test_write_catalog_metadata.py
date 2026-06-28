"""Test write_catalog_metadata — refuses without confirmation; calls Metadata Mgmt MCP when confirmed."""
from tests._helpers import parse_result
from tools import _write_catalog_metadata, _confirmed_actions


def test_write_refuses_without_confirmation():
    _confirmed_actions.discard("write_catalog_metadata:UnconfirmedMeta")
    result = parse_result(_write_catalog_metadata(product_name="UnconfirmedMeta"))
    assert "error" in result


def test_write_succeeds_when_confirmed():
    result = parse_result(_write_catalog_metadata(
        product_name="ConfirmedMeta",
        description="My description",
        owner="My Team",
        tags='["tag1"]',
        confirmed=True,
    ))
    assert result["tool"] == "write_catalog_metadata"
    assert result["status"] == "metadata_written"


def test_write_reports_completeness_gaps():
    result = parse_result(_write_catalog_metadata(
        product_name="IncompleteMeta",
        description="",
        owner="",
        tags="[]",
        confirmed=True,
    ))
    assert len(result["completeness_gaps"]) > 0


def test_write_no_gaps_when_complete():
    result = parse_result(_write_catalog_metadata(
        product_name="CompleteMeta",
        description="Full description",
        owner="Team X",
        tags='["a", "b"]',
        confirmed=True,
    ))
    assert result["completeness_gaps"] == []
