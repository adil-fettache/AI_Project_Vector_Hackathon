"""Test list_data_products tool."""
from tests._helpers import parse_result
from tools import _list_data_products


def test_list_data_products_returns_tool_name():
    result = parse_result(_list_data_products())
    assert result["tool"] == "list_data_products"


def test_list_data_products_respects_top():
    result = parse_result(_list_data_products(top=999))
    assert result["top"] <= 100


def test_list_data_products_default_top():
    result = parse_result(_list_data_products())
    assert result["top"] == 100
