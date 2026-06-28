# Product Requirements Document (PRD)

**Title:** Autonomous Data Product Lifecycle Agent for SAP Business Data Cloud  
**Date:** 2026-06-25  
**Owner:** Data Platform Team  
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Data platform teams today spend hours manually navigating 8+ APIs and UIs to bring a single Data Product to life in SAP Business Data Cloud. This agent replaces that manual orchestration with a single natural language interface — from landscape discovery to SAP Analytics Cloud delivery — with a human confirming only what matters.

**Business Need:**  
Organizations running SAP Business Data Cloud face a fragmented, expert-dependent process for managing Data Product lifecycles. There is no unified orchestration layer that can discover the BDC landscape, activate SAP-managed and custom Data Products, integrate non-SAP sources generically, enforce data quality as a hard deployment gate, and surface results in SAP Analytics Cloud — from a single entry point.

**Expected Value:**  
- Reduce time-to-production for a new Data Product from days to hours  
- Eliminate manual API orchestration across Datasphere, BDC, Databricks, and SAC  
- Prevent bad data from reaching consumers via automated quality gates  
- Enable non-expert users to trigger full Data Product lifecycles through natural language  

**Product Objectives (Prioritized):**
1. Deliver a working natural-language interface over the complete BDC Data Product lifecycle — from discovery to SAC consumption
2. Enforce data quality as a hard deployment gate: no Data Product with critical violations reaches production
3. Support generic non-SAP source integration (any system reachable via REST API, JDBC, SFTP, OData, GraphQL, or other protocols) — not limited to specific connectors
4. Minimize human intervention: automate all read/discovery operations; require human confirmation only for deployment and destructive actions
5. Provide continuous monitoring and alerting once a Data Product is live

---

## User Profiles & Personas

### Primary Persona: Alex — Data Engineer / Data Platform Engineer

Alex is a 34-year-old data engineer who owns the technical delivery of Data Products for his organization's SAP Business Data Cloud environment. He spends 60–70% of his day context-switching between Datasphere, BDC catalog, Databricks, and SAC to set up, connect, and validate data pipelines. He knows the APIs but finds the manual orchestration tedious and error-prone — a misconfigured connection or a skipped quality check can break a downstream report and take hours to diagnose. He wants an agent that handles the repetitive plumbing while keeping him in control of irreversible actions.

### Secondary Persona: Maya — Data Product Owner / Data Steward

Maya is a 41-year-old data product owner responsible for the quality, discoverability, and governance of the organization's Data Products. She is not an API expert, but she understands the business rules that data must satisfy. She is frustrated that enforcing data quality rules currently requires coordination with engineering. She needs a tool that lets her define quality rules in plain language and ensures they are enforced before any Data Product goes live.

### Tertiary Persona: Ben — Business Analyst

Ben is a 29-year-old analyst who consumes Data Products in SAP Analytics Cloud. He doesn't build data pipelines, but he is often blocked waiting for a Data Product to be activated or a new source to be integrated. He wants to describe what he needs in plain language and know when it's ready — without having to understand the underlying technical process.

---

## Goals and Non-Goals

### Goals (In Scope)

- Discover and map the full BDC environment: Datasphere spaces, connections, existing Data Products, and Databricks workspaces
- Activate SAP-managed Data Products (S/4HANA, SuccessFactors, Ariba, and others) with human confirmation at deployment steps
- Integrate non-SAP source systems generically — supporting any protocol (REST, JDBC, SFTP, OData, GraphQL, or custom) by dynamically retrieving the system's integration documentation and registering it via the Connections API
- Create custom Data Products in Datasphere: SQL Views, Graphical Views, Transformation Flows, and Analytic Models
- Define, enforce, and continuously monitor data quality rules (completeness, freshness, referential integrity, and custom rules); block deployment on critical violations
- Manage governance and metadata in the BDC catalog
- Consume and surface completed Data Products in SAP Analytics Cloud
- Provide lifecycle monitoring and alerting for live Data Products

### Non-Goals (Out of Scope)

- Datasphere Replication Flows (the available spec covers an unrelated SAP product — excluded; users are directed to the Datasphere UI)
- Building or managing Databricks notebooks or jobs (agent uses Databricks as a non-SAP integration surface, not a compute orchestration target)
- SAP Build Process Automation workflows (agent is Python-based; no SBPA dependency)
- Direct UI automation or screen scraping of any BDC or Datasphere interface

