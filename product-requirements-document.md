# Product Requirements Document (PRD)

**Title:** Autonomous Data Product Lifecycle Agent  
**Date:** 2026-06-04  
**Owner:** Data Architecture / Data Governance Team  
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Data teams spend weeks manually wiring together source systems, defining Data Products, validating quality, and configuring governance in SAP Business Data Cloud — with no unified layer to coordinate it. This AI agent automates the entire lifecycle, from discovery to monitoring, presenting each action to the user for approval before execution.

**Business Need:**  
SAP Business Data Cloud and Datasphere offer powerful capabilities for managing Data Products, but the lifecycle is fragmented: identifying SAP-managed Data Products that can be reused, configuring integrations for new sources, avoiding duplicates, validating quality, building analytical models, and enforcing governance all require separate manual steps across multiple tools and APIs. There is no orchestration layer to guide a data steward or architect through the process end-to-end — resulting in delays, duplication, inconsistent governance, and underutilised SAP-managed assets.

**Expected Value:**
- Reduce Data Product time-to-delivery from weeks to hours by automating integration setup, quality validation, and governance configuration.
- Eliminate duplicate Data Products by scanning the BDC catalog for semantic similarity before creation.
- Maximise reuse of SAP-managed Data Products, reducing custom development overhead.
- Improve data quality and governance consistency across Finance, Procurement, Supply Chain, Sales, and HR domains.

**Product Objectives (Prioritized):**
1. Automate the end-to-end Data Product lifecycle — from source discovery to consumption-ready publication — with configurable human approval gates.
2. Detect and prevent duplicate or redundant Data Products by applying semantic similarity analysis on the BDC catalog.
3. Support SAP and non-SAP source system integration with intelligent connection configuration and code generation.
4. Continuously monitor usage, data quality, and governance health, surfacing actionable recommendations.

---

## User Profiles & Personas

### Primary Persona: Alex — Data Architect

Alex is a 38-year-old senior data architect at a large manufacturing enterprise using SAP S/4HANA, Salesforce, and Databricks. Alex is responsible for designing and managing the data architecture across Finance and Procurement domains in SAP Business Data Cloud. Every new data source requires Alex to manually configure connections, define Replication Flows, model data products, and coordinate governance — a process that takes 2–3 weeks per source. Alex is highly technical, comfortable with APIs and SQL, but frustrated by the repetitive, error-prone nature of lifecycle setup. Alex wants a conversational agent that can automate the boilerplate while keeping Alex in control of key decisions.

### Secondary Persona: Morgan — Data Steward

Morgan is a 31-year-old data steward responsible for ensuring data quality and governance compliance across the BDC catalog. Morgan monitors Data Product health, enforces ownership rules, and fields requests from business users across Sales and HR. Morgan often discovers that similar Data Products have been created by different teams without coordination, leading to inconsistency. Morgan is moderately technical, comfortable with the Datasphere UI but not with APIs. Morgan needs the agent to proactively surface duplicates, flag quality issues, and recommend governance actions in plain language.

### Other User Types

- **Analytics Engineers**: consume Data Products for SAP Analytics Cloud models; need high-quality, well-governed products.
- **IT Governance Managers**: oversee Data Product policies, access rights, and compliance with data privacy regulations.
- **Business Analysts (Finance, Procurement, Supply Chain, Sales, HR)**: define analytical requirements and validate that Data Products meet their domain needs.

---

## User Goals & Tasks

### For Alex (Data Architect):

**Goals:**
- Connect new SAP and non-SAP sources to BDC quickly and correctly without repetitive manual setup.
- Ensure new Data Products do not duplicate existing ones in the catalog.
- Publish Data Products that are analytically ready with proper models and governance from day one.

**Key Tasks:**
- Describe a new source system to the agent and receive an integration plan with recommended connection type and configuration.
- Review and approve generated Replication Flow configuration or non-SAP ingestion code before execution.
- Review and approve custom Data Product definitions proposed by the agent.
- Trigger data quality validation and review profiling results.

