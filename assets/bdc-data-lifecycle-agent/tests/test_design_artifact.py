"""Test design_artifact — verifies definition generated for each supported type."""
import pytest
from tests._helpers import parse_result
from tools import _design_artifact


@pytest.mark.parametrize("artifact_type", ["SQLView", "GraphicalView", "TransformationFlow", "AnalyticModel"])
def test_design_artifact_supported_types(artifact_type):
    result = parse_result(_design_artifact(
        description="Show revenue by region",
        artifact_type=artifact_type,
        space_id="space_01",
    ))
    assert result["tool"] == "design_artifact"
    assert result["artifact_type"] == artifact_type


def test_design_artifact_invalid_type():
    result = parse_result(_design_artifact(
        description="Something",
        artifact_type="InvalidType",
        space_id="space_01",
    ))
    assert "error" in result


def test_design_artifact_captures_space_id():
    result = parse_result(_design_artifact(
        description="Revenue view",
        artifact_type="SQLView",
        space_id="my_space",
    ))
    assert result["definition"]["space"] == "my_space"