---

## Requirements

### Must-Have Requirements

**R01: Landscape Discovery**

- **Problem to Solve**: Users have no single view of their BDC environment — spaces, connections, existing Data Products, and Databricks workspaces are spread across multiple UIs.
- **User Story**: As a Data Engineer, I need the agent to map my full BDC landscape so that I can understand what exists before deciding what to build or activate.
- **Acceptance Criteria**:
  - Given the agent is initialized, when I ask "what does my BDC environment look like?", then the agent returns a structured summary of all Datasphere spaces, active connections, existing Data Products (SAP-managed and custom), and Databricks workspaces.
- **Maps to Objective**: 1
- **Priority Rank**: 1

**R02: SAP-Managed Data Product Activation**

- **Problem to Solve**: Activating an SAP-managed Data Product (e.g. S/4HANA Finance) requires navigating the BDC Data Products API manually, with no guided orchestration.
- **User Story**: As a Data Product Owner, I need the agent to identify the right SAP-managed Data Product and activate it — with my confirmation before any deployment action — so that I don't make irreversible changes by accident.
- **Acceptance Criteria**:
  - Given a user intent (e.g. "activate S/4HANA Finance Data Product in space FINANCE"), when the agent identifies the matching Data Product, then it presents the activation plan and waits for explicit user confirmation before proceeding.
  - Given confirmation, when the agent activates the Data Product, then it reports success or failure with detail.
- **Maps to Objective**: 1, 4
- **Priority Rank**: 2

**R03: Generic Non-SAP Source Integration**

- **Problem to Solve**: Connecting non-SAP systems requires knowing their specific API/protocol details, authentication methods, and Databricks integration patterns — knowledge that varies per system and is not codified anywhere accessible.
- **User Story**: As a Data Engineer, I need the agent to integrate any non-SAP source system by retrieving its technical integration documentation and registering it as a connection — without me writing custom code per system.
- **Acceptance Criteria**:
  - Given a non-SAP system name and credentials, when the agent is asked to integrate it, then it retrieves the system's integration documentation, determines the appropriate protocol (REST, JDBC, SFTP, OData, GraphQL, or other), and registers the connection via the Connections API.
  - The integration pattern must not be hardcoded to any specific protocol — it must work for any reachable system.
- **Maps to Objective**: 3
- **Priority Rank**: 3

**R04: Custom Data Product Creation**

- **Problem to Solve**: Creating a custom Data Product in Datasphere (SQL View, Graphical View, Transformation Flow, Analytic Model) requires API knowledge and manual artifact configuration.
- **User Story**: As a Data Engineer, I need the agent to generate and deploy the required Datasphere artifacts from a natural language description so that I can create custom Data Products without writing API calls by hand.
- **Acceptance Criteria**:
  - Given a description of the desired Data Product, when the agent generates the artifact definition, then it presents the plan for review and deploys only after user confirmation.
  - Artifacts supported: SQL View, Graphical View, Transformation Flow, Analytic Model.
- **Maps to Objective**: 1
- **Priority Rank**: 4

**R05: Data Quality Enforcement as Deployment Gate**

- **Problem to Solve**: Data Products are deployed without systematic quality checks, causing downstream consumers to receive incomplete, stale, or referentially broken data.
- **User Story**: As a Data Steward, I need data quality rules to be defined, evaluated, and enforced before any Data Product goes live so that only data meeting defined standards reaches consumers.
- **Acceptance Criteria**:
  - Given a Data Product ready for deployment, when the agent runs quality checks, then any Data Product with one or more critical violations is blocked from deployment with a clear explanation.
  - Quality rule types supported: completeness, freshness, referential integrity, and custom rules expressible in natural language.
  - Quality monitoring continues after deployment; alerts are raised on rule violations.
- **Maps to Objective**: 2
- **Priority Rank**: 5

**R06: Governance and Metadata Management**

- **Problem to Solve**: BDC catalog metadata is inconsistently populated, making Data Products hard to discover and govern.
- **User Story**: As a Data Steward, I need the agent to read and write governance metadata in the BDC catalog so that all Data Products are properly documented and discoverable.
- **Acceptance Criteria**:
  - Given a deployed Data Product, when the agent writes metadata (description, owner, tags, lineage), then the Data Product is discoverable in the BDC catalog with complete metadata.
