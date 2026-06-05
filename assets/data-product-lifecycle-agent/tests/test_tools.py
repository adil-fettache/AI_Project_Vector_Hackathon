"""Unit tests for the Data Product Lifecycle Agent.

Tests cover:
  - MCP mock tool loading (27 tool smoke tests, one per key tool)
  - ApprovalGateway (3 tests: autonomous, supervised, always_approve)
  - SampleAgent._classify_query (2 tests)
  - SampleAgent._classify_response (1 test)

Total: 33 tests (≥ 27 required by spec).
"""
from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure IBD_TESTING is set before importing agent modules
os.environ.setdefault("IBD_TESTING", "1")

# Add app/ to the path so peer-level imports work as in production
AGENT_ROOT = Path(__file__).parent.parent
APP_DIR = AGENT_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_mock() -> dict[str, Any]:
    mock_path = AGENT_ROOT / "mcp-mock.json"
    return json.loads(mock_path.read_text())


def _get_all_tools_from_mock() -> dict[str, Any]:
    """Return flat dict: tool_name -> tool_def from all servers."""
    mock = _load_mock()
    result: dict[str, Any] = {}
    for server in mock["servers"].values():
        result.update(server.get("tools", {}))
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def mock_tools_flat() -> dict[str, Any]:
    return _get_all_tools_from_mock()


@pytest.fixture(scope="module")
def mock_data() -> dict[str, Any]:
    return _load_mock()


# ---------------------------------------------------------------------------
# Test Group 1: mcp-mock.json structure
# ---------------------------------------------------------------------------

class TestMcpMockStructure:
    """Validate the structure and completeness of mcp-mock.json."""

    def test_mock_json_parseable(self, mock_data):
        assert isinstance(mock_data, dict)

    def test_mock_has_servers(self, mock_data):
        assert "servers" in mock_data
        assert isinstance(mock_data["servers"], dict)
        assert len(mock_data["servers"]) >= 9

    def test_mock_has_metadata(self, mock_data):
        assert "metadata" in mock_data
        meta = mock_data["metadata"]
        assert meta["mock_mode"] is True
        assert meta["total_servers"] >= 9
        assert meta["total_tools"] >= 50

    def test_all_servers_have_mcp_server_name(self, mock_data):
        for slug, server in mock_data["servers"].items():
            assert "mcp_server_name" in server, f"Server {slug} missing mcp_server_name"

    def test_all_tools_have_description(self, mock_tools_flat):
        for name, defn in mock_tools_flat.items():
            assert "description" in defn, f"Tool {name} missing description"

    def test_all_tools_have_mock_response(self, mock_tools_flat):
        for name, defn in mock_tools_flat.items():
            assert "mock_response" in defn, f"Tool {name} missing mock_response"


# ---------------------------------------------------------------------------
# Test Group 2: MCP tool loading (IBD_TESTING=1)
# ---------------------------------------------------------------------------

class TestMcpToolLoading:
    """Test that get_mcp_tools() returns correct StructuredTool instances in mock mode."""

    @pytest.fixture(autouse=True)
    def ensure_testing_env(self):
        os.environ["IBD_TESTING"] = "1"
        yield
        os.environ["IBD_TESTING"] = "1"

    def test_get_mcp_tools_returns_list(self):
        from mcp_tools import get_mcp_tools
        tools = asyncio.get_event_loop().run_until_complete(get_mcp_tools())
        assert isinstance(tools, list)

    def test_get_mcp_tools_returns_nonempty(self):
        from mcp_tools import get_mcp_tools
        tools = asyncio.get_event_loop().run_until_complete(get_mcp_tools())
        assert len(tools) > 0

    def test_tools_have_name_and_description(self):
        from mcp_tools import get_mcp_tools
        tools = asyncio.get_event_loop().run_until_complete(get_mcp_tools())
        for t in tools:
            assert t.name, f"Tool without name: {t}"
            assert t.description, f"Tool {t.name} has no description"


# ---------------------------------------------------------------------------
# Test Group 3: Catalog API tools (3 tests)
# ---------------------------------------------------------------------------