### For Morgan (Data Steward):

**Goals:**
- Maintain a clean, deduplicated BDC catalog without manually scanning every new submission.
- Ensure all Data Products have defined ownership, lineage, and access policies.
- Stay informed about quality degradation and usage trends without manual monitoring.

**Key Tasks:**
- Review agent-generated similarity alerts and decide whether to merge, supersede, or retain Data Products.
- Approve or modify governance recommendations (ownership, access policies, lineage tags).
- Review usage and data quality dashboards surfaced by the agent.

---

## Product Principles

1. **Agent proposes, human approves**: No irreversible action (connection creation, data product publication, governance policy change) executes without user confirmation, unless explicitly configured as autonomous.
2. **Reuse before create**: The agent always checks for existing SAP-managed or custom Data Products before proposing a new one.
3. **Domain-agnostic lifecycle**: The agent operates identically across Finance, Procurement, Supply Chain, Sales, and HR — no domain-specific hardcoding.
4. **Transparency by default**: Every agent action emits structured logs; every recommendation includes its reasoning and the API it will invoke.
5. **Configurable autonomy**: Approval requirements are configurable per action category — routine read operations can be fully autonomous; destructive or governance-sensitive actions always require confirmation.

---

## Business Context

**Current State:**  
Data teams manually coordinate across Datasphere UI, API scripts, and governance tools to deliver each Data Product. There is no unified agent; each lifecycle phase is isolated. Duplicate Data Products accumulate because there is no systematic similarity check. SAP-managed Data Products are underutilised because discovery is manual. Non-SAP integration requires bespoke scripting per source with no reusable framework.

**Strategic Alignment:**  
Accelerating Data Product delivery directly supports the enterprise's data mesh and data-as-a-product strategy within SAP Business Data Cloud, enabling faster and more reliable analytics consumption across all business domains.

**Success Criteria:**
- Data Product end-to-end lifecycle time reduced by ≥70% compared to current manual process.
- Zero net-new duplicate Data Products created after agent deployment (existing duplicates flagged within 30 days).
- 100% of agent-executed actions traceable via structured logs with full reasoning provenance.
- Data quality validation coverage ≥90% of newly created Data Products within 24 hours of publication.

---

## Goals and Non-Goals

### Goals (In Scope)

- Discover and surface SAP-managed Data Products available for activation in the BDC catalog.
- Create and configure connections to SAP Applications such as S/4HANA and non-SAP sources (Databricks, Salesforce, Snowflake, REST APIs, Azure Data Lake) in SAP Datasphere.
- Configure and trigger Replication Flows for SAP sources; generate and propose ingestion code for non-SAP sources.
- Activate SAP-managed Data Products; define and publish custom Data Products.
- Run data profiling and quality validation; surface issues with remediation recommendations.
- Create Analytical Models in Datasphere and configure governance (ownership, lineage, access policies).
- Detect duplicate or semantically similar Data Products in the catalog.
- Continuously monitor usage metrics, data quality trends, and maturity scores; emit improvement recommendations.
- Support configurable human-in-the-loop approval gates per action category.

### Non-Goals (Out of Scope)

- Building a custom Datasphere or BDC UI — the agent operates via API and conversational interface only.
- Executing approved actions in external systems (e.g., Databricks) beyond what the generated code describes — deployment into external platforms requires user-managed execution.
- Replacing SAP Privacy Governance or SAP Cloud Identity Access Governance for enterprise-wide data privacy and IAM.
- Managing SAP Analytics Cloud stories or reports (analytics consumption layer is out of scope).

---

## Requirements

### Must-Have Requirements

**REQ-01**: Data Landscape Discovery

