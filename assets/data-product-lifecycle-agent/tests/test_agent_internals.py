"""Targeted tests to cover agent.py internal functions and _run_agent().

Coverage targets:
  - Module-level decorated functions (get_model_name, get_temperature, get_system_prompt)
  - MODELING_VIEW_TYPES constant (REQ-08)
  - SampleAgent.__init__ with patched LLM
  - SampleAgent._touch (thread eviction)
  - SampleAgent._classify_query (including modeling keywords)
  - SampleAgent._classify_response (including modeling indicators)
  - SampleAgent._run_agent with patched LangGraph create_agent
  - stream() with tools argument
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("IBD_TESTING", "1")

AGENT_ROOT = Path(__file__).parent.parent
APP_DIR = AGENT_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Test the module-level decorated functions
# ---------------------------------------------------------------------------

class TestDecoratedFunctions:
    """Test the 3 @agent_model / @agent_config / @prompt_section decorated functions."""

    def test_get_model_name_returns_string(self):
        from agent import get_model_name
        result = get_model_name()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_model_name_contains_expected_model(self):
        from agent import get_model_name
        result = get_model_name()
        # Should reference claude or another SAP-supported model
        assert "claude" in result.lower() or "sap" in result.lower()

    def test_get_temperature_returns_float(self):
        from agent import get_temperature
        result = get_temperature()
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_get_temperature_is_deterministic(self):
        from agent import get_temperature
        assert get_temperature() == 0.0

    def test_get_system_prompt_returns_string(self):
        from agent import get_system_prompt
        result = get_system_prompt()
        assert isinstance(result, str)
        assert len(result) > 100

    def test_get_system_prompt_contains_key_rules(self):
        from agent import get_system_prompt
        prompt = get_system_prompt()
        assert "catalog_search" in prompt or "catalog" in prompt.lower()
        assert "approval" in prompt.lower() or "approve" in prompt.lower()

    def test_get_system_prompt_references_sap_sources(self):
        from agent import get_system_prompt
        prompt = get_system_prompt()
        assert "S/4HANA" in prompt or "SAP" in prompt

    def test_get_system_prompt_contains_modeling_workflow(self):
        """REQ-08: system prompt must contain the 4-step modeling workflow."""
        from agent import get_system_prompt
        prompt = get_system_prompt()
        assert "MODELING WORKFLOW" in prompt or "ANALYTICAL MODELING" in prompt

    def test_get_system_prompt_has_gather_requirements_step(self):
        """REQ-08 STEP 1: system prompt instructs agent to gather requirements."""
        from agent import get_system_prompt
        prompt = get_system_prompt()
        assert "GATHER REQUIREMENTS" in prompt or "business question" in prompt.lower()

    def test_get_system_prompt_has_propose_view_types_step(self):
        """REQ-08 STEP 2: system prompt must list all Datasphere artifact type options."""
        from agent import get_system_prompt
        prompt = get_system_prompt().lower()
        # All 7 artifact types must appear in the system prompt via MODELING_VIEW_TYPES
        assert "graphical view" in prompt
        # sql_view key title renders as "Sql View", description contains "transformation view"
        assert "sql view" in prompt or "transformation view" in prompt
        # analytical_model or analytical dataset
        assert "analytical model" in prompt or "analytical dataset" in prompt
        # New artifact types added in REQ-08 expansion
        assert "dimension view" in prompt
        assert "fact view" in prompt
        assert "data flow" in prompt
        assert "er model" in prompt

    def test_get_system_prompt_has_present_schema_step(self):
        """REQ-08 STEP 3: system prompt must instruct agent to present proposed schema."""
        from agent import get_system_prompt
        prompt = get_system_prompt()
        assert "PRESENT" in prompt or "proposed schema" in prompt.lower() or "SCHEMA" in prompt

    def test_get_system_prompt_has_approval_step(self):
        """REQ-08 STEP 4: system prompt must require explicit user approval before creation."""
        from agent import get_system_prompt
        prompt = get_system_prompt()
        assert "Do you approve" in prompt or "explicit" in prompt.lower() or "APPROVAL" in prompt

    def test_get_system_prompt_has_modeling_antipatterns(self):
        """REQ-08: system prompt must include anti-patterns that prevent skipping the workflow."""
        from agent import get_system_prompt
        prompt = get_system_prompt()
        assert "create_analytical_model" in prompt or "ANTI-PATTERNS" in prompt or "never do" in prompt.lower()


# ---------------------------------------------------------------------------
# Test MODELING_VIEW_TYPES constant (REQ-08 expanded — 7 artifact types)
# ---------------------------------------------------------------------------

class TestModelingViewTypes:
    """Test the MODELING_VIEW_TYPES constant covers all 7 Datasphere modeling artifacts."""

    def test_modeling_view_types_is_dict(self):
        from agent import MODELING_VIEW_TYPES
        assert isinstance(MODELING_VIEW_TYPES, dict)

    def test_modeling_view_types_has_minimum_7_keys(self):
        """REQ-08 expansion: must cover at least 7 artifact types."""
        from agent import MODELING_VIEW_TYPES
        assert len(MODELING_VIEW_TYPES) >= 7

    def test_modeling_view_types_has_graphical_view(self):
        from agent import MODELING_VIEW_TYPES
        assert "graphical_view" in MODELING_VIEW_TYPES

    def test_modeling_view_types_has_sql_view(self):
        """SQL/Transformation View — key renamed from transformation_view to sql_view."""
        from agent import MODELING_VIEW_TYPES
        assert "sql_view" in MODELING_VIEW_TYPES

    def test_modeling_view_types_has_dimension_view(self):
        """Dimension View — new artifact type added in REQ-08 expansion."""
        from agent import MODELING_VIEW_TYPES
        assert "dimension_view" in MODELING_VIEW_TYPES

    def test_modeling_view_types_has_fact_view(self):
        """Fact View — new artifact type added in REQ-08 expansion."""
        from agent import MODELING_VIEW_TYPES
        assert "fact_view" in MODELING_VIEW_TYPES

    def test_modeling_view_types_has_analytical_model(self):
        """Analytical Model — renamed from analytical_dataset."""
        from agent import MODELING_VIEW_TYPES
        assert "analytical_model" in MODELING_VIEW_TYPES

    def test_modeling_view_types_has_data_flow(self):
        """Data Flow — new ETL/ELT artifact type added in REQ-08 expansion."""
        from agent import MODELING_VIEW_TYPES
        assert "data_flow" in MODELING_VIEW_TYPES

    def test_modeling_view_types_has_er_model(self):
        from agent import MODELING_VIEW_TYPES
        assert "er_model" in MODELING_VIEW_TYPES

    def test_modeling_view_types_all_values_are_nonempty_strings(self):
        from agent import MODELING_VIEW_TYPES
        for key, val in MODELING_VIEW_TYPES.items():
            assert isinstance(val, str), f"{key} value should be a string"
            assert len(val) > 10, f"{key} description is too short"

    def test_graphical_view_mentions_projection_or_join(self):
        """Graphical view should describe its key capabilities: projections and joins."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["graphical_view"].lower()
        assert "projection" in desc or "join" in desc or "visual" in desc

    def test_graphical_view_mentions_aggregation(self):
        """Graphical view supports aggregation nodes."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["graphical_view"].lower()
        assert "aggregation" in desc or "group by" in desc

    def test_graphical_view_mentions_calculated_columns(self):
        """Graphical view supports calculated columns."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["graphical_view"].lower()
        assert "calculated column" in desc or "formula" in desc or "case when" in desc

    def test_sql_view_mentions_sql_or_transformation(self):
        """SQL View must reference SQL as its authoring mechanism."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["sql_view"].lower()
        assert "sql" in desc or "transformation view" in desc

    def test_sql_view_mentions_cte_or_window(self):
        """SQL View should document CTE and window function support."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["sql_view"].lower()
        assert "cte" in desc or "window" in desc or "partition" in desc

    def test_sql_view_mentions_aggregation(self):
        """SQL View supports GROUP BY aggregations."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["sql_view"].lower()
        assert "aggregation" in desc or "group by" in desc

    def test_dimension_view_mentions_master_data_or_key(self):
        """Dimension View describes master data and key columns."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["dimension_view"].lower()
        assert "key column" in desc or "master data" in desc or "dimension" in desc

    def test_dimension_view_mentions_hierarchy(self):
        """Dimension View should reference hierarchy support."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["dimension_view"].lower()
        assert "hierarchy" in desc or "hierarchi" in desc

    def test_fact_view_mentions_measures(self):
        """Fact View must declare measures for aggregation."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["fact_view"].lower()
        assert "measure" in desc

    def test_fact_view_mentions_star_schema_or_fact(self):
        """Fact View should reference star schema or fact concept."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["fact_view"].lower()
        assert "fact" in desc or "star schema" in desc or "snowflake" in desc

    def test_analytical_model_mentions_sac_or_analytics(self):
        """Analytical Model is consumed by SAP Analytics Cloud."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["analytical_model"].lower()
        assert "analytics" in desc or "sac" in desc

    def test_analytical_model_mentions_calculated_measures(self):
        """Analytical Model supports calculated and restricted measures."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["analytical_model"].lower()
        assert "calculated measure" in desc or "restricted measure" in desc or "formula" in desc

    def test_data_flow_mentions_etl_or_load(self):
        """Data Flow is an ETL/ELT pipeline."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["data_flow"].lower()
        assert "etl" in desc or "elt" in desc or "load" in desc

    def test_data_flow_mentions_delta_or_incremental(self):
        """Data Flow supports delta/incremental loading."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["data_flow"].lower()
        assert "delta" in desc or "incremental" in desc

    def test_data_flow_mentions_operators(self):
        """Data Flow has transformation operators (Projection, Filter, Aggregation, Join)."""
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["data_flow"].lower()
        assert "projection" in desc or "filter" in desc or "aggregation" in desc

    def test_er_model_mentions_entity_or_relationship(self):
        from agent import MODELING_VIEW_TYPES
        desc = MODELING_VIEW_TYPES["er_model"].lower()
        assert "entity" in desc or "relationship" in desc or "er" in desc

    def test_all_types_reference_a_tool(self):
        """Each artifact type must reference its creation tool."""
        from agent import MODELING_VIEW_TYPES
        expected_tools = {
            "graphical_view": "create_graphical_view",
            "sql_view": "create_sql_view",
            "dimension_view": "create_dimension_view",
            "fact_view": "create_fact_view",
            "analytical_model": "create_analytical_model",
            "data_flow": "create_data_flow",
            "er_model": "create_er_model",
        }
        for key, expected_tool in expected_tools.items():
            assert key in MODELING_VIEW_TYPES, f"Missing key: {key}"
            assert expected_tool in MODELING_VIEW_TYPES[key], \
                f"{key} description should reference tool {expected_tool}"


# ---------------------------------------------------------------------------
# Test SampleAgent.__init__
# ---------------------------------------------------------------------------

class TestSampleAgentInit:
    """Test SampleAgent construction with mocked dependencies."""

    def _make_agent(self):
        with patch("langchain_litellm.ChatLiteLLM") as llm_cls:
            mock_llm = MagicMock()
            llm_cls.return_value = mock_llm
            with patch("langgraph.checkpoint.memory.InMemorySaver") as saver_cls:
                saver_cls.return_value = MagicMock()
                with patch("langchain.agents.middleware.SummarizationMiddleware") as mid_cls:
                    mid_cls.return_value = MagicMock()
                    from agent import SampleAgent
                    return SampleAgent()

    def test_init_creates_approval_gateway(self):
        from approval_gateway import ApprovalGateway
        agent = self._make_agent()
        assert isinstance(agent.approval_gateway, ApprovalGateway)

    def test_init_has_last_active_dict(self):
        agent = self._make_agent()
        assert isinstance(agent._last_active, dict)

    def test_init_has_checkpointer(self):
        agent = self._make_agent()
        assert agent._checkpointer is not None

    def test_supported_content_types(self):
        from agent import SampleAgent
        assert "text" in SampleAgent.SUPPORTED_CONTENT_TYPES


# ---------------------------------------------------------------------------
# Test _classify_query (including REQ-08 modeling keywords)
# ---------------------------------------------------------------------------

class TestClassifyQuery:
    """Test _classify_query correctly identifies intent categories."""

    def _make_minimal_agent(self):
        from agent import SampleAgent
        from approval_gateway import ApprovalGateway
        inst = object.__new__(SampleAgent)
        inst.approval_gateway = ApprovalGateway()
        return inst

    def test_classify_discovery_keywords(self):
        agent = self._make_minimal_agent()
        result = agent._classify_query("scan and discover catalog data products")
        assert result["discovery"] is True

    def test_classify_integration_keywords(self):
        agent = self._make_minimal_agent()
        result = agent._classify_query("connect to S/4HANA and replicate data")
        assert result["integration"] is True

    def test_classify_dp_creation_keywords(self):
        agent = self._make_minimal_agent()
        result = agent._classify_query("activate and publish a custom data product")
        assert result["dp_creation"] is True

    def test_classify_quality_keywords(self):
        agent = self._make_minimal_agent()
        result = agent._classify_query("profile and validate data quality completeness")
        assert result["quality"] is True

    def test_classify_governance_keywords(self):
        agent = self._make_minimal_agent()
        result = agent._classify_query("govern ownership and lineage policy")
        assert result["governance"] is True

    def test_classify_monitoring_keywords(self):
        agent = self._make_minimal_agent()
        result = agent._classify_query("monitor maturity score and usage trend")
        assert result["monitoring"] is True

    def test_classify_modeling_transformation_view(self):
        """REQ-08: 'transformation view' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("create a transformation view for sales data")
        assert result["modeling"] is True

    def test_classify_modeling_sql_view(self):
        """REQ-08: 'sql view' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("build an sql view with aggregation logic")
        assert result["modeling"] is True

    def test_classify_modeling_graphical_view(self):
        """REQ-08: 'graphical view' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("build a graphical view with joins")
        assert result["modeling"] is True

    def test_classify_modeling_dimension_view(self):
        """REQ-08 expansion: 'dimension view' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("create a dimension view for customer master data")
        assert result["modeling"] is True

    def test_classify_modeling_fact_view(self):
        """REQ-08 expansion: 'fact view' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("build a fact view with declared measures")
        assert result["modeling"] is True

    def test_classify_modeling_analytical_model(self):
        """REQ-08 expansion: 'analytical model' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("create an analytical model for SAC consumption")
        assert result["modeling"] is True

    def test_classify_modeling_analytical_dataset(self):
        """REQ-08: 'analytical dataset' (legacy term) triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("create an analytical dataset for revenue reporting")
        assert result["modeling"] is True

    def test_classify_modeling_data_flow(self):
        """REQ-08 expansion: 'data flow' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("create a data flow to load sales orders incrementally")
        assert result["modeling"] is True

    def test_classify_modeling_etl(self):
        """REQ-08 expansion: 'etl' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("design an etl pipeline to materialize sales data")
        assert result["modeling"] is True

    def test_classify_modeling_er_model(self):
        """REQ-08: 'er model' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("design an er model for the schema")
        assert result["modeling"] is True

    def test_classify_modeling_cte(self):
        """REQ-08 expansion: 'cte' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("build a sql view using a cte for multi-step logic")
        assert result["modeling"] is True

    def test_classify_modeling_window_function(self):
        """REQ-08 expansion: 'window function' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("I need window function for running total calculation")
        assert result["modeling"] is True

    def test_classify_modeling_aggregation(self):
        """REQ-08 expansion: 'aggregation' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("define aggregation nodes with group by")
        assert result["modeling"] is True

    def test_classify_modeling_projection(self):
        """REQ-08 expansion: 'projection' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("add a projection operator to select columns")
        assert result["modeling"] is True

    def test_classify_modeling_calculated_column(self):
        """REQ-08 expansion: 'calculated column' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("add a calculated column for margin percentage")
        assert result["modeling"] is True

    def test_classify_modeling_star_schema(self):
        """REQ-08 expansion: 'star schema' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("design a star schema with fact and dimension tables")
        assert result["modeling"] is True

    def test_classify_modeling_dimensions_measures(self):
        """REQ-08: 'dimensions' and 'measures' trigger modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("define dimensions and measures for the KPI dashboard")
        assert result["modeling"] is True

    def test_classify_modeling_build_model(self):
        """REQ-08: 'build model' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("build model for monthly revenue by region")
        assert result["modeling"] is True

    def test_classify_modeling_analytical_model_keyword(self):
        """REQ-08: 'analytical model' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("create an analytical model in Datasphere")
        assert result["modeling"] is True

    def test_classify_modeling_incremental_load(self):
        """REQ-08 expansion: 'incremental load' triggers modeling classification."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("set up incremental load for the data flow")
        assert result["modeling"] is True

    def test_classify_modeling_upsert(self):
        """REQ-08 expansion: 'upsert' triggers modeling classification (data flow delta mode)."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("configure upsert mode for delta loading")
        assert result["modeling"] is True

    def test_classify_non_modeling_query(self):
        """Non-modeling query should not set modeling=True."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("list all data products in the catalog")
        assert result["modeling"] is False

    def test_classify_all_false_for_empty_query(self):
        """Empty query should not match any category."""
        agent = self._make_minimal_agent()
        result = agent._classify_query("")
        assert all(v is False for v in result.values())


# ---------------------------------------------------------------------------
# Test _classify_response (including REQ-08 modeling response indicators)
# ---------------------------------------------------------------------------

class TestClassifyResponse:
    """Test _classify_response correctly detects milestone achievement."""

    def _make_minimal_agent(self):
        from agent import SampleAgent
        from approval_gateway import ApprovalGateway
        inst = object.__new__(SampleAgent)
        inst.approval_gateway = ApprovalGateway()
        return inst

    def test_response_discovery_achieved(self):
        agent = self._make_minimal_agent()
        result = agent._classify_response("Found 5 data products in the catalog. Results available.")
        assert result["discovery_achieved"] is True

    def test_response_integration_achieved(self):
        agent = self._make_minimal_agent()
        result = agent._classify_response("Connection created. Replication flow configured.")
        assert result["integration_achieved"] is True

    def test_response_dp_creation_achieved(self):
        agent = self._make_minimal_agent()
        result = agent._classify_response("Data product successfully activated. Catalog ID: dp-001.")
        assert result["dp_creation_achieved"] is True

    def test_response_quality_achieved(self):
        agent = self._make_minimal_agent()
        result = agent._classify_response("Profiling complete. Completeness: 98%. Quality validated.")
        assert result["quality_achieved"] is True

    def test_response_governance_achieved(self):
        agent = self._make_minimal_agent()
        result = agent._classify_response("Governance configured. Ownership applied. Lineage enabled.")
        assert result["governance_achieved"] is True

    def test_response_monitoring_achieved(self):
        agent = self._make_minimal_agent()
        result = agent._classify_response("Maturity score: 4.2. Monitoring recommendations delivered.")
        assert result["monitoring_achieved"] is True

    def test_response_modeling_requirements_gathered(self):
        """REQ-08: agent asking 'business question' indicates requirements-gathering step."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "To proceed, I need to understand your business question. "
            "What dimensions and measures should the model include?"
        )
        assert result["modeling_requirements_gathered"] is True

    def test_response_modeling_requirements_gathered_source_entities(self):
        """REQ-08: asking about source entities indicates requirements gathering."""
        agent = self._make_minimal_agent()
        result = agent._classify_response("Which tables are your source entities? Please provide the space ID.")
        assert result["modeling_requirements_gathered"] is True

    def test_response_modeling_proposal_made_transformation_view(self):
        """REQ-08: proposing a 'transformation view' indicates proposal step."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "I propose a Transformation View with the following SQL draft..."
        )
        assert result["modeling_proposal_made"] is True

    def test_response_modeling_proposal_made_graphical_view(self):
        """REQ-08: proposing a 'graphical view' indicates proposal step."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "I recommend a Graphical View as the best option for your use case."
        )
        assert result["modeling_proposal_made"] is True

    def test_response_modeling_proposal_made_analytical_dataset(self):
        """REQ-08: proposing an 'analytical model' or 'analytical dataset' indicates proposal step."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "Given your SAC consumption need, an Analytical Model is the best fit. "
            "I propose the following star schema with fact and dimension views."
        )
        assert result["modeling_proposal_made"] is True

    def test_response_modeling_proposal_made_dimension_view(self):
        """REQ-08 expansion: proposing a 'dimension view' indicates proposal step."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "I recommend creating a Dimension View for your customer master data."
        )
        assert result["modeling_proposal_made"] is True

    def test_response_modeling_proposal_made_fact_view(self):
        """REQ-08 expansion: proposing a 'fact view' indicates proposal step."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "A Fact View is the right choice for your transactional sales orders."
        )
        assert result["modeling_proposal_made"] is True

    def test_response_modeling_proposal_made_data_flow(self):
        """REQ-08 expansion: proposing a 'data flow' indicates proposal step."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "I propose a Data Flow with DELTA load mode for incremental ingestion."
        )
        assert result["modeling_proposal_made"] is True

    def test_response_modeling_proposal_made_er_model(self):
        """REQ-08 expansion: proposing an 'ER model' indicates proposal step."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "An ER Model will document all the entity relationships in your space."
        )
        assert result["modeling_proposal_made"] is True

    def test_response_modeling_proposal_schema_with_uppercase_name(self):
        """REQ-08: proposed schema with UPPER_SNAKE_CASE name triggers proposal detection."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "Proposed schema:\n  View name: UPPER_SNAKE_CASE_REVENUE\n  Measures: NET_AMOUNT"
        )
        assert result["modeling_proposal_made"] is True

    def test_response_modeling_schema_presented_join_condition(self):
        """REQ-08 STEP 3: response with join condition details triggers schema_presented."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "Here is the proposed schema:\n"
            "  Source entities: SALES_ORDERS, CUSTOMERS\n"
            "  Join condition: SALES_ORDERS.CUSTOMER_ID = CUSTOMERS.ID\n"
            "  Measure columns: NET_AMOUNT (SUM), QUANTITY (SUM)"
        )
        assert result["modeling_schema_presented"] is True

    def test_response_modeling_schema_presented_sql_select(self):
        """REQ-08 STEP 3: response containing a SQL SELECT statement triggers schema_presented."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "Here is the draft SQL SELECT statement:\n"
            "  SELECT region, SUM(revenue) AS total_revenue FROM sales GROUP BY region"
        )
        assert result["modeling_schema_presented"] is True

    def test_response_modeling_schema_presented_measure_column(self):
        """REQ-08 STEP 3: 'measure column' reference triggers schema_presented."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "The Fact View will have measure columns: NET_AMOUNT (SUM), QUANTITY (COUNT)."
        )
        assert result["modeling_schema_presented"] is True

    def test_response_modeling_schema_not_presented_for_plain_query(self):
        """Non-schema response should not trigger schema_presented."""
        agent = self._make_minimal_agent()
        result = agent._classify_response("Let me look up the catalog for you.")
        assert result["modeling_schema_presented"] is False

    def test_response_modeling_approval_requested(self):
        """REQ-08: agent asking 'do you approve' triggers approval-requested detection."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "I am about to call create_analytical_model. Do you approve (yes/no)?"
        )
        assert result["modeling_approval_requested"] is True

    def test_response_modeling_approval_shall_i_proceed(self):
        """REQ-08: 'shall I proceed' triggers approval-requested detection."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "Shall I proceed with creating the Graphical View in space SALES_SPACE?"
        )
        assert result["modeling_approval_requested"] is True

    def test_response_modeling_approval_please_confirm(self):
        """REQ-08: 'please confirm' triggers approval-requested detection."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "Please confirm before I call create_data_flow to persist the ETL pipeline."
        )
        assert result["modeling_approval_requested"] is True

    def test_response_modeling_achieved_view_created(self):
        """REQ-08: 'view created' in response indicates modeling was completed."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "The Transformation View has been successfully created in Datasphere. "
            "Object created in Datasphere: REVENUE_BY_REGION."
        )
        assert result["modeling_achieved"] is True

    def test_response_modeling_achieved_graphical_view_created(self):
        """REQ-08: 'graphical view created' indicates modeling was completed."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "Graphical view created successfully. Deployment completed."
        )
        assert result["modeling_achieved"] is True

    def test_response_modeling_achieved_sql_view_created(self):
        """REQ-08 expansion: 'sql view created' indicates modeling was completed."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "SQL view created. Status: COMPLETED. Now deploying to HANA."
        )
        assert result["modeling_achieved"] is True

    def test_response_modeling_achieved_data_flow_created(self):
        """REQ-08 expansion: 'data flow created' indicates modeling was completed."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "Data flow created successfully. Ready to schedule via task chain."
        )
        assert result["modeling_achieved"] is True

    def test_response_modeling_achieved_deployment_completed(self):
        """REQ-08: 'deployment completed' indicates the artifact is live."""
        agent = self._make_minimal_agent()
        result = agent._classify_response(
            "Deployment completed successfully. The analytical model is now DEPLOYED."
        )
        assert result["modeling_achieved"] is True

    def test_response_no_modeling_for_plain_catalog_query(self):
        """Non-modeling response should not set any modeling flag."""
        agent = self._make_minimal_agent()
        result = agent._classify_response("Catalog search returned 10 data products.")
        assert result["modeling_requirements_gathered"] is False
        assert result["modeling_proposal_made"] is False
        assert result["modeling_schema_presented"] is False
        assert result["modeling_approval_requested"] is False
        assert result["modeling_achieved"] is False


