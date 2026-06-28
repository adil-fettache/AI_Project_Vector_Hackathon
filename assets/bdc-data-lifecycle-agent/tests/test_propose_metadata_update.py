"""Test propose_metadata_update — verifies proposal presented, no write called."""
from tests._helpers import parse_result
from tools import _propose_metadata_update


def test_propose_metadata_returns_plan():
    result = parse_result(_propose_metadata_update(
        product_name="SalesOrder",
        description="Sales order data",
        owner="Finance Team",
        tags='["sales", "order"]',
    ))
    assert "AWAITING USER CONFIRMATION" in result["plan"]


def test_propose_metadata_does_not_write():
    result = parse_result(_propose_metadata_update(
        product_name="TestDP",
        description="Test",
        owner="Me",
    ))
    assert result["tool"] == "propose_metadata_update"
    assert "metadata_written" not in str(result)