- **Problem to Solve**: Data architects do not know which SAP-managed Data Products in the BDC catalog can be immediately activated and reused, nor which sources have already been integrated.
- **User Story**: As a Data Architect, I need the agent to scan the BDC catalog and present available SAP-managed Data Products relevant to my domain so that I avoid creating redundant custom Data Products.
- **Acceptance Criteria**:
  - Given a user query specifying a domain (e.g., Finance), when the agent scans the Catalog API, then it returns a list of SAP-managed Data Products available for activation, grouped by relevance.
  - Given the scan result, when the user selects a Data Product, then the agent presents the activation steps and requests approval before executing.
- **Maps to Objective**: Objective 1 (automate lifecycle), Objective 2 (prevent duplicates)
- **Priority Rank**: 1

**REQ-02**: SAP Source Integration (S/4HANA)

- **Problem to Solve**: Configuring connections and Replication Flows to S/4HANA in Datasphere requires multiple manual API calls and is error-prone.
- **User Story**: As a Data Architect, I need the agent to create the Datasphere connection and configure the Replication Flow for an S/4HANA source so that integration is completed in minutes, not days.
- **Acceptance Criteria**:
  - Given S/4HANA system credentials provided by the user, when the agent calls the Connections API, then a connection is created (after user approval) and confirmed.
  - Given a confirmed connection, when the user specifies the tables or CDS views to replicate, then the agent configures and triggers the Replication Flow via the Pipeline Engine API (after user approval).
- **Maps to Objective**: Objective 1, Objective 3
- **Priority Rank**: 2

**REQ-03**: Non-SAP Source Integration

- **Problem to Solve**: Each non-SAP source (Databricks, Salesforce, Snowflake, REST APIs, Azure Data Lake) requires bespoke ingestion logic with no reusable framework.
- **User Story**: As a Data Architect, I need the agent to analyse the non-SAP source's technical capabilities (provided as documentation) and generate the required integration code so that I do not need to write boilerplate ingestion logic from scratch.
- **Acceptance Criteria**:
  - Given technical documentation for a non-SAP source, when the agent analyses it, then it proposes an integration approach (e.g., Databricks notebook, parquet push to HDL) with code for user review.
  - Given user approval, the agent records the approved configuration; execution of code in the external system is the user's responsibility.
  - Agent supports at minimum: Databricks, Salesforce, Snowflake, generic REST API, and Azure Data Lake.
- **Maps to Objective**: Objective 1, Objective 3
- **Priority Rank**: 3

**REQ-04**: Data Product Activation and Creation

- **Problem to Solve**: There is no unified flow for activating SAP-managed Data Products or defining and publishing custom ones.
- **User Story**: As a Data Architect, I need the agent to either activate the appropriate SAP-managed Data Product or guide me through defining a custom Data Product so that data is available for analytics consumption quickly.
- **Acceptance Criteria**:
  - Given integrated data, the agent checks the catalog for a matching SAP-managed Data Product and proposes activation if found.
  - If no SAP-managed Data Product matches, the agent generates a custom Data Product definition and publishes it via the Catalog API (after user approval).
  - Published Data Products are discoverable in the BDC catalog within 5 minutes.
- **Maps to Objective**: Objective 1, Objective 2
- **Priority Rank**: 4

**REQ-05**: Data Quality Validation

- **Problem to Solve**: Data quality issues in newly integrated data are discovered late, after Data Products have been consumed, leading to costly remediation.
- **User Story**: As a Data Steward, I need the agent to run data profiling and apply quality rules on new Data Products so that issues are identified and surfaced before consumption.
- **Acceptance Criteria**:
  - Given a newly created or activated Data Product, the agent triggers profiling via the Data Profiling API.
  - Profiling results are presented with issue highlights and remediation recommendations.
  - Quality validation completes within 24 hours of Data Product creation.
- **Maps to Objective**: Objective 1, Objective 4
- **Priority Rank**: 5

**REQ-06**: Duplicate and Similarity Detection

- **Problem to Solve**: Multiple teams independently create Data Products covering the same business entities, leading to inconsistency and wasted effort.
- **User Story**: As a Data Steward, I need the agent to detect semantically similar Data Products in the catalog before a new one is created so that duplication is prevented.
- **Acceptance Criteria**:
  - Before creating any new Data Product, the agent retrieves catalog metadata and applies semantic similarity analysis.
  - If a similar Data Product is found (similarity score ≥ 0.8), the agent alerts the user and recommends reuse or consolidation before proceeding.
  - Similarity check completes in under 30 seconds.
