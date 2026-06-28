"""Test read_catalog_metadata — mocks Catalog MCP, verifies metadata returned."""
from tests._helpers import parse_result
from tools import _read_catalog_metadata


def test_read_metadata_returns_tool_name():
    result = parse_result(_read_catalog_metadata(product_name="SalesOrder"))
    assert result["tool"] == "read_catalog_metadata"


def test_read_metadata_contains_required_fields():
    result = parse_result(_read_catalog_metadata(product_name="SalesOrder"))
    meta = result["metadata"]
    assert "description" in meta
    assert "owner" in meta
    assert "tags" in meta
    assert "lineage" in meta


def test_read_metadata_captures_product_name():
    result = parse_result(_read_catalog_metadata(product_name="MyProduct"))
    assert result["product_name"] == "MyProduct"