- **Maps to Objective**: 1
- **Priority Rank**: 6

**R07: SAP Analytics Cloud Consumption**

- **Problem to Solve**: Business Analysts cannot consume a new Data Product in SAC until someone manually publishes a model or story — there is no automated delivery path.
- **User Story**: As a Business Analyst, I need the agent to make a deployed Data Product available in SAP Analytics Cloud so that I can start analyzing it immediately after go-live.
- **Acceptance Criteria**:
  - Given a live Data Product, when the agent is asked to surface it in SAC, then it pushes the model/story to SAC via the SAC REST API and reports the URL or identifier for access.
- **Maps to Objective**: 1
- **Priority Rank**: 7

**R08: Continuous Monitoring and Alerting**

- **Problem to Solve**: Once a Data Product is live, there is no automated mechanism to detect degradation, staleness, or quality drift.
- **User Story**: As a Data Engineer, I need the agent to continuously monitor a live Data Product and alert me on issues so that I can respond before consumers are impacted.
- **Acceptance Criteria**:
  - Given a live Data Product with active quality rules, when a rule violation is detected, then the agent emits an alert with the affected rule, severity, and recommended remediation.
- **Maps to Objective**: 5
- **Priority Rank**: 8

---

## Solution Architecture

**Architecture Overview:**  
A pro-code Python AI Agent following the A2A protocol, deployed on SAP BTP. All SAP API interactions go through a dedicated MCP tool layer (one MCP server per API surface). The agent uses a hybrid autonomy model: fully autonomous for read/discovery operations; human-in-the-loop confirmation required for all write, deployment, and activation actions.

**Key Components:**

- **Agent Core**: Python LangChain agent; natural language understanding + tool orchestration; implements 5 key milestone checkpoints
- **MCP Tool Layer**: Custom-generated MCP servers covering: BDC Data Products API, Datasphere Catalog, Connections, Tasks, Monitoring Query, Metadata Management, DQM microservices, Data Sharing Cockpit, Certificates, and SAC REST API
- **Non-SAP Integration Module**: Generic integration pattern — agent retrieves target system documentation dynamically, determines protocol, and registers via Connections API; no hardcoded connectors
- **Data Quality Engine**: Quality rule definition, evaluation (via DQM microservices + Monitoring Query API), continuous monitoring, and deployment gate logic
- **Human-in-the-Loop Gate**: Confirmation prompt injected before any deployment, activation, or destructive action; agent halts until explicit approval is received

**Integration Points:**

- SAP Business Data Cloud — Data Products API: SAP-managed Data Product discovery and activation
- SAP Datasphere — Catalog API: artifact discovery, metadata read/write
- SAP Datasphere — Connections API: connection registration and validation (SAP + non-SAP)
- SAP Datasphere — Tasks API: artifact deployment and task execution
- SAP Datasphere — Monitoring Query API: Data Product health and quality monitoring
- SAP Data Quality Management microservices: data quality rule evaluation
- SAP Metadata Management Cloud Edition: governance metadata read/write
- SAP Databricks (external): non-SAP source integration workspace
- SAP Analytics Cloud REST API: model/story publication for consumption
- SAP Datasphere — Certificates API: secure connectivity for non-SAP systems

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The agent exposes a capability registration pattern: new source systems, new API surfaces, or new artifact types can be added by providing a new MCP server without modifying the agent core
- The non-SAP integration module is a first-class extension point: any protocol supported by Databricks can be onboarded by supplying documentation — no code changes required
- Data quality rule types are extensible: new rule categories can be registered as named rule types alongside completeness, freshness, and referential integrity
- Extension authors: Data Engineers (new connectors), Data Stewards (new quality rule types), Platform Admins (new MCP servers)