- **Maps to Objective**: Objective 2
- **Priority Rank**: 6

**REQ-07**: Governance Configuration

- **Problem to Solve**: Data Product governance (ownership, lineage, access policies) is configured inconsistently and often after publication, leaving Data Products ungoverned.
- **User Story**: As a Data Steward, I need the agent to configure governance policies for each Data Product as part of the creation workflow so that every published Data Product has defined ownership and access controls.
- **Acceptance Criteria**:
  - As part of the Data Product creation flow, the agent prompts for ownership and access policy inputs.
  - The agent applies governance configuration via the Enterprise Information Management and Data Sharing Cockpit APIs (after user approval).
  - Lineage metadata is set automatically from integration provenance.
- **Maps to Objective**: Objective 1, Objective 4
- **Priority Rank**: 7

**REQ-08**: Analytical Model Creation

- **Problem to Solve**: Creating Analytical Models in Datasphere for newly created Data Products is a separate manual step that delays analytics consumption.
- **User Story**: As a Data Architect, I need the agent to create a basic Analytical Model for a newly published Data Product so that it is immediately consumable in SAP Analytics Cloud.
- **Acceptance Criteria**:
  - Given a published Data Product, the agent proposes an Analytical Model structure via the Consumption API (after user approval).
  - The created model is accessible in SAP Analytics Cloud within 10 minutes.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 8

**REQ-09**: Continuous Lifecycle Monitoring

- **Problem to Solve**: There is no automated monitoring of Data Product usage, quality degradation, or governance drift after publication.
- **User Story**: As a Data Steward, I need the agent to continuously monitor usage metrics and data quality and surface recommendations so that Data Products remain fit-for-purpose over time.
- **Acceptance Criteria**:
  - The agent periodically queries the Data Maturity Assessment and Consumption APIs and generates monitoring summaries.
  - Usage anomalies (e.g., zero consumption for >30 days) and quality degradation (e.g., completeness drop >10%) trigger proactive alerts.
  - Recommendations are expressed in plain language with proposed remediation actions.
- **Maps to Objective**: Objective 4
- **Priority Rank**: 9

**REQ-10**: Configurable Human-in-the-Loop Approval

- **Problem to Solve**: Different action categories carry different risk levels; a single approval policy does not fit all.
- **User Story**: As an IT Governance Manager, I need to configure which agent actions require human approval and which can run autonomously so that governance controls match business risk tolerance.
- **Acceptance Criteria**:
  - Action categories (connection creation, replication flow config, Data Product publication, governance changes, code generation, monitoring queries) each have a configurable approval mode: `autonomous`, `supervised`, or `always-approve`.
  - The active configuration is persisted and displayed to the user at agent startup.
  - Any action in `supervised` or `always-approve` mode presents a structured approval request with action description, target system, and expected side effects before execution.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 10

---

## Solution Architecture

**Architecture Overview:**  
A pro-code Python AI agent built on the A2A protocol and deployed on SAP BTP (Cloud Foundry or Kyma). The agent uses SAP AI Core (via SAP Generative AI Hub) for LLM-powered reasoning, semantic similarity, and code generation. It invokes SAP Datasphere APIs as its primary tool suite via MCP tool wrappers. A lightweight BTP-hosted configuration service stores approval mode settings per action category.

**Key Components:**

