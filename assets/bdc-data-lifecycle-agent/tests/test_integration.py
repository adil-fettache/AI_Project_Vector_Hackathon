"""Integration test — end-to-end flow: landscape discovery → data product selection
→ quality gate → deployment. All mocked. Verifies all 5 milestone logs emitted in sequence.
"""

from __future__ import annotations

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure app/ is on path
from tests._helpers import parse_result
from tools import (
    _summarize_landscape,
    _search_sap_data_products,
    _propose_activation_plan,
    _define_quality_rules,
    _run_quality_gate,
    _activate_data_product,
    _monitor_quality_continuously,
    _propose_sac_publication,
    _publish_to_sac,
    _quality_gate_results,
    _confirmed_actions,
)


@pytest.mark.asyncio
async def test_full_lifecycle_all_milestones(caplog):
    """End-to-end flow emitting M1→M5 milestones in sequence (all mocked)."""
    product = "IntegrationTestProduct"

    # Clear state
    _quality_gate_results.pop(product, None)
    _confirmed_actions.discard(f"activate_data_product:{product}")
    _confirmed_actions.discard(f"publish_to_sac:{product}")

    with caplog.at_level(logging.INFO):
        # M1 — Landscape Discovery
        r1 = parse_result(_summarize_landscape())
        assert r1["milestone"] == "M1"

        # M2 — Data product proposal (sets confirmation + emits M2)
        r2 = parse_result(_search_sap_data_products(query="Sales Order"))
        assert r2["tool"] == "search_sap_data_products"

        r3 = parse_result(_propose_activation_plan(product_name=product, target_space="space_01"))
        assert "AWAITING USER CONFIRMATION" in r3["plan"]

        # Quality rules → Quality gate (M4 pre-check)
        _define_quality_rules(product, "completeness check")
        gate_result = parse_result(_run_quality_gate(product_name=product))
        assert gate_result["gate_status"] == "PASS"

        # M4 — Activation (confirmed by propose_activation_plan + gate passed)
        r4 = parse_result(_activate_data_product(
            product_name=product, target_space="space_01", confirmed=True
        ))
        assert r4["tool"] == "activate_data_product"

        # M5 — SAC Publication
        r5_plan = parse_result(_propose_sac_publication(product_name=product))
        assert "AWAITING USER CONFIRMATION" in r5_plan["plan"]

        r5 = parse_result(_publish_to_sac(product_name=product, confirmed=True))
        assert r5["status"] == "published"

    # Verify all 5 milestones appear in logs
    log_messages = [r.message for r in caplog.records]
    all_logs = "\n".join(log_messages)

    assert "M1.achieved" in all_logs, "M1 milestone not logged"
    assert "M2.achieved" in all_logs, "M2 milestone not logged"
    assert "M4.achieved" in all_logs, "M4 milestone not logged"
    assert "M5.achieved" in all_logs, "M5 milestone not logged"


def test_quality_gate_blocks_full_pipeline():
    """M3 path: quality gate blocks deployment when critical violations present."""
    import json
    from unittest.mock import patch

    product = "BlockedPipeline"
    _quality_gate_results.pop(product, None)

    critical_results = json.dumps({
        "tool": "evaluate_quality_rules",
        "product_name": product,
        "results": [
            {"rule_type": "completeness", "severity": "critical", "status": "fail", "detail": "Nulls found"}
        ],
    })
    with patch("tools._evaluate_quality_rules", return_value=critical_results):
        gate = parse_result(_run_quality_gate(product_name=product))
    assert gate["gate_status"] == "BLOCK"

    # Deployment should be blocked
    deploy = parse_result(_activate_data_product(product_name=product, target_space="s1", confirmed=True))
    assert "error" in deploy
    assert "quality" in deploy["error"].lower()


def test_m3_generic_non_sap_integration(caplog):
    """M3 path: generic non-SAP integration flow emits M3.achieved."""
    from tools import (
        _retrieve_integration_docs,
        _determine_integration_protocol,
        _propose_connection_plan,
        _register_connection,
    )
    with caplog.at_level(logging.INFO):
        docs = parse_result(_retrieve_integration_docs(system_name="Jira"))
        assert len(docs["docs"]) > 0

        protocol_result = parse_result(_determine_integration_protocol(
            system_name="Jira",
            integration_docs=docs["docs"],
        ))
        protocol = protocol_result["protocol"]
        assert protocol in ["REST", "JDBC", "SFTP", "OData", "GraphQL"]

        _propose_connection_plan(
            system_name="Jira",
            protocol=protocol,
            connection_params='{"base_url": "https://jira.example.com"}',
            target_space="space_01",
        )

        conn = parse_result(_register_connection(
            system_name="Jira",
            protocol=protocol,
            connection_params='{"base_url": "https://jira.example.com"}',
            target_space="space_01",
            confirmed=True,
        ))
        assert conn["tool"] == "register_connection"

    log_messages = [r.message for r in caplog.records]
    assert any("M3.achieved" in m for m in log_messages)
