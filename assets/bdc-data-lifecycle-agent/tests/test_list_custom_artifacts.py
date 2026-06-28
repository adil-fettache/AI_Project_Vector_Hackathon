"""Test list_custom_artifacts tool."""
from tests._helpers import parse_result
from tools import _list_custom_artifacts


def test_list_custom_artifacts_returns_tool_name():
    result = parse_result(_list_custom_artifacts(space_id="space_001"))
    assert result["tool"] == "list_custom_artifacts"


def test_list_custom_artifacts_returns_space_id():
    result = parse_result(_list_custom_artifacts(space_id="my_space"))
    assert result["space_id"] == "my_space"


def test_list_custom_artifacts_respects_top():
    result = parse_result(_list_custom_artifacts(space_id="s1", top=200))
    assert result["top"] <= 100