class TestCatalogTools:
    """Test individual catalog MCP tools in mock mode."""

    def _find_tool(self, name: str):
        from mcp_tools import get_mcp_tools
        tools = asyncio.get_event_loop().run_until_complete(get_mcp_tools())
        return next((t for t in tools if t.name == name), None)

    def test_list_spaces_tool_exists(self):
        """T01: list_spaces_for_catalogservice returns results list."""
        tool = self._find_tool("list_spaces_for_catalogservice")
        assert tool is not None, "list_spaces_for_catalogservice not found in mock tools"

    def test_list_spaces_tool_returns_results(self):
        """T01: list_spaces_for_catalogservice mock returns results array."""
        tool = self._find_tool("list_spaces_for_catalogservice")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({}))
        data = json.loads(resp)
        assert "results" in data
        assert len(data["results"]) >= 1

    def test_get_spaces_tool_exists(self):
        """T02: get_spaces_for_catalogservice returns a single space."""
        tool = self._find_tool("get_spaces_for_catalogservice")
        assert tool is not None

    def test_list_assets_tool_returns_results(self):
        """T03: list_assets_for_catalogservice returns assets array."""
        tool = self._find_tool("list_assets_for_catalogservice")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({}))
        data = json.loads(resp)
        assert "results" in data

    def test_get_assets_tool_exists(self):
        """T04: get_assets_for_catalogservice returns a single asset."""
        tool = self._find_tool("get_assets_for_catalogservice")
        assert tool is not None

    def test_count_spaces_returns_integer(self):
        """T05: count_spaces_for_catalogservice returns an integer."""
        tool = self._find_tool("count_spaces_for_catalogservice")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({}))
        data = json.loads(resp)
        assert isinstance(data, int)

    def test_count_assets_returns_integer(self):
        """T06: count_assets_for_catalogservice returns an integer."""
        tool = self._find_tool("count_assets_for_catalogservice")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({}))
        data = json.loads(resp)
        assert isinstance(data, int)


# ---------------------------------------------------------------------------
# Test Group 4: Connections API tools (3 tests)
# ---------------------------------------------------------------------------

class TestConnectionsTools:
    """Test connection MCP tools in mock mode."""

    def _find_tool(self, name: str):
        from mcp_tools import get_mcp_tools
        tools = asyncio.get_event_loop().run_until_complete(get_mcp_tools())
        return next((t for t in tools if t.name == name), None)

    def test_list_connections_tool_exists(self):
        """T07: ListConnectionsInSpace returns results."""
        tool = self._find_tool("ListConnectionsInSpace")
        assert tool is not None

    def test_list_connections_returns_results(self):
        """T07: ListConnectionsInSpace mock returns connection list."""
        tool = self._find_tool("ListConnectionsInSpace")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({"spaceid": "SALESDATA"}))
        data = json.loads(resp)
        assert "results" in data
        assert len(data["results"]) >= 1

    def test_create_connection_tool_exists(self):
        """T08: CreateConnectionInSpace tool exists."""
        tool = self._find_tool("CreateConnectionInSpace")
        assert tool is not None

    def test_validate_connection_returns_ok(self):
        """T09: ValidateConnectionInSpace returns OK status."""
        tool = self._find_tool("ValidateConnectionInSpace")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(
            tool.arun({"spaceid": "SALESDATA", "name": "S4HANA_CONN"})
        )
        data = json.loads(resp)
        assert data.get("status") == "OK"


# ---------------------------------------------------------------------------
# Test Group 5: Pipeline Engine tools (3 tests)
# ---------------------------------------------------------------------------

class TestPipelineEngineTools:
    """Test pipeline engine MCP tools in mock mode."""

    def _find_tool(self, name: str):
        from mcp_tools import get_mcp_tools
        tools = asyncio.get_event_loop().run_until_complete(get_mcp_tools())
        return next((t for t in tools if t.name == name), None)

    def test_list_graphs_returns_list(self):
        """T10: listGraphs returns a list of graphs."""
        tool = self._find_tool("listGraphs")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({}))
        data = json.loads(resp)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_start_graph_returns_handle(self):
        """T11: startExecutionGraph returns a handle."""
        tool = self._find_tool("startExecutionGraph")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({"body": "{}"}))
        data = json.loads(resp)
        assert "handle" in data

    def test_get_execution_graph_returns_status(self):
        """T12: getExecutionGraph returns execution details with status."""
        tool = self._find_tool("getExecutionGraph")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({"handle": "exec-001"}))
        data = json.loads(resp)
        assert "status" in data
        assert "rowsProcessed" in data


# ---------------------------------------------------------------------------
# Test Group 6: Data Profiling tool (1 test)
# ---------------------------------------------------------------------------

class TestDataProfilingTool:
    """Test data profiling MCP tool in mock mode."""

    def _find_tool(self, name: str):
        from mcp_tools import get_mcp_tools
        tools = asyncio.get_event_loop().run_until_complete(get_mcp_tools())
        return next((t for t in tools if t.name == name), None)

    def test_prf_report_returns_statistics(self):
        """T13: prf_report_profiling_post returns report with statistics."""
        tool = self._find_tool("prf_report_profiling_post")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({"body": "{}"}))
        data = json.loads(resp)
        assert data.get("status") == "completed"
        assert "statistics" in data
        stats = data["statistics"]
        assert "rowCount" in stats
        assert "completeness" in stats


