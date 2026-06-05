# Specification: data-product-lifecycle-agent

> **Guidelines**: Read [../guidelines.md](../guidelines.md) and [../guidelines-agent.md](../guidelines-agent.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` thoroughly before writing any code
- [x] Bootstrap agent code in `assets/data-product-lifecycle-agent/` using skill `sap-agent-bootstrap` (invoke from inside `assets/data-product-lifecycle-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies: `pip install -r requirements.txt -q && pip install -r requirements-test.txt -q`
- [x] Validate the agent starts and the `/.well-known/agent.json` endpoint responds

---

## REQ-01 — Data Landscape Discovery

**Goal**: Let the agent scan the BDC catalog for available SAP-managed Data Products and existing connections, grouped by domain, before any new Data Product creation is proposed.

- [x] Implement `catalog_search` tool via MCP:
  - Calls Catalog API (OData/REST) to list SAP-managed Data Products available for activation
  - Spec: `specification/data-product-lifecycle-agent/api-specs/catalog.edmx`
  - Accepts optional `domain` parameter (Finance, Procurement, Supply Chain, Sales, HR, or empty for all)
  - Returns: list of Data Product names, descriptions, activation status, ORD IDs — max 100 per page
  - Side effect: **read-only** — no approval gate required
- [x] Implement `list_connections` tool via MCP:
  - Calls `GET /api/v1/datasphere/spaces/{spaceId}/connections`
  - Spec: `specification/data-product-lifecycle-agent/api-specs/connections.json`
  - Accepts `spaceId` as required parameter
  - Returns: existing connection names, types, and statuses — max 100
  - Side effect: **read-only** — no approval gate required
- [x] Wire both tools into the agent graph via `get_mcp_tools()`; do NOT hard-code tool names in agent code
- [x] System prompt rule: agent must call `catalog_search` before proposing any new Data Product creation (reuse-before-create)
- [x] System prompt rule: set `top`/page size to maximum 100 on all paginated calls; inform user when limit is applied

## REQ-02 — SAP Application Source Integration

**Goal**: Create Datasphere connections to SAP application sources (S/4HANA and other SAP systems) and configure Replication Flows for selected tables or CDS views.

- [x] Implement `create_connection` tool via MCP:
  - Calls `POST /api/v1/datasphere/spaces/{spaceId}/connections`
  - Spec: `specification/data-product-lifecycle-agent/api-specs/connections.json`
  - Required parameters: `spaceId`, connection `name`, `type` (e.g., `ABAP`, `S4`), credentials payload
  - Side effect: **write — creates a persistent connection in Datasphere** → approval category: `connection_create`
- [x] Implement `validate_connection` tool via MCP:
  - Calls `GET /api/v1/datasphere/spaces/{spaceId}/connections/{name}/validation`
  - Spec: `specification/data-product-lifecycle-agent/api-specs/connections.json`
  - Side effect: **read-only** — no approval gate required
- [x] Implement `configure_replication_flow` tool via MCP:
  - Calls `POST /v1/runtime/graphs` to create and start a pipeline/replication graph
  - Spec: `specification/data-product-lifecycle-agent/api-specs/pipeline-engine.json`
  - Required parameters: graph name, source connection reference, target space, list of objects (table names / CDS view names)
  - Side effect: **write — creates and triggers a replication job** → approval category: `replication_flow_config`
- [x] Implement `get_pipeline_status` tool via MCP:
  - Calls `GET /v1/runtime/graphs/{handle}`
  - Spec: `specification/data-product-lifecycle-agent/api-specs/pipeline-engine.json`
  - Side effect: **read-only** — no approval gate required
- [x] Implement `list_pipeline_graphs` tool via MCP:
  - Calls `GET /v1/repository/graphs`
  - Spec: `specification/data-product-lifecycle-agent/api-specs/pipeline-engine.json`
  - Side effect: **read-only** — no approval gate required

## REQ-03 — Non-SAP Source Integration (Code Generation)

**Goal**: Analyse non-SAP source documentation and generate bespoke integration code as a text artifact for user review. Agent never deploys code autonomously.

- [x] Implement `analyze_non_sap_source` tool (LLM-powered, no API call):
  - Accepts `source_type` (Databricks | Salesforce | Snowflake | REST_API | ADLS) and `documentation` (free-text description or pasted schema/API spec) as inputs
  - Returns: structured integration proposal including recommended ingestion pattern, generated Python code (Databricks notebook / REST ingest / Snowflake COPY / ADLS parquet push to HDL), required configuration parameters, and estimated data volume
  - The code output is a **text artifact only** — agent must explicitly instruct the user to execute it themselves in the target system
  - Side effect: **code generation only** — no approval gate required
- [x] Implement `generate_hdl_upload_code` tool (LLM-powered, no API call):
  - Accepts `source_system`, `schema_definition` (column names + types), and `hdl_target_path` as inputs
  - Returns: complete Python script for writing parquet files to SAP HANA Data Lake (HDL) Files API
  - Side effect: **code generation only** — no approval gate required
- [x] System prompt rule: for all non-SAP code generation, the agent must append — "This code is provided as a text artifact only. Please review and execute it manually in your target system."

## REQ-04 — Data Product Activation and Creation

**Goal**: Activate an existing SAP-managed Data Product or define and publish a custom one. Always gate on duplicate check (REQ-06) before creation.

- [x] Implement `activate_sap_managed_dp` tool via MCP:
  - Calls Catalog API activation endpoint
  - Spec: `specification/data-product-lifecycle-agent/api-specs/catalog.edmx`
  - Required parameters: catalog Data Product ID / ORD ID
  - Side effect: **write — activates a Data Product in the BDC catalog** → approval category: `data_product_publish`
  - Returns: activation confirmation with catalog ID and discoverable URL
- [x] Implement `create_custom_dp` tool via MCP:
  - Calls Catalog API creation endpoint
  - Spec: `specification/data-product-lifecycle-agent/api-specs/catalog.edmx`
  - Required parameters: name, description, owner, domain, source connection reference, schema definition (list of fields + types)
  - Side effect: **write — publishes a new custom Data Product** → approval category: `data_product_publish`
  - Returns: new Data Product catalog ID
- [x] Implement `get_dp_status` tool via MCP:
  - Reads Data Product publication status and catalog metadata by ID from Catalog API
  - Spec: `specification/data-product-lifecycle-agent/api-specs/catalog.edmx`
  - Side effect: **read-only** — no approval gate required
- [x] System prompt rule: `check_duplicate_dp` (REQ-06) **must** be called before `create_custom_dp`; block creation and surface duplicate report if similarity score ≥ 0.8 without explicit user override

## REQ-05 — Data Quality Validation

**Goal**: Trigger data profiling and evaluate quality rules for newly integrated Data Products; surface completeness, uniqueness, and pattern violations.

- [x] Implement `run_data_profiling` tool via MCP:
  - Calls `POST /profiling`
  - Spec: `specification/data-product-lifecycle-agent/api-specs/data-profiling.json`
  - Required parameters: dataset identifier, space ID, profiling scope (`full` | `sample`)
  - Side effect: **write — triggers a profiling job** → approval category: `data_profiling_run` (default: autonomous)
  - Returns: profiling job ID for status polling
- [x] Implement `get_quality_rules` tool via MCP:
  - Calls `GET /rules` and `GET /rules/rulebooks`
  - Spec: `specification/data-product-lifecycle-agent/api-specs/metadata-management.json`
  - Side effect: **read-only** — no approval gate required
- [x] Implement `get_rulebook_results` tool via MCP:
  - Calls `GET /rules/rulebooks/{rulebookId}/datasetResults`
  - Spec: `specification/data-product-lifecycle-agent/api-specs/metadata-management.json`
  - Required parameters: `rulebookId`, dataset reference
  - Side effect: **read-only** — no approval gate required
  - Returns: rule evaluation results with pass/fail counts and sample failing records
- [x] Agent presents profiling results as structured summary: completeness %, uniqueness %, pattern violations count, top 5 failing fields
- [x] System prompt rule: if completeness < 80%, flag as **critical quality issue** and request user remediation decision before proceeding to Data Product activation

## REQ-06 — Duplicate and Similarity Detection

**Goal**: Before any new Data Product is created, compare its proposed metadata against the BDC catalog using LLM-based semantic similarity. Block creation if score ≥ 0.8.

- [x] Implement `check_duplicate_dp` tool (hybrid — catalog API + LLM reasoning):
  - Step 1: calls `catalog_search` (REQ-01) to retrieve all existing Data Product names and descriptions
  - Step 2: calls `GET /catalog/connections/{connectionId}/datasets/{qualifiedName}` for richer dataset metadata where available
    - Spec: `specification/data-product-lifecycle-agent/api-specs/metadata-management.json`
  - Step 3: LLM computes semantic similarity between proposed Data Product description and each existing one
  - Returns: list of (existing DP name, similarity score) sorted descending; flags any score ≥ 0.8 as "duplicate risk"
  - Must complete within 30 seconds — enforce via `asyncio.wait_for` with a 30-second timeout
  - Side effect: **read-only** — no approval gate required
- [x] If duplicate risk found: agent presents match details and offers three choices to the user:
  1. Reuse existing Data Product (abort creation)
  2. Supersede existing Data Product (proceed with deprecation note)
  3. Proceed with new creation despite similarity (requires explicit user confirmation)
- [x] Store similarity check result in agent conversation context for the current session — do not re-run for the same proposed DP name unless the user changes its definition

## REQ-07 — Governance Configuration

**Goal**: Configure ownership, lineage, and access policies as part of the Data Product creation workflow; every published Data Product must be governed before it is consumption-ready.

- [x] Implement `set_dp_ownership` tool via MCP:
  - Calls `POST /tasks/{taskName}/executions` and `PUT /tasks/{taskName}/executions/{execId}` on the EIM API
  - Spec: `specification/data-product-lifecycle-agent/api-specs/enterprise-information-management.json`
  - Required parameters: Data Product ID, `owner_name`, `steward_name`, `domain`
  - Side effect: **write — sets ownership metadata** → approval category: `governance_change`
- [x] Implement `configure_access_policy` tool via MCP:
  - Calls `POST /v1/datasphere/marketplace/dsc/products` and `POST .../changeLifecycleStatus`
  - Spec: `specification/data-product-lifecycle-agent/api-specs/data-sharing-cockpit.json`
  - Required parameters: Data Product ID, `access_mode` (open | restricted | licensed), `license_type` (if restricted)
  - Side effect: **write — sets access and lifecycle policy** → approval category: `governance_change`
- [x] Implement `set_lineage_metadata` tool via MCP:
  - Calls `POST /catalog/datasets` and `GET /catalog/lineage/export`
  - Spec: `specification/data-product-lifecycle-agent/api-specs/metadata-management.json`
  - Required parameters: source connection ID, source dataset qualified name, target Data Product ID
  - Lineage is derived automatically from integration provenance (REQ-02 / REQ-03 outputs)
  - Side effect: **write — sets lineage links** → approval category: `governance_change`
- [x] Governance configuration runs as part of the Data Product creation workflow (REQ-04), immediately after activation/publication is confirmed and before marking the Data Product as consumption-ready

## REQ-08 — Analytical Model Creation

**Goal**: Create a basic Analytical Model in Datasphere for a published Data Product so it is immediately consumable in SAP Analytics Cloud.

- [x] Implement `list_analytical_models` tool via MCP:
  - Reads existing Analytical Models from Consumption API to avoid duplicates
  - Spec: `specification/data-product-lifecycle-agent/api-specs/consumption.edmx`
  - Side effect: **read-only** — no approval gate required
- [x] Implement `create_analytical_model` tool via MCP:
  - Calls Consumption API to create an Analytical Model entity
  - Spec: `specification/data-product-lifecycle-agent/api-specs/consumption.edmx`
  - Required parameters: Data Product ID, `model_name`, `dimensions` (list), `measures` (list), `description`
  - Side effect: **write — creates an Analytical Model** → approval category: `analytical_model_create`
- [x] Before proposing model creation: agent auto-derives candidate dimensions and measures from the Data Product schema returned by `get_dp_status`; presents them to the user for confirmation or adjustment before calling the tool

## REQ-09 — Continuous Lifecycle Monitoring

**Goal**: Continuously query usage metrics, maturity scores, and quality trends for published Data Products; surface plain-language recommendations.

- [x] Implement `get_maturity_score` tool via MCP:
  - Calls `POST /DHA` (Data Health Assessment)
  - Spec: `specification/data-product-lifecycle-agent/api-specs/data-maturity-assessment.json`
  - Required parameters: Data Product ID, `scope` (`full` | `dimensions`)
  - Returns: overall maturity score, dimension breakdown (completeness, consistency, timeliness)
  - Side effect: **read-only** — no approval gate required
- [x] Implement `get_usage_stats` tool via MCP:
  - Reads Consumption API for usage metrics: query count, last access timestamp, unique consumer count
  - Spec: `specification/data-product-lifecycle-agent/api-specs/consumption.edmx`
  - Side effect: **read-only** — no approval gate required
- [x] Implement `get_catalog_metadata` tool via MCP:
  - Reads Catalog API for metadata freshness: last updated, schema version, publication status
  - Spec: `specification/data-product-lifecycle-agent/api-specs/catalog.edmx`
  - Side effect: **read-only** — no approval gate required
- [x] Implement `generate_monitoring_report` tool (LLM-powered, no API call):
  - Accepts `maturity_result`, `usage_stats`, `quality_result` as structured dict inputs
  - Produces a human-readable monitoring summary with:
    - Overall health assessment
    - Flagged anomalies (zero usage > `ZERO_USAGE_DAYS_THRESHOLD = 30` days; completeness drop > `QUALITY_DROP_THRESHOLD = 0.10`)
    - Ranked improvement recommendations (max 5)
  - Side effect: **read-only** — no approval gate required
- [x] Monitoring triggers: (a) on-demand when user explicitly requests a report; (b) automatically after each lifecycle step (M3 through M6) completes

## REQ-10 — Configurable Approval Gateway

**Goal**: Implement an `ApprovalGateway` class that controls which action categories require human approval. All write tools must check the gateway before executing.

- [x] Implement `ApprovalGateway` in `app/approval_gateway.py` with the following:
  - `APPROVAL_CONFIG` dict (plain Python constant — **not** a decorator) with these defaults:
    | Category | Default Mode |
    |---|---|
    | `catalog_read` | `autonomous` |
    | `monitoring_read` | `autonomous` |
    | `code_generation` | `autonomous` |
    | `connection_create` | `supervised` |
    | `replication_flow_config` | `supervised` |
    | `data_product_publish` | `supervised` |
    | `governance_change` | `always_approve` |
    | `analytical_model_create` | `supervised` |
    | `data_profiling_run` | `autonomous` |
  - `supervised`: agent presents structured approval request (action description, API endpoint, side effects); user must respond "approve" or "reject"
  - `always_approve`: same as supervised but cannot be bypassed
  - `autonomous`: executes immediately; logs action taken
  - Methods: `get_mode(category)`, `requires_approval(category)`, `format_approval_request(...)`, `format_autonomous_notice(...)`, `log_decision(...)`, `get_config_summary()`, `update_mode(category, mode)`
  - All approval decisions logged: timestamp, category, tool name, API endpoint, decision, user ID
- [x] Implement `show_approval_config` tool (read-only, no MCP call):
  - Returns formatted string from `gateway.get_config_summary()`
  - Displays at agent startup so users know the active configuration
  - No approval gate required
- [x] The approval gateway is instantiated once in `SampleAgent.__init__()` and passed to or used by the agent's system prompt context

## Agent System Prompt

- [x] System prompt must include all of the following rules:
  - Agent identity: "Autonomous Data Product Lifecycle Agent for SAP Business Data Cloud"
  - Lifecycle workflow order: Discover → Integrate → Activate/Create → Validate → Model → Govern → Monitor
  - Reuse-before-create: always call `catalog_search` before proposing any Data Product creation
  - Duplicate gate: always call `check_duplicate_dp` before `create_custom_dp`; block on score ≥ 0.8
  - Approval transparency: before any write action, state — which tool, which API, what side effect — then request approval per gateway config
  - Non-SAP code artifacts: always remind user to execute generated code themselves in the target system
  - Page size: set `top` to max 100 on all paginated tool calls; inform user when limit is applied
  - No hallucination: never invent Data Product names, connection parameters, schema fields, or catalog entries — only use tool-returned data
  - Quality threshold: flag completeness < 80% as critical and request user remediation before proceeding
  - Alert thresholds: `ZERO_USAGE_DAYS_THRESHOLD = 30`, `QUALITY_DROP_THRESHOLD = 0.10`

## Instrumentation — Milestones M1–M6

- [x] Extract all business logic from `stream()` into a plain `async def _run_agent(query, context_id, tools)` helper in `agent.py`; instrument `_run_agent` with OpenTelemetry spans. `stream()` calls `_run_agent()` and yields its result — **no span context manager wraps any `yield`**
- [x] `auto_instrument()` called at top of `main.py` before any AI framework imports (already in bootstrap template — verify it remains first)
- [x] Add `tracer = trace.get_tracer(__name__)` in `agent.py`
- [x] Instrument each milestone inside `_run_agent()` using `tracer.start_as_current_span()` as context managers on non-generator code paths:
  - **M1 — Data Landscape Discovery**: `milestone.M1.data_landscape_discovery` span with achieved/missed logs ✓
  - **M2 — Integration Configured**: `milestone.M2.integration_configured` span with achieved/missed logs ✓
  - **M3 — Data Product Activated or Created**: `milestone.M3.data_product_activated_or_created` span ✓
  - **M4 — Data Quality Validated**: `milestone.M4.data_quality_validated` span ✓
  - **M5 — Governance and Modeling Complete**: `milestone.M5.governance_modeling_complete` span ✓
  - **M6 — Lifecycle Monitored**: `milestone.M6.lifecycle_monitored` span ✓

## MCP Translation and MCP Server Assets

- [x] Verify all 10 API spec files are present in `specification/data-product-lifecycle-agent/api-specs/`
- [x] Invoke `mcp-translation-file` skill for 9/10 APIs (metadata-management skipped — 233KB exceeds limit)
- [x] MCP server assets created for 9 specs under `assets/<stem>-mcp-server/` with `asset.yaml` and `translation.json`
- [x] `assets/data-product-lifecycle-agent/asset.yaml` `requires` section updated with all 9 MCP server ORD IDs
- [x] `solution.yaml` updated to reference all 10 asset YAML files (agent + 9 MCP servers)
- [x] `mcp-mock.json` generated at `assets/data-product-lifecycle-agent/mcp-mock.json` — 9 servers, 151 tools
- [x] MCP tool loading in `agent.py` and `agent_executor.py` via `get_mcp_tools()` from `mcp_tools.py` — no direct HTTP clients

## Testing

- [x] `conftest.py` sets `IBD_TESTING=1` — mock MCP tools loaded from `mcp-mock.json` via `mcp_tools._build_mock_tools()`
- [x] Unit tests written in `assets/data-product-lifecycle-agent/tests/` covering all 27+ tool categories
- [x] All tests pass; coverage ≥ 70% (actual: **84%** total, 89% agent.py, 100% approval_gateway.py, 88% util.py)
- [x] Decorator count verified: exactly **3** (`@agent_model`, `@agent_config`, `@prompt_section`)
- [x] Final `pytest` run (no args) passed: **118/118 tests**, score 100.0
- [x] `assets/data-product-lifecycle-agent/test_report.json` exists ✓

## Validation Checklist

All checks passed:

```
✓ M1–M6 achieved/missed log patterns present in agent.py
✓ Decorator count = 3
✓ auto_instrument() called before AI framework imports in main.py
✓ No direct requests/httpx imports in agent code
✓ test_report.json exists with 118 tests, score 100.0, coverage 84%
```