**Business Step Instrumentation:**
- Each of the five key milestones emits structured log statements on achievement and on miss/skip
- Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`
- All deployment gate decisions (quality pass/block, human confirmation accept/reject) are logged with decision context for auditability

### Automation & Agent Behaviour

**Automation Level:** Hybrid — fully autonomous for read/discovery; human-gated for write/deployment/activation

**Actions the system performs without human approval:**
- Discover and map BDC landscape (spaces, connections, Data Products, Databricks workspaces)
- Search and retrieve integration documentation for non-SAP systems
- Evaluate data quality rules and generate quality reports
- Read governance metadata from the BDC catalog
- Monitor live Data Products and detect violations

**Actions that require human review or approval:**
- Activate an SAP-managed Data Product
- Register or modify a source connection (SAP or non-SAP)
- Deploy any Datasphere artifact (SQL View, Graphical View, Transformation Flow, Analytic Model)
- Write or update governance metadata in the BDC catalog
- Publish a model or story to SAP Analytics Cloud
- Any action classified as destructive (delete, deactivate, remove)

**Model:** SAP Generative AI Hub (LLM via SAP AI Core)

**Knowledge & data sources accessed:**

- SAP BDC Data Products API — SAP-managed Data Product catalog and activation
- SAP Datasphere APIs (Catalog, Connections, Tasks, Monitoring Query) — lifecycle management
- DQM microservices + Monitoring Query API — data quality evaluation and continuous monitoring
- Metadata Management Cloud Edition — governance metadata
- Databricks workspace — non-SAP integration surface
- SAC REST API — analytical consumption layer
- Third-party system documentation — dynamically retrieved for non-SAP integration

**Tools / MCP servers invoked:**

- `bdc-data-products-mcp-server` — read/activate SAP-managed Data Products (activation = high-risk, requires confirmation)
- `catalog-datasphere-mcp-server` — search artifacts, read/write metadata (metadata write = write action)
- `connections-datasphere-mcp-server` — list, create, validate connections (create = write action)
- `tasks-datasphere-mcp-server` — deploy artifacts, execute tasks (deploy = high-risk, requires confirmation)
- `monitoring-datasphere-mcp-server` — query Data Product health (read-only)
- `dqm-mcp-server` — evaluate quality rules (read-only; gate decision is in agent logic)
- `metadata-management-mcp-server` — governance metadata read/write (write = write action)
- `certificates-datasphere-mcp-server` — manage secure connectivity certificates (write = write action)
- `sac-mcp-server` — publish models/stories to SAC (publish = high-risk, requires confirmation)

**Guardrails & fail-safes:**
- Agent never modifies production artifacts without explicit human confirmation
- Data Products with one or more critical quality violations are hard-blocked from deployment — no override
- If an MCP server call fails, the agent reports the failure with detail and halts the affected workflow; it does not attempt silent retries on write operations
- If the agent cannot retrieve integration documentation for a non-SAP system, it surfaces the gap to the user and requests manual input before proceeding
- LLM confidence below threshold on artifact generation routes the proposed artifact to the user for review before deployment

---

## Milestones

### M1: Landscape Discovered

- **Description**: The agent has successfully mapped the full BDC environment available to the user.
- **Achieved when**: All Datasphere spaces, active connections, existing Data Products (SAP-managed and custom), and Databricks workspaces have been retrieved and summarized.
- **Log on achievement**: `M1.achieved: BDC landscape mapped — {space_count} spaces, {connection_count} connections, {data_product_count} data products, {workspace_count} Databricks workspaces discovered`
- **Log on miss**: `M1.missed: landscape discovery incomplete — one or more API calls failed or returned empty; partial results surfaced to user`

### M2: Data Product Identified / Proposed

- **Description**: The agent has identified the target SAP-managed Data Product or designed the structure for a custom Data Product, and the user has confirmed the proposal.
- **Achieved when**: The agent presents a Data Product activation plan or custom Data Product structure, and the user provides explicit confirmation.
- **Log on achievement**: `M2.achieved: data product proposal confirmed by user — type={product_type}, name={product_name}, target_space={space_id}`
- **Log on miss**: `M2.missed: data product proposal not confirmed — user declined or agent could not identify a matching product for the stated intent`

### M3: Source Connected

- **Description**: The required source system connection is validated and active — either an SAP source activated via BDC, or a non-SAP source integrated via Databricks using dynamically retrieved documentation and credentials for the appropriate protocol.
- **Achieved when**: The connection is registered, validated, and returns an active status from the Connections API.
- **Log on achievement**: `M3.achieved: source connection active — system={source_system}, protocol={protocol}, connection_id={connection_id}, space={space_id}`
- **Log on miss**: `M3.missed: source connection could not be established — system={source_system}, reason={failure_reason}`

### M4: Data Product Deployed

- **Description**: The Data Product is live in Datasphere: all required artifacts are created, all data quality rules have been applied, and no critical quality violations are present.
- **Achieved when**: Artifact deployment tasks complete successfully AND the quality gate passes (zero critical violations).
- **Log on achievement**: `M4.achieved: data product deployed and quality gate passed — name={product_name}, artifacts={artifact_list}, quality_status=PASS`
- **Log on miss**: `M4.missed: data product deployment blocked or failed — name={product_name}, reason={reason}, critical_violations={violation_count}`

### M5: Monitoring Active & Insight Delivered

- **Description**: Continuous quality monitoring is running, alerts are configured, and the Data Product is accessible for consumption in SAP Analytics Cloud.
- **Achieved when**: Monitoring rules are active in the Monitoring Query API, alert thresholds are set, and the Data Product model or story is published in SAC.
- **Log on achievement**: `M5.achieved: monitoring active and SAC delivery complete — product={product_name}, monitoring_rules={rule_count}, sac_url={sac_url}`
- **Log on miss**: `M5.missed: post-deployment setup incomplete — monitoring={monitoring_status}, sac_delivery={sac_status}, reason={reason}`

---

## Risks, Assumptions, and Dependencies

### Risks

- **API spec quality**: All BDC/Datasphere APIs require custom MCP server generation from raw OpenAPI/EDMX specs — spec completeness and accuracy may vary; gaps may require manual remediation.
- **Non-SAP integration accuracy**: The generic integration pattern relies on the agent correctly interpreting third-party documentation for unfamiliar protocols; human review of generated connection specs is recommended for novel systems.
- **SAC API scope**: The SAC REST API is not part of the BDC API discovery; it must be sourced and implemented as a separate MCP server — availability and coverage must be validated.
- **Deployment platform stability**: Recent Joule deployment jobs failed due to a container registry outage (`dhi.io`); deployment must be retried when the platform is confirmed stable.

### Assumptions

- All required BDC/Datasphere API credentials are available at agent runtime as environment variables — no `.env` files used.
- The Databricks workspace is accessible from the BTP runtime environment where the agent is deployed.
- SAC is provisioned and its REST API is accessible with appropriate credentials.
- Human-in-the-loop confirmation is delivered via the same conversational interface used to invoke the agent (no separate approval workflow system required).

### Dependencies

- SAP BDC Data Products API (`sap.clm:apiResource:DataProducts:v1`) — custom MCP server to be generated
- SAP Datasphere Catalog, Connections, Tasks, Monitoring Query, Metadata Management, DQM, Data Sharing Cockpit, Certificates APIs — custom MCP servers to be generated
- SAP Analytics Cloud REST API — custom MCP server to be sourced and generated
- SAP AI Core / Generative AI Hub — LLM runtime for agent
- Databricks workspace — non-SAP integration surface

---

## Appendix

### Glossary

- **BDC**: SAP Business Data Cloud — the unified data platform integrating Datasphere, HDL, and Databricks
- **Data Product**: A governed, discoverable, reusable data asset in BDC, either SAP-managed (pre-built for SAP applications) or custom (user-defined)
- **HDL**: SAP Hana Data Lake — the storage layer within BDC
- **MCP Server**: Model Context Protocol server — the tool adapter layer that exposes SAP APIs to the AI agent
- **Quality Gate**: A mandatory checkpoint before deployment that blocks any Data Product with critical data quality violations
- **A2A**: Agent-to-Agent protocol — the communication standard used by the agent runtime
- **SAC**: SAP Analytics Cloud — the BI and analytics platform where Data Products are consumed

### References

- SAP Business Data Cloud — Data Products API ORD ID: `sap.clm:apiResource:DataProducts:v1`
- SAP Datasphere API documentation: Catalog (EDMX + OpenAPI), Connections (OpenAPI), Tasks (OpenAPI), Monitoring Query (REST), Metadata Management (REST), DQM microservices (REST), Data Sharing Cockpit (REST), Certificates (REST)
- SAP Analytics Cloud REST API documentation
- RBA mapping: Governance E2E — BPS-456 (IT Governance), BPS-400 (Data Privacy/Protection), BPS-399 (Identity/Access Governance)
- Intent analysis: `intent.md`