- **Agent Core (Python / A2A)**: Orchestrates lifecycle workflows, manages state across multi-step conversations, and routes decisions to the LLM.
- **SAP AI Core / Generative AI Hub**: Provides LLM capabilities for natural language understanding, semantic similarity scoring, integration code generation, and recommendation synthesis.
- **Datasphere API Tool Suite (MCP)**: Wraps all Datasphere REST/OData APIs (Catalog, Connections, Replication, Pipeline Engine, Data Profiling, Metadata Management, Enterprise Information Management, Data Sharing Cockpit, Consumption, Data Maturity Assessment) as agent-callable tools.
- **Approval Gateway**: Intercepts actions whose category is configured as `supervised` or `always-approve`; presents structured approval requests to the user and blocks execution until confirmed.
- **Configuration Service (BTP)**: Persists per-action-category approval mode settings; accessible via agent and by IT Governance Managers.
- **OpenTelemetry Instrumentation**: Emits structured spans and milestone logs for all agent actions and business steps.

**Integration Points:**

- **SAP Datasphere / BDC**: Primary system of record; all Data Product lifecycle operations performed via REST/OData APIs.
- **SAP S/4HANA**: Source system for SAP-native Data Products; connected via Datasphere Connections + Replication Flow APIs.
- **Non-SAP Sources (Databricks, Salesforce, Snowflake, REST APIs, Azure Data Lake)**: Agent analyses source documentation and generates ingestion code; execution in external systems is user-managed.
- **SAP Analytics Cloud**: Consumer of Analytical Models created by the agent; integration is read-only from agent perspective.

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The agent is designed with a modular tool registry: new Datasphere API tools or third-party source connectors can be registered without modifying core agent logic.
- Source-type handlers (SAP, Databricks, Salesforce, Snowflake, REST, ADLS) are implemented as pluggable strategy classes; new source types are added by implementing the `SourceIntegrationStrategy` interface.
- The approval gateway is extensible: new action categories and custom approval workflows (e.g., multi-level approval) can be registered without core changes.
- Business domain context (Finance, Procurement, etc.) is injectable as agent configuration to enable domain-specific terminology and validation rules.

