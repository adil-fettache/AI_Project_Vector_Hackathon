"""Test list_connections tool."""
from tests._helpers import parse_result
from tools import _list_connections


def test_list_connections_returns_tool_name():
    result = parse_result(_list_connections())
    assert result["tool"] == "list_connections"


def test_list_connections_respects_top_limit():
    result = parse_result(_list_connections(top=500))
    assert result["top"] <= 100


def test_list_connections_default_top():
    result = parse_result(_list_connections())
    assert result["top"] == 100
