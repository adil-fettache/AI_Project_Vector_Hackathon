# Specification: bdc-data-lifecycle-agent

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-agent.md](../guidelines-agent.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [x] Read `product-requirements-document.md` (full PRD for the Autonomous Data Product Lifecycle Agent)
- [x] Bootstrap agent code in `assets/bdc-data-lifecycle-agent/` using skill `sap-agent-bootstrap` (invoke from inside `assets/bdc-data-lifecycle-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

## API Spec Files

The following API spec files were discovered but could not be downloaded due to pre-signed URL restrictions. They are listed here for reference — the MCP translation skill will need to be re-run at implementation time or the existing datasphere-management-agent MCP servers re-used where applicable.

**Discovered APIs (all require custom MCP server generation):**
- `data-products.json` — BDC Data Products API (ORD ID: `sap.clm:apiResource:DataProducts:v1`) — OpenAPI
- `catalog.edmx` — Datasphere Catalog OData API — EDMX (preferred over JSON)
- `connections.json` — Datasphere Connections REST API — OpenAPI
- `tasks.json` — Datasphere Tasks REST API — OpenAPI
- `monitoring.json` — Datasphere Monitoring REST API — OpenAPI
- `monitoring-query.json` — Datasphere Monitoring Query (Cloud Edition) REST API — OpenAPI
- `metadata-management.json` — Metadata Management Cloud Edition REST API — OpenAPI
- `dqm.json` — SAP Data Quality Management microservices REST API — OpenAPI
- `certificates.json` — Datasphere Certificates REST API — OpenAPI
- `sac.json` — SAP Analytics Cloud Activities Service REST API — OpenAPI

**Re-use existing MCP server assets** (already created for datasphere-management-agent) where the API surface matches:
- `catalog-datasphere-mcp-server` — ORD ID: `customer.mcpbuilder.datasphere:apiResource:data-product-lifecycle-agent-3eafb_catalog-datasphere-mcp-server:v1`
- `connections-datasphere-mcp-server` — ORD ID: `customer.mcpbuilder.datasphere:apiResource:data-product-lifecycle-agent-3eafb_connections-datasphere-mcp-server:v1`
- `tasks-datasphere-mcp-server` — ORD ID: `customer.mcpbuilder.datasphere:apiResource:data-product-lifecycle-agent-3eafb_tasks-datasphere-mcp-server:v1`

## R01 — Landscape Discovery (M1)

- [x] Implement `list_spaces` tool: calls Datasphere Catalog MCP server to list all Datasphere spaces; returns structured list with space ID, name, status
- [x] Implement `list_connections` tool: calls Connections MCP server to enumerate all registered connections; returns connection ID, name, type, status
- [x] Implement `list_data_products` tool: calls BDC Data Products MCP server to list SAP-managed Data Products; returns name, type, activation status, target space
- [x] Implement `list_custom_artifacts` tool: calls Catalog MCP server to list custom Datasphere artifacts (SQL Views, Graphical Views, Transformation Flows, Analytic Models) per space
- [x] Implement `summarize_landscape` tool: orchestrates the above 4 tools and produces a single structured landscape summary; emits M1 milestone log on completion
- [x] Log pattern: `M1.achieved: BDC landscape mapped — {space_count} spaces, {connection_count} connections, {data_product_count} data products, {workspace_count} Databricks workspaces discovered`
- [x] Log on miss: `M1.missed: landscape discovery incomplete — one or more API calls failed or returned empty; partial results surfaced to user`

## R02 — SAP-Managed Data Product Activation (M2)

- [x] Implement `search_sap_data_products` tool: searches BDC Data Products API for products matching user's stated intent (name/type/application); returns matching candidates with metadata
- [x] Implement `get_data_product_details` tool: fetches full details of a specific SAP-managed Data Product (schema, dependencies, target space requirements)
- [x] Implement `propose_activation_plan` tool: generates a human-readable activation plan for a specific Data Product including: target space, estimated impact, prerequisite checks; halts for user confirmation — NEVER activates without explicit approval
- [x] Implement `activate_data_product` tool: **HIGH-RISK — requires prior human confirmation stored in context**; calls BDC Data Products API activation endpoint; reports success/failure with detail
- [x] Human-in-the-loop gate: agent system prompt must instruct the LLM to always call `propose_activation_plan` before `activate_data_product`; `activate_data_product` must check confirmation flag in context and refuse to proceed if not set
- [x] M2 milestone log on proposal confirmed: `M2.achieved: data product proposal confirmed by user — type={product_type}, name={product_name}, target_space={space_id}`
- [x] M2 milestone log on miss: `M2.missed: data product proposal not confirmed — user declined or agent could not identify a matching product for the stated intent`

## R03 — Generic Non-SAP Source Integration (M3)

- [x] Implement `retrieve_integration_docs` tool: given a system name and optional URL hint, retrieves the target system's integration documentation dynamically (does NOT hardcode connectors); returns raw documentation text
- [x] Implement `determine_integration_protocol` tool: given integration documentation, instructs the LLM to determine the appropriate protocol (REST, JDBC, SFTP, OData, GraphQL, or other) and extract required connection parameters; returns protocol + parameter schema
- [x] Implement `propose_connection_plan` tool: generates a human-readable connection registration plan including: protocol, endpoint, auth method, Datasphere connection type; halts for user confirmation — NEVER registers without approval
- [x] Implement `register_connection` tool: **HIGH-RISK — requires prior human confirmation**; calls Connections MCP server `create_connection` endpoint; validates the registered connection; reports outcome
- [x] Implement `validate_connection` tool: calls Connections MCP server to validate an existing connection; returns status (active/inactive/error) with detail
- [x] Non-SAP integration: protocol captured as variable — never hardcoded; Jira (REST) and PostgreSQL (JDBC) are reference examples only
- [x] M3 milestone logs:
  - Achievement: `M3.achieved: source connection active — system={source_system}, protocol={protocol}, connection_id={connection_id}, space={space_id}`
  - Miss: `M3.missed: source connection could not be established — system={source_system}, reason={failure_reason}`

## R04 — Custom Data Product Creation (M2 → M4 path)

- [x] Implement `design_artifact` tool: given a natural language description, generates the Datasphere artifact definition (SQL View, Graphical View, Transformation Flow, or Analytic Model); returns the artifact JSON/XML definition for review
- [x] Implement `propose_artifact_deployment` tool: presents the generated artifact definition and deployment plan to the user; halts for explicit confirmation — NEVER deploys without approval
- [x] Implement `deploy_artifact` tool: **HIGH-RISK — requires prior human confirmation**; calls Tasks MCP server to deploy the artifact to the target space; monitors task execution; returns success/failure with logs
- [x] Artifact types supported: SQL View, Graphical View, Transformation Flow, Analytic Model
- [x] Agent system prompt must instruct LLM to route low-confidence artifact generations to the user for review before any deployment call

## R05 — Data Quality Enforcement as Deployment Gate (M4)

- [x] Implement `define_quality_rules` tool: accepts quality rule definitions in natural language; converts to structured DQM rule format; supports: completeness, freshness, referential integrity, and custom rules; stores rules in agent context
- [x] Implement `evaluate_quality_rules` tool: calls DQM MCP server to evaluate defined rules against a target Data Product or dataset; returns per-rule results with severity (info/warning/critical)
- [x] Implement `run_quality_gate` tool: orchestrates `evaluate_quality_rules`; if ANY critical violation is found, blocks deployment and returns a blocking report — NO override possible; if gate passes, returns PASS status; emits M4 milestone logs accordingly
- [x] Quality gate is a hard block: `deploy_artifact` and `activate_data_product` MUST check quality gate status before proceeding; if gate has not been run or returned critical violations, both tools must refuse and instruct the user to run `run_quality_gate` first
- [x] Implement `monitor_quality_continuously` tool: registers quality monitoring rules with the Monitoring Query API for a deployed Data Product; enables ongoing rule evaluation
- [x] M4 milestone logs:
  - Achievement: `M4.achieved: data product deployed and quality gate passed — name={product_name}, artifacts={artifact_list}, quality_status=PASS`
  - Miss: `M4.missed: data product deployment blocked or failed — name={product_name}, reason={reason}, critical_violations={violation_count}`

## R06 — Governance and Metadata Management

- [x] Implement `read_catalog_metadata` tool: reads governance metadata for a Data Product from the BDC catalog via Catalog MCP server; returns description, owner, tags, lineage
- [x] Implement `propose_metadata_update` tool: generates proposed metadata (description, owner, tags, lineage) for a Data Product; presents to user for review — NEVER writes without approval
- [x] Implement `write_catalog_metadata` tool: **WRITE ACTION — requires prior human confirmation**; calls Metadata Management MCP server to write governance metadata; returns confirmation with updated fields
- [x] Metadata completeness check: after writing, agent verifies all mandatory fields (description, owner, tags) are populated; reports any gaps

## R07 — SAP Analytics Cloud Consumption (M5)

- [x] Implement `check_sac_connectivity` tool: tests connectivity to the SAC endpoint via SAC MCP server; returns status and available capabilities
- [x] Implement `propose_sac_publication` tool: generates a SAC model/story publication plan for a deployed Data Product; presents plan to user for review — NEVER publishes without explicit approval
- [x] Implement `publish_to_sac` tool: **HIGH-RISK — requires prior human confirmation**; calls SAC MCP server to publish the Data Product model/story; returns SAC URL or identifier on success
- [x] M5 milestone log:
  - Achievement: `M5.achieved: monitoring active and SAC delivery complete — product={product_name}, monitoring_rules={rule_count}, sac_url={sac_url}`
  - Miss: `M5.missed: post-deployment setup incomplete — monitoring={monitoring_status}, sac_delivery={sac_status}, reason={reason}`

## R08 — Continuous Monitoring and Alerting (M5)

- [x] Implement `get_data_product_health` tool: calls Monitoring Query MCP server to retrieve current health status of a live Data Product; returns health score, active violations, last check timestamp
- [x] Implement `list_active_alerts` tool: queries Monitoring MCP server for active alerts on a Data Product; returns alert list with severity, rule, and recommended remediation
- [x] Implement `set_alert_thresholds` tool: **WRITE ACTION — requires human confirmation**; configures alert thresholds for a Data Product in the Monitoring API; returns confirmation
- [x] M5 monitoring component logged together with SAC delivery (see R07 M5 log above)

## Agent System Prompt & Instrumentation

- [x] Write system prompt in `app/agent.py` `@prompt_section` that:
  - Instructs LLM to never hallucinate data; always call appropriate tools to retrieve real data
  - Sets page size limit (`top`) to maximum 100 on every tool call that accepts it; informs user when limit applied
  - Lists the 5 milestones (M1–M5) and instructs the agent to log them using the patterns above
  - Enumerates all HIGH-RISK tools and instructs the LLM to ALWAYS call the corresponding proposal/plan tool first and confirm with the user before calling the high-risk action tool
  - Instructs LLM that data quality gate (`run_quality_gate`) must pass before any deployment action
  - Instructs LLM on generic non-SAP integration pattern: retrieve docs → determine protocol → propose → confirm → register
  - Instructs LLM to surface MCP tool call failures to the user with full detail; do not silently retry write operations
- [x] Implement OpenTelemetry custom spans:
  - Extract all business logic from `stream()` into `_run_agent()` helper (async, non-generator)
  - Apply `@tracer.start_as_current_span("landscape_discovery")` on landscape discovery logic
  - Apply `@tracer.start_as_current_span("data_product_activation")` on activation logic
  - Apply `@tracer.start_as_current_span("source_integration")` on non-SAP integration logic
  - Apply `@tracer.start_as_current_span("quality_gate")` on quality gate logic
  - Apply `@tracer.start_as_current_span("sac_publication")` on SAC publication logic
- [x] Verify `auto_instrument()` is called at top of `main.py` before any AI framework imports
- [x] Verify `app/agent.py` has exactly 3 decorated functions: `@agent_model`, `@agent_config` (temperature), `@prompt_section`

## MCP Tool Layer Setup

- [x] Re-use existing MCP server assets for Catalog, Connections, Tasks (already in solution):
  - `catalog-datasphere-mcp-server` (ORD ID: `customer.mcpbuilder.datasphere:apiResource:data-product-lifecycle-agent-3eafb_catalog-datasphere-mcp-server:v1`)
  - `connections-datasphere-mcp-server` (ORD ID: `customer.mcpbuilder.datasphere:apiResource:data-product-lifecycle-agent-3eafb_connections-datasphere-mcp-server:v1`)
  - `tasks-datasphere-mcp-server` (ORD ID: `customer.mcpbuilder.datasphere:apiResource:data-product-lifecycle-agent-3eafb_tasks-datasphere-mcp-server:v1`)
- [x] Generate new MCP server assets via `mcp-translation-file` → `setup-solution` for:
  - `data-products.json` → `bdc-data-products-mcp-server`
  - `monitoring.json` + `monitoring-query.json` → `monitoring-datasphere-mcp-server`
  - `dqm.json` → `dqm-mcp-server`
  - `metadata-management.json` → `metadata-management-mcp-server`
  - `certificates.json` → `certificates-datasphere-mcp-server`
  - `sac.json` → `sac-mcp-server`
  - **Note:** If `mcp-translation-file` skill is unavailable, skip MCP server asset creation for these APIs. Agent will mock them in tests. Log: `[MCP-SKILL] mcp-translation-file unavailable — skipping MCP server asset generation.`
- [x] Add ALL MCP server dependencies to `assets/bdc-data-lifecycle-agent/asset.yaml` under `requires`:
  - `bdc-data-products-mcp-server` (kind: mcp-server)
  - `catalog-datasphere-mcp-server` (kind: mcp-server)
  - `connections-datasphere-mcp-server` (kind: mcp-server)
  - `tasks-datasphere-mcp-server` (kind: mcp-server)
  - `monitoring-datasphere-mcp-server` (kind: mcp-server)
  - `dqm-mcp-server` (kind: mcp-server)
  - `metadata-management-mcp-server` (kind: mcp-server)
  - `certificates-datasphere-mcp-server` (kind: mcp-server)
  - `sac-mcp-server` (kind: mcp-server)
- [x] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from `mcp_tools` module — NEVER use direct HTTP clients
- [x] Generate `mcp-mock.json` using `mcp-mock-config` skill after all MCP server assets are in place
  - `mcp-mock.json` must include mock responses for all 9 MCP servers listed above (create stubs if new servers not yet generated)

## Business Step Instrumentation

- [x] All 5 milestones (M1–M5) emit structured log statements on achievement and miss (patterns defined per requirement above)
- [x] All deployment gate decisions (quality PASS/BLOCK, human confirmation ACCEPT/REJECT) are logged with decision context
- [x] Log pattern verified: `grep -r "M[1-5]\.\(achieved\|missed\)" assets/bdc-data-lifecycle-agent/app/` must return results for all 5 milestones

## Testing

- [x] `conftest.py` only sets `IBD_TESTING=true` — causes agent to run with mock MCP tool results during tests
- [x] Write unit tests in `assets/bdc-data-lifecycle-agent/tests/` — exactly one per tool:
  - `test_list_spaces.py` — mocks Catalog MCP, verifies structured response
  - `test_list_connections.py` — mocks Connections MCP, verifies connection list
  - `test_list_data_products.py` — mocks BDC Data Products MCP, verifies product list
  - `test_list_custom_artifacts.py` — mocks Catalog MCP, verifies artifact list
  - `test_summarize_landscape.py` — verifies M1 milestone log emitted
  - `test_search_sap_data_products.py` — mocks BDC Data Products MCP, verifies search results
  - `test_get_data_product_details.py` — mocks BDC Data Products MCP, verifies detail response
  - `test_propose_activation_plan.py` — verifies plan presented, no activation called, M2 log emitted
  - `test_activate_data_product.py` — verifies refuses without confirmation flag; verifies activation called when flag set
  - `test_retrieve_integration_docs.py` — mocks doc retrieval, verifies non-empty doc text returned
  - `test_determine_integration_protocol.py` — verifies protocol extracted from docs
  - `test_propose_connection_plan.py` — verifies plan presented, no registration called
  - `test_register_connection.py` — verifies refuses without confirmation; verifies Connections MCP called when confirmed
  - `test_validate_connection.py` — mocks Connections MCP, verifies active status returned
  - `test_design_artifact.py` — verifies artifact definition generated for each supported type
  - `test_propose_artifact_deployment.py` — verifies plan presented, no deployment called
  - `test_deploy_artifact.py` — verifies refuses without confirmation; verifies Tasks MCP called when confirmed
  - `test_define_quality_rules.py` — verifies rules structured and stored in context
  - `test_evaluate_quality_rules.py` — mocks DQM MCP, verifies per-rule results
  - `test_run_quality_gate.py` — verifies PASS on no critical violations; verifies BLOCK on critical violation; verifies M4 log emitted
  - `test_monitor_quality_continuously.py` — mocks Monitoring MCP, verifies rules registered
  - `test_read_catalog_metadata.py` — mocks Catalog MCP, verifies metadata returned
  - `test_propose_metadata_update.py` — verifies proposal presented, no write called
  - `test_write_catalog_metadata.py` — verifies refuses without confirmation; verifies Metadata Mgmt MCP called when confirmed
  - `test_check_sac_connectivity.py` — mocks SAC MCP, verifies connectivity status
  - `test_propose_sac_publication.py` — verifies plan presented, no publish called
  - `test_publish_to_sac.py` — verifies refuses without confirmation; verifies SAC MCP called when confirmed; M5 log emitted
  - `test_get_data_product_health.py` — mocks Monitoring Query MCP, verifies health score returned
  - `test_list_active_alerts.py` — mocks Monitoring MCP, verifies alert list returned
  - `test_set_alert_thresholds.py` — verifies refuses without confirmation; verifies Monitoring MCP called when confirmed
- [x] Run each unit test immediately after writing it
- [x] Write one integration test (`test_integration.py`) — exercises end-to-end flow: landscape discovery → data product selection → quality gate → deployment (all mock); verifies all 5 milestone logs emitted in sequence
- [x] Run `pytest` from `assets/bdc-data-lifecycle-agent/` (no args, no extra flags)
- [x] If coverage < 70%, add targeted tests until threshold met
- [x] Verify `assets/bdc-data-lifecycle-agent/app/agent.py` has exactly 3 decorated functions — run `grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/bdc-data-lifecycle-agent/app/agent.py` → must return 3
- [x] Run `pytest` again (no args) to generate final `test_report.json`
- [x] Verify `assets/bdc-data-lifecycle-agent/test_report.json` exists

## Validation Checklist

```bash
# Milestone instrumentation — all 5 milestones present
grep -r "M1\.achieved" assets/bdc-data-lifecycle-agent/app/    # must return results
grep -r "M2\.achieved" assets/bdc-data-lifecycle-agent/app/    # must return results
grep -r "M3\.achieved" assets/bdc-data-lifecycle-agent/app/    # must return results
grep -r "M4\.achieved" assets/bdc-data-lifecycle-agent/app/    # must return results
grep -r "M5\.achieved" assets/bdc-data-lifecycle-agent/app/    # must return results

# Decorators — exactly 3
grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/bdc-data-lifecycle-agent/app/agent.py  # must return 3

# Test report
ls assets/bdc-data-lifecycle-agent/test_report.json           # must exist
```
