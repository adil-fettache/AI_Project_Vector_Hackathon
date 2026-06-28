"""Test propose_sac_publication — verifies plan presented, no publish called."""
from tests._helpers import parse_result
from tools import _propose_sac_publication


def test_propose_sac_returns_plan():
    result = parse_result(_propose_sac_publication(product_name="SalesOrder"))
    assert "AWAITING USER CONFIRMATION" in result["plan"]


def test_propose_sac_does_not_publish():
    result = parse_result(_propose_sac_publication(product_name="TestDP"))
    assert result["tool"] == "propose_sac_publication"
    assert "published" not in str(result.get("status", ""))


def test_propose_sac_captures_model_type():
    result = parse_result(_propose_sac_publication(product_name="DP", model_type="import"))
    assert result["model_type"] == "import"