**Business Step Instrumentation:**
- All six business milestone steps emit structured OpenTelemetry spans and log statements.
- Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`
- Every tool invocation emits a child span with action category, target API, approval mode, and outcome.
- Reasoning traces (LLM prompts and responses) are logged at DEBUG level with PII masking.

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent with configurable human-in-the-loop gates (Hybrid)

**Actions the system performs without human approval (when configured as `autonomous`):**
- Catalog scan and Data Product discovery queries
- Semantic similarity analysis on catalog metadata
- Data profiling execution and results retrieval
- Usage and maturity monitoring queries
- Generating integration code proposals (code is generated but not deployed)

**Actions that require human review or approval (default `supervised` or `always-approve`):**
- Creating connections to source systems in Datasphere
- Configuring and triggering Replication Flows
- Publishing or activating Data Products in the BDC catalog
- Applying governance policies (ownership, access, lineage)
- Creating Analytical Models
- Any write or delete operation against Datasphere APIs

**Model used:** LLM via SAP Generative AI Hub (GPT-4o or equivalent model available on tenant)

**Knowledge & data sources accessed:**
- SAP Datasphere Catalog API: Data Product metadata and catalog entries
- SAP Datasphere Metadata Management API: schema, lineage, and technical metadata
- SAP Datasphere Data Maturity Assessment API: quality scores and maturity metrics
- SAP Datasphere Consumption API: usage statistics and analytical model registry
- User-provided technical documentation for non-SAP sources (uploaded per session)

**Tools or connectors invoked:**

| Tool | API | Side Effect |
|---|---|---|
| `catalog_search` | Datasphere Catalog (OData/REST) | Read-only |
| `catalog_publish_dp` | Datasphere Catalog (REST) | Write — creates/updates Data Product |
| `create_connection` | Datasphere Connections (REST) | Write — creates system connection |
| `configure_replication_flow` | Datasphere Replication + Pipeline Engine (REST) | Write — creates/triggers flow |
| `run_data_profiling` | Datasphere Data Profiling (REST) | Write — triggers profiling job |
| `get_profiling_results` | Datasphere Data Profiling (REST) | Read-only |
| `configure_governance` | Datasphere EIM + Data Sharing Cockpit (REST) | Write — sets policies |
| `create_analytical_model` | Datasphere Consumption (OData/REST) | Write — creates model |
| `get_maturity_metrics` | Datasphere Data Maturity Assessment (REST) | Read-only |
| `get_usage_stats` | Datasphere Consumption (REST) | Read-only |
| `manage_metadata` | Datasphere Metadata Management (REST) | Read/Write — lineage, tags |

**Guardrails & fail-safes:**
- No Datasphere write operation executes without passing through the approval gateway first (unless explicitly configured as `autonomous` by an IT Governance Manager).
- Generated code for non-SAP sources is presented as a text artifact only; the agent never directly deploys code into external systems (Databricks, Salesforce, etc.).
- If the LLM returns a tool call with a destructive or irreversible action category, the agent downgrades it to `always-approve` regardless of current configuration.
- If any Datasphere API call returns a 4xx or 5xx error, the agent halts the current lifecycle step, explains the error in plain language, and asks the user how to proceed.
- Similarity check must complete before any new Data Product creation proceeds; a failed similarity check blocks creation.

---

## Non-Functional Requirements

### Performance
- **Latency**: Agent responses to conversational queries ≤ 5 seconds (p95). Datasphere API calls ≤ 10 seconds per tool invocation.
- **Throughput**: Supports concurrent lifecycle sessions for up to 20 simultaneous users per BTP tenant.

### Reliability
- **Availability**: 99.5% uptime aligned with SAP BTP Cloud Foundry SLA.
- **Fallback**: If SAP AI Core is unavailable, the agent degrades gracefully — tool calls still execute, but LLM-generated recommendations and code generation are disabled with a user-visible notice.

### Explainability
- **Traceability**: Every agent recommendation includes the API endpoint, query parameters, and LLM reasoning excerpt that produced it.
- **Decision Logging**: All approval requests and user decisions are logged with timestamp, action category, user identity, and outcome.
- **Uncertainty Communication**: When the LLM similarity score falls between 0.6 and 0.8, the agent flags the result as "uncertain match" and recommends manual review rather than blocking.

---

## Governance, Risk & Compliance

**Data Handling:**
- Agent does not store raw business data; only metadata, configuration, and structured logs are persisted.
- All API calls to Datasphere are authenticated via OAuth 2.0 using the calling user's BTP identity.
- PII detected in profiling results or user-provided documentation is masked in logs.

**Compliance Frameworks:**
- Inherits data privacy and access governance from SAP Privacy Governance and SAP Cloud Identity Access Governance — the agent does not replace these controls.
- All governance actions are logged for audit trail compliance.

**Approval Flows:**
- IT Governance Managers configure per-category approval modes via the Configuration Service.
- Any change to approval configuration requires IT Governance Manager role; changes are logged.

---

## Milestones

### M1: Data Landscape Discovery

- **Description**: Agent has scanned the BDC catalog and identified available SAP-managed Data Products and existing integrations relevant to the user's domain query.
- **Achieved when**: Catalog scan completes and at least one result (Data Product or integration) is returned to the user.
- **Log on achievement**: `M1.achieved: catalog scan completed; <N> SAP-managed Data Products identified for domain <domain>`
- **Log on miss**: `M1.missed: catalog scan did not complete; reason: <error_message>`

### M2: Integration Configured

- **Description**: Connection to source system created in Datasphere and Replication Flow configured (SAP) or integration code generated and presented (non-SAP), pending or receiving user approval.
- **Achieved when**: Connection API returns 201 Created (SAP) or generated code artifact is presented to user (non-SAP), and user approval decision is recorded.
- **Log on achievement**: `M2.achieved: integration configured for source <source_system>; approval_mode: <mode>; user_decision: <approved|deferred>`
- **Log on miss**: `M2.missed: integration configuration failed for source <source_system>; reason: <error_message>`

### M3: Data Product Activated or Created

- **Description**: SAP-managed Data Product activated or custom Data Product defined and published to the BDC catalog.
- **Achieved when**: Catalog API returns success for activation or custom Data Product publication, and the Data Product is discoverable in the catalog.
- **Log on achievement**: `M3.achieved: Data Product <dp_name> activated/created; type: <sap-managed|custom>; catalog_id: <id>`
- **Log on miss**: `M3.missed: Data Product activation/creation failed for <dp_name>; reason: <error_message>`

### M4: Data Quality Validated

- **Description**: Data profiling job completed for the Data Product; quality results reviewed and any issues flagged to the user.
- **Achieved when**: Data Profiling API returns completed profiling results and summary is presented to the user.
- **Log on achievement**: `M4.achieved: data quality validated for <dp_name>; completeness: <pct>%; issues_found: <N>`
- **Log on miss**: `M4.missed: data quality validation did not complete for <dp_name>; reason: <error_message>`

### M5: Governance and Modeling Complete

- **Description**: Analytical Model created, governance policies applied (ownership, lineage, access), and the Data Product is marked as consumption-ready.
- **Achieved when**: Consumption API confirms Analytical Model creation and EIM/Data Sharing Cockpit APIs confirm governance policy application.
- **Log on achievement**: `M5.achieved: governance and modeling complete for <dp_name>; analytical_model_id: <id>; governance_status: configured`
- **Log on miss**: `M5.missed: governance or modeling step failed for <dp_name>; reason: <error_message>`

### M6: Lifecycle Monitored

- **Description**: Usage metrics, data quality trends, and duplicate/similarity alerts are being continuously tracked and improvement recommendations have been surfaced.
- **Achieved when**: At least one monitoring cycle completes successfully and a monitoring summary (usage stats + maturity score) is delivered to the user.
- **Log on achievement**: `M6.achieved: monitoring cycle completed for <dp_name>; usage_score: <score>; maturity_score: <score>; recommendations: <N>`
- **Log on miss**: `M6.missed: monitoring cycle failed for <dp_name>; reason: <error_message>`

---

## Risks, Assumptions, and Dependencies

### Risks

- **Non-SAP integration code quality**: Generated ingestion code for Databricks, Salesforce, Snowflake, REST APIs, or ADLS may contain errors when source documentation is ambiguous or incomplete. Mitigation: code is always presented for user review; never executed autonomously.
- **Datasphere API coverage gaps**: Full creation of complex Analytical Models via API may not be supported for all model types; edge cases may require manual Datasphere UI steps. Mitigation: agent falls back to guided instructions when API-based creation is not possible.
- **LLM semantic similarity accuracy**: Similarity detection depends on embedding quality; false negatives (missed duplicates) are possible. Mitigation: detection threshold is configurable; users are encouraged to review borderline matches manually.
- **Approval fatigue**: Over-application of the `supervised` mode may slow adoption. Mitigation: default configuration pre-classifies low-risk actions as `autonomous`.

### Assumptions

- The customer's BTP tenant has SAP AI Core and Generative AI Hub enabled with an LLM model deployed.
- SAP Datasphere REST/OData APIs are accessible from BTP via service binding or API key authentication.
- Users have appropriate Datasphere roles to perform the actions the agent proposes (connection admin, Data Product publisher, governance admin).
- Non-SAP source documentation (API specs, schemas) provided by users is accurate and current.

### Dependencies

- SAP Datasphere API availability and stability (Catalog, Connections, Replication, Pipeline Engine, Data Profiling, Metadata Management, EIM, Data Sharing Cockpit, Consumption, Data Maturity Assessment).
- SAP AI Core / Generative AI Hub for LLM inference.
- SAP BTP Cloud Foundry or Kyma runtime for agent deployment.
- SAP Cloud Identity Services for user authentication and role-based access control.

---

## References

- SAP Business Data Cloud product documentation
- SAP Datasphere REST API reference
- SAP AI Core / Generative AI Hub documentation
- SAP BTP A2A Agent development guidelines
- SAP Privacy Governance and SAP Cloud Identity Access Governance product pages