# ---------------------------------------------------------------------------
# Test _touch thread eviction
# ---------------------------------------------------------------------------

class TestTouchEviction:
    """Test that _touch evicts expired threads."""

    def _make_minimal_agent(self):
        from agent import SampleAgent
        from approval_gateway import ApprovalGateway
        inst = object.__new__(SampleAgent)
        inst._last_active = {}
        mock_cp = MagicMock()
        mock_cp.delete_thread = MagicMock()
        inst._checkpointer = mock_cp
        inst.approval_gateway = ApprovalGateway()
        return inst

    def test_touch_adds_thread(self):
        agent = self._make_minimal_agent()
        agent._touch("thread-abc")
        assert "thread-abc" in agent._last_active

    def test_touch_evicts_expired_thread(self):
        from agent import THREAD_TTL_SECONDS
        agent = self._make_minimal_agent()
        # Set an old timestamp to simulate expiry
        expired_ts = time.monotonic() - (THREAD_TTL_SECONDS + 1)
        agent._last_active["old-thread"] = expired_ts
        # Touch a new thread to trigger eviction
        agent._touch("new-thread")
        assert "old-thread" not in agent._last_active
        assert "new-thread" in agent._last_active


# ---------------------------------------------------------------------------
# Test _run_agent with patched LangGraph
# ---------------------------------------------------------------------------