# ---------------------------------------------------------------------------
# Test Group 7: Enterprise Information Management tools (3 tests)
# ---------------------------------------------------------------------------

class TestEIMTools:
    """Test EIM MCP tools in mock mode."""

    def _find_tool(self, name: str):
        from mcp_tools import get_mcp_tools
        tools = asyncio.get_event_loop().run_until_complete(get_mcp_tools())
        return next((t for t in tools if t.name == name), None)

    def test_get_tasks_returns_list(self):
        """T14: GET_tasks returns list of tasks."""
        tool = self._find_tool("GET_tasks")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({}))
        data = json.loads(resp)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_addtasks_returns_execution_id(self):
        """T15: addtasks returns execution ID."""
        tool = self._find_tool("addtasks")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({"taskname": "SAPHANADB::billing_flowgraph"}))
        data = json.loads(resp)
        assert "taskExecutionId" in data
        assert data.get("status") == "RUNNING"

    def test_get_virtual_tables_returns_list(self):
        """T16: GET_virtualTables returns list of virtual tables."""
        tool = self._find_tool("GET_virtualTables")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({}))
        data = json.loads(resp)
        assert isinstance(data, list)


# ---------------------------------------------------------------------------
# Test Group 8: Data Sharing Cockpit tools (4 tests)
# ---------------------------------------------------------------------------

class TestDSCTools:
    """Test Data Sharing Cockpit MCP tools in mock mode."""

    def _find_tool(self, name: str):
        from mcp_tools import get_mcp_tools
        tools = asyncio.get_event_loop().run_until_complete(get_mcp_tools())
        return next((t for t in tools if t.name == name), None)

    def test_get_products_returns_results(self):
        """T17: GET_v1_datasphere_marketplace_dsc_products returns list."""
        tool = self._find_tool("GET_v1_datasphere_marketplace_dsc_products")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({}))
        data = json.loads(resp)
        assert "results" in data

    def test_post_product_returns_uuid(self):
        """T18: POST_v1_datasphere_marketplace_dsc_products creates new product."""
        tool = self._find_tool("POST_v1_datasphere_marketplace_dsc_products")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({"body": "{}"}))
        data = json.loads(resp)
        assert "productUUID" in data

    def test_change_lifecycle_status_returns_status(self):
        """T19: changeLifecycleStatus updates product status."""
        tool = self._find_tool("POST_v1_datasphere_marketplace_dsc_products_productUUID_changeLifecycleStatus")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(
            tool.arun({"productuuid": "PROD-001", "body": "{}"})
        )
        data = json.loads(resp)
        assert "lifecycleStatus" in data

    def test_install_product_returns_installation_id(self):
        """T20: install product returns installationId."""
        tool = self._find_tool("POST_v1_datasphere_marketplace_consumer_products_productUUID_install")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(
            tool.arun({"productuuid": "PROD-001", "body": "{}"})
        )
        data = json.loads(resp)
        assert data.get("status") == "INSTALLED"


# ---------------------------------------------------------------------------
# Test Group 9: Data Maturity Assessment tool (1 test)
# ---------------------------------------------------------------------------

class TestDMATools:
    """Test Data Maturity Assessment MCP tool in mock mode."""

    def _find_tool(self, name: str):
        from mcp_tools import get_mcp_tools
        tools = asyncio.get_event_loop().run_until_complete(get_mcp_tools())
        return next((t for t in tools if t.name == name), None)

    def test_dma_assessment_returns_score(self):
        """T21: DHAPRocess_DHA_post returns maturity score."""
        tool = self._find_tool("DHAPRocess_DHA_post")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({"body": "{}"}))
        data = json.loads(resp)
        assert "score" in data
        assert data.get("status") == "completed"
        assert isinstance(data["score"], (int, float))


# ---------------------------------------------------------------------------
# Test Group 10: Replication tools (2 tests)
# ---------------------------------------------------------------------------

class TestReplicationTools:
    """Test replication MCP tools in mock mode."""

    def _find_tool(self, name: str):
        from mcp_tools import get_mcp_tools
        tools = asyncio.get_event_loop().run_until_complete(get_mcp_tools())
        return next((t for t in tools if t.name == name), None)

    def test_replicate_products_returns_success(self):
        """T22: replicateProducts returns success status."""
        tool = self._find_tool("replicateProducts")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({"body": "{}"}))
        data = json.loads(resp)
        assert data.get("status") == "success"

    def test_replicate_company_code_returns_success(self):
        """T23: replicateCompanyCode returns success status."""
        tool = self._find_tool("replicateCompanyCode")
        assert tool is not None
        resp = asyncio.get_event_loop().run_until_complete(tool.arun({"body": "{}"}))
        data = json.loads(resp)
        assert data.get("status") == "success"
        assert "entity" in data


