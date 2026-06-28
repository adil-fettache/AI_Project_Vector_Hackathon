"""Test get_data_product_details tool."""
from tests._helpers import parse_result
from tools import _get_data_product_details


def test_get_details_returns_tool_name():
    result = parse_result(_get_data_product_details(product_name="SalesOrder"))
    assert result["tool"] == "get_data_product_details"


def test_get_details_captures_product_name():
    result = parse_result(_get_data_product_details(product_name="MyProduct"))
    assert result["product_name"] == "MyProduct"