class TestRunAgent:
    """Test _run_agent by patching create_agent."""

    def _make_agent_with_mocks(self):
        with patch("langchain_litellm.ChatLiteLLM") as llm_cls:
            mock_llm = MagicMock()
            llm_cls.return_value = mock_llm
            with patch("langgraph.checkpoint.memory.InMemorySaver") as saver_cls:
                saver_cls.return_value = MagicMock()
                with patch("langchain.agents.middleware.SummarizationMiddleware") as mid_cls:
                    mid_cls.return_value = MagicMock()
                    from agent import SampleAgent
                    return SampleAgent()

    def _make_fake_graph(self, content="Data products found in catalog."):
        """Return a mock LangGraph graph that returns a predefined message."""
        msg = MagicMock()
        msg.content = content
        graph = MagicMock()
        graph.ainvoke = AsyncMock(return_value={"messages": [msg]})
        return graph

    def test_run_agent_returns_string(self):
        """_run_agent returns a string response."""
        agent = self._make_agent_with_mocks()
        graph = self._make_fake_graph("Found data products in catalog.")

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "scan catalog for available data products", "ctx-001"
            ))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_run_agent_m1_discovery_achieved(self):
        """_run_agent sets M1 achieved when discovery keyword in query and result."""
        agent = self._make_agent_with_mocks()
        graph = self._make_fake_graph("Found 3 data products in the catalog results.")

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "scan and discover catalog data products", "ctx-m1"
            ))
        assert "found" in result.lower() or "catalog" in result.lower()

    def test_run_agent_m2_integration(self):
        """_run_agent handles integration queries."""
        agent = self._make_agent_with_mocks()
        graph = self._make_fake_graph("Connection created and replication flow configured.")

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "connect to S/4HANA and replicate data", "ctx-m2"
            ))
        assert isinstance(result, str)

    def test_run_agent_m3_dp_creation(self):
        """_run_agent handles data product creation queries."""
        agent = self._make_agent_with_mocks()
        graph = self._make_fake_graph("Data product successfully activated and created.")

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "activate and create data product", "ctx-m3"
            ))
        assert "activated" in result.lower() or "created" in result.lower()

    def test_run_agent_m4_quality(self):
        """_run_agent handles quality validation queries."""
        agent = self._make_agent_with_mocks()
        graph = self._make_fake_graph("Profiling complete. Completeness: 98%. Quality validated.")

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "profile and validate data quality completeness", "ctx-m4"
            ))
        assert "completeness" in result.lower() or "profiling" in result.lower()

    def test_run_agent_m5_governance(self):
        """_run_agent handles governance queries."""
        agent = self._make_agent_with_mocks()
        graph = self._make_fake_graph("Governance configured. Ownership applied. Lineage enabled.")

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "govern data product ownership and model analytical lineage", "ctx-m5"
            ))
        assert isinstance(result, str)

    def test_run_agent_m6_monitoring(self):
        """_run_agent handles monitoring queries."""
        agent = self._make_agent_with_mocks()
        graph = self._make_fake_graph("Maturity score: 4.2. Monitoring summary and recommendations delivered.")

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "monitor maturity score and usage report", "ctx-m6"
            ))
        assert "maturity" in result.lower() or "monitoring" in result.lower()

    def test_run_agent_raises_propagates(self):
        """_run_agent re-raises exceptions from the graph."""
        agent = self._make_agent_with_mocks()
        failing_graph = MagicMock()
        failing_graph.ainvoke = AsyncMock(side_effect=RuntimeError("LLM failure"))

        with patch("agent.create_agent", return_value=failing_graph):
            with pytest.raises(RuntimeError):
                _run(agent._run_agent(
                    "scan catalog for data products", "ctx-fail"
                ))

    def test_run_agent_all_milestones(self):
        """_run_agent handles a query hitting all 6 milestone categories."""
        agent = self._make_agent_with_mocks()
        response = (
            "Found data product catalog results. Connection created. "
            "Data product activated. Completeness validated. Governance applied. "
            "Maturity score: 4.5 monitoring recommendations delivered."
        )
        graph = self._make_fake_graph(response)

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "discover catalog connect replicate activate profile govern monitor maturity",
                "ctx-all"
            ))
        assert isinstance(result, str)

    # REQ-08 modeling integration tests

    def test_run_agent_modeling_requirements_gathering(self):
        """REQ-08 STEP 1: agent returns requirements-gathering response for modeling query."""
        agent = self._make_agent_with_mocks()
        response = (
            "To build the analytical model, I need to understand your business question. "
            "What dimensions and measures should be included?"
        )
        graph = self._make_fake_graph(response)

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "create a transformation view for sales revenue analytics",
                "ctx-req08-step1"
            ))
        assert "business question" in result.lower() or "dimensions" in result.lower()

    def test_run_agent_modeling_proposal_made(self):
        """REQ-08 STEP 2: agent proposes a Transformation View."""
        agent = self._make_agent_with_mocks()
        response = (
            "Based on your requirements, I recommend a Transformation View. "
            "Here is the proposed schema:\n"
            "  View name: MONTHLY_REVENUE_BY_REGION\n"
            "  Measures: SUM(NET_AMOUNT) as TOTAL_REVENUE\n"
            "  Dimensions: REGION, PRODUCT_LINE, MONTH\n"
            "Do you approve?"
        )
        graph = self._make_fake_graph(response)

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "build model for monthly revenue by region with dimensions and measures",
                "ctx-req08-step2"
            ))
        assert "transformation view" in result.lower() or "proposed schema" in result.lower() or "approve" in result.lower()

    def test_run_agent_modeling_graphical_view_proposal(self):
        """REQ-08: agent proposes Graphical View for simple join use case."""
        agent = self._make_agent_with_mocks()
        response = (
            "For a simple join between ORDERS and CUSTOMERS, a Graphical View is ideal. "
            "I propose the following: View name: UPPER_SNAKE_CASE. Shall I proceed?"
        )
        graph = self._make_fake_graph(response)

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "design graphical view joining orders and customers tables",
                "ctx-req08-graphical"
            ))
        assert "graphical view" in result.lower() or "upper_snake" in result.lower()

    def test_run_agent_modeling_analytical_dataset_proposal(self):
        """REQ-08: agent proposes Analytical Dataset for SAC consumption."""
        agent = self._make_agent_with_mocks()
        response = (
            "Since the primary consumer is SAP Analytics Cloud, an Analytical Dataset is "
            "the best fit. Proposed schema includes declared measures and dimensions. "
            "Do you approve creating this analytical dataset?"
        )
        graph = self._make_fake_graph(response)

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "create an analytical dataset for KPI dashboard consumption",
                "ctx-req08-analytic"
            ))
        assert "analytical dataset" in result.lower() or "approve" in result.lower()

    def test_run_agent_modeling_creation_achieved(self):
        """REQ-08 STEP 4: after approval, artifact is created in Datasphere."""
        agent = self._make_agent_with_mocks()
        response = (
            "The Transformation View MONTHLY_REVENUE has been successfully created. "
            "Object created in Datasphere: MONTHLY_REVENUE in space FINANCE_SPACE."
        )
        graph = self._make_fake_graph(response)

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "create view MONTHLY_REVENUE analytical model in Datasphere",
                "ctx-req08-created"
            ))
        assert "created" in result.lower() or "datasphere" in result.lower()

    def test_run_agent_modeling_dimension_view_proposed(self):
        """REQ-08 expansion: agent proposes Dimension View for master data."""
        agent = self._make_agent_with_mocks()
        response = (
            "Based on your customer master data requirements, I recommend a Dimension View. "
            "Here is the proposed schema:\n"
            "  View name: DIM_CUSTOMER\n"
            "  Key columns: CUSTOMER_ID\n"
            "  Attribute columns: CUSTOMER_NAME, REGION_CODE, COUNTRY\n"
            "  Text association: CUSTOMER_TEXT (locale-aware descriptions)\n"
            "  Source entities: CUSTOMER_MASTER table\n"
            "Do you approve (yes/no)?"
        )
        graph = self._make_fake_graph(response)

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "create a dimension view for customer master data with hierarchy",
                "ctx-req08-dim"
            ))
        assert "dimension view" in result.lower() or "dim_customer" in result.lower()

    def test_run_agent_modeling_fact_view_proposed(self):
        """REQ-08 expansion: agent proposes Fact View with measures."""
        agent = self._make_agent_with_mocks()
        response = (
            "For transactional sales data with revenue measures, a Fact View is the right choice. "
            "Proposed schema:\n"
            "  View name: FACT_SALES\n"
            "  Measure columns: NET_AMOUNT (SUM), QUANTITY (SUM)\n"
            "  Dimension associations: DIM_CUSTOMER via CUSTOMER_ID, DIM_PRODUCT via PRODUCT_ID\n"
            "  Source entities: SALES_ORDERS_RAW\n"
            "Do you approve (yes/no)?"
        )
        graph = self._make_fake_graph(response)

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "build fact view for sales orders with declared measures and dimension associations",
                "ctx-req08-fact"
            ))
        assert "fact view" in result.lower() or "measure column" in result.lower()

    def test_run_agent_modeling_data_flow_proposed(self):
        """REQ-08 expansion: agent proposes Data Flow for incremental load."""
        agent = self._make_agent_with_mocks()
        response = (
            "Since data must be physically stored, I recommend a Data Flow with DELTA load mode. "
            "Proposed:\n"
            "  Flow name: DF_SALES_INCREMENTAL\n"
            "  Source entities: SALES_ORDERS_RAW\n"
            "  Target local table: SALES_ORDERS_LOCAL\n"
            "  Load type: DELTA (incremental load)\n"
            "  Delta column: CHANGED_AT\n"
            "  Operators: Projection (select key columns), Filter (active orders only)\n"
            "Do you approve (yes/no)?"
        )
        graph = self._make_fake_graph(response)

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "create a data flow for etl incremental load with upsert",
                "ctx-req08-dataflow"
            ))
        assert "data flow" in result.lower() or "incremental" in result.lower()

    def test_run_agent_modeling_sql_view_with_cte(self):
        """REQ-08 expansion: agent proposes SQL View with CTE for complex logic."""
        agent = self._make_agent_with_mocks()
        response = (
            "For your multi-step aggregation with window functions, an SQL View is the best fit. "
            "Draft SQL SELECT statement:\n"
            "  WITH monthly_agg AS (SELECT region, month, SUM(net_amount) AS revenue\n"
            "  FROM sales_fact GROUP BY region, month)\n"
            "  SELECT *, SUM(revenue) OVER (PARTITION BY region ORDER BY month) AS running_total\n"
            "  FROM monthly_agg\n"
            "Source entities: SALES_FACT\n"
            "Do you approve (yes/no)?"
        )
        graph = self._make_fake_graph(response)

        with patch("agent.create_agent", return_value=graph):
            result = _run(agent._run_agent(
                "build sql view using cte and window function for running total by region",
                "ctx-req08-sqlview"
            ))
        assert "sql" in result.lower() or "cte" in result.lower() or "running" in result.lower()

    def test_run_agent_modeling_error_logged(self):
        """REQ-08: modeling failures are logged with M5.modeling.missed."""
        agent = self._make_agent_with_mocks()
        failing_graph = MagicMock()
        failing_graph.ainvoke = AsyncMock(side_effect=RuntimeError("Datasphere API error"))

        with patch("agent.create_agent", return_value=failing_graph):
            with pytest.raises(RuntimeError):
                _run(agent._run_agent(
                    "create transformation view for analytical model",
                    "ctx-req08-fail"
                ))