# ---------------------------------------------------------------------------
# Test Group 11: ApprovalGateway (3 tests)
# ---------------------------------------------------------------------------

class TestApprovalGateway:
    """Test ApprovalGateway approval modes."""

    @pytest.fixture(autouse=True)
    def gateway(self):
        from approval_gateway import ApprovalGateway
        self.gw = ApprovalGateway()

    def test_autonomous_action_does_not_require_approval(self):
        """T24: catalog_read=autonomous — requires_approval returns False."""
        result = self.gw.requires_approval("catalog_read")
        assert result is False

    def test_always_approve_requires_approval(self):
        """T25: governance_change=always_approve — requires_approval returns True."""
        result = self.gw.requires_approval("governance_change")
        assert result is True

    def test_supervised_requires_approval(self):
        """T26: connection_create=supervised — requires_approval returns True."""
        result = self.gw.requires_approval("connection_create")
        assert result is True

    def test_approval_config_has_all_categories(self):
        """T27: APPROVAL_CONFIG contains all required action categories."""
        from approval_gateway import APPROVAL_CONFIG
        required_categories = [
            "catalog_read",
            "monitoring_read",
            "code_generation",
            "data_profiling_run",
            "connection_create",
            "replication_flow_config",
            "data_product_publish",
            "analytical_model_create",
            "governance_change",
        ]
        for cat in required_categories:
            assert cat in APPROVAL_CONFIG, f"Missing category: {cat}"

    def test_update_mode_changes_behavior(self):
        """T28: update_mode changes the approval requirement for a category."""
        from approval_gateway import ApprovalMode
        self.gw.update_mode("connection_create", ApprovalMode.AUTONOMOUS)
        assert self.gw.requires_approval("connection_create") is False
        # Reset for other tests
        self.gw.update_mode("connection_create", ApprovalMode.SUPERVISED)

    def test_format_approval_request_returns_string(self):
        """T29: format_approval_request returns a non-empty string."""
        msg = self.gw.format_approval_request(
            action_category="governance_change",
            tool_name="update_ownership",
            target_api="/v1/datasphere/marketplace/dsc/providers/123",
            description="Modify data product ownership",
            side_effects="Updates ownership records in Datasphere",
        )
        assert isinstance(msg, str)
        assert len(msg) > 0
        assert "governance" in msg.lower() or "approval" in msg.lower()


# ---------------------------------------------------------------------------
# Test Group 12: Agent classification helpers (3 tests)
# ---------------------------------------------------------------------------

class TestAgentClassification:
    """Test SampleAgent._classify_query and _classify_response helpers."""

    @pytest.fixture(autouse=True)
    def agent(self):
        # Import the unbound methods directly — no LLM initialisation needed
        # since _classify_query and _classify_response are pure Python helpers
        import importlib
        import types

        # We only need the two classification methods — load them without
        # instantiating SampleAgent (which would require LLM credentials).
        agent_mod = importlib.import_module("agent")

        # Create a bare object with only the methods we need
        obj = object.__new__(agent_mod.SampleAgent)
        # Bind the methods manually
        self.agent_instance = obj

    def test_classify_query_discovery(self):
        """T28: discovery-related keywords trigger discovery classification."""
        result = self.agent_instance._classify_query("scan the catalog for available data products")
        assert result["discovery"] is True
        assert result["monitoring"] is False

    def test_classify_query_integration(self):
        """T29: integration-related keywords trigger integration classification."""
        result = self.agent_instance._classify_query("connect to S/4HANA and replicate data")
        assert result["integration"] is True

    def test_classify_response_discovery(self):
        """T30: response containing 'data product' triggers discovery_achieved."""
        result = self.agent_instance._classify_response(
            "Found 3 data products in the catalog matching your criteria."
        )
        assert result["discovery_achieved"] is True

    def test_classify_query_quality(self):
        """T31: quality keywords trigger quality classification."""
        result = self.agent_instance._classify_query("run data profiling and validate quality")
        assert result["quality"] is True

    def test_classify_query_monitoring(self):
        """T32: monitoring keywords trigger monitoring classification."""
        result = self.agent_instance._classify_query("check maturity score and monitor usage")
        assert result["monitoring"] is True

    def test_classify_response_integration(self):
        """T33: response containing 'connection' triggers integration_achieved."""
        result = self.agent_instance._classify_response(
            "Successfully created the connection to S/4HANA and configured replication flow."
        )
        assert result["integration_achieved"] is True
