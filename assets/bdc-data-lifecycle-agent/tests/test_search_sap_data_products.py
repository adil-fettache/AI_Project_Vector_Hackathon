"""Test search_sap_data_products tool."""
from tests._helpers import parse_result
from tools import _search_sap_data_products


def test_search_returns_tool_name():
    result = parse_result(_search_sap_data_products(query="Sales Order"))
    assert result["tool"] == "search_sap_data_products"


def test_search_captures_query():
    result = parse_result(_search_sap_data_products(query="Finance"))
    assert result["query"] == "Finance"


def test_search_respects_top():
    result = parse_result(_search_sap_data_products(query="test", top=999))
    assert "top=100" in result["note"] or result.get("top", 100) <= 100