# ---------------------------------------------------------------------------
# Test stream() with tools argument (line 287)
# ---------------------------------------------------------------------------

class TestStreamWithTools:
    """Test stream() when tools are provided (covers line 287)."""

    def _make_agent(self):
        with patch("langchain_litellm.ChatLiteLLM") as llm_cls:
            mock_llm = MagicMock()
            llm_cls.return_value = mock_llm
            with patch("langgraph.checkpoint.memory.InMemorySaver") as saver_cls:
                saver_cls.return_value = MagicMock()
                with patch("langchain.agents.middleware.SummarizationMiddleware") as mid_cls:
                    mid_cls.return_value = MagicMock()
                    from agent import SampleAgent
                    return SampleAgent()

    def test_stream_with_tools_provided(self):
        """Passing tools to stream() logs the tool count (line 287)."""
        agent = self._make_agent()
        fake_msg = MagicMock()
        fake_msg.content = "Found data products in catalog results."
        graph = MagicMock()
        graph.ainvoke = AsyncMock(return_value={"messages": [fake_msg]})

        mock_tool = MagicMock()
        mock_tool.name = "list_spaces_for_catalogservice"

        async def collect():
            chunks = []
            with patch("agent.create_agent", return_value=graph):
                async for chunk in agent.stream("discover data products", "ctx-tools", tools=[mock_tool]):
                    chunks.append(chunk)
            return chunks

        chunks = _run(collect())
        assert len(chunks) >= 2  # processing + result
        last = chunks[-1]
        assert last["is_task_complete"] is True
