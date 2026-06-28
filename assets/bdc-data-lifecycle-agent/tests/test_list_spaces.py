"""Test list_spaces tool."""
import pytest
from tests._helpers import parse_result
from tools import _list_spaces


def test_list_spaces_returns_tool_name():
    result = parse_result(_list_spaces())
    assert result["tool"] == "list_spaces"


def test_list_spaces_respects_top_limit():
    result = parse_result(_list_spaces(top=200))
    assert result["top"] <= 100


def test_list_spaces_default_top():
    result = parse_result(_list_spaces())
    assert result["top"] == 100
