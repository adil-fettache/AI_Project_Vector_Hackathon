# Autonomous Data Product Lifecycle Agent for SAP Business Data Cloud

An autonomous AI agent that manages the end-to-end lifecycle of Data Products across SAP Business Data Cloud (BDC), orchestrating landscape discovery, SAP-managed and custom Data Product activation, non-SAP integration via Databricks, Datasphere modeling, data quality enforcement, governance, monitoring, and SAP Analytics Cloud consumption — all through natural language.

## Business challenge

Organizations running SAP Business Data Cloud face a fragmented, manual, and expert-dependent process for managing Data Product lifecycles. Data Engineers, Data Product Owners, Data Stewards, and Business Analysts must navigate multiple systems — Datasphere, HDL, Databricks, SAP BDC catalog, SAP Analytics Cloud — to discover, activate, create, connect, validate, and monitor Data Products. There is no unified, intelligent orchestration layer that can:

- Discover the full BDC landscape (spaces, connections, existing products, Databricks workspaces)
- Activate SAP-managed Data Products (e.g. S/4HANA Finance, SuccessFactors, Ariba) with human-in-the-loop confirmation for deployment steps
- Integrate non-SAP systems generically (any system with REST API or JDBC capabilities) by retrieving technical documentation and integration capabilities, with Jira (REST) and PostgreSQL (JDBC) as reference implementations
- Create custom Data Products from scratch (SQL Views, Graphical Views, Transformation Flows, Analytic Models) in Datasphere
- Define, enforce, and continuously monitor data quality rules (completeness, freshness, referential integrity) — blocking deployment on critical violations
- Manage governance and metadata across the BDC catalog
- Surface insights and consume Data Products in SAP Analytics Cloud

## Key Milestones

1. **Landscape Discovered** — Agent has successfully mapped the BDC environment: all Datasphere spaces, active connections, existing Data Products (SAP-managed and custom), and Databricks workspaces
2. **Data Product Identified / Proposed** — Agent has identified the target SAP-managed Data Product or designed the structure for a custom Data Product based on user intent; user has confirmed the proposal
3. **Source Connected** — Required source system connection is validated and active (SAP source activated via BDC, or non-SAP source integrated via Databricks with retrieved documentation and JDBC/REST credentials confirmed)
4. **Data Product Deployed** — Data Product is live in Datasphere: artifacts created (views, flows, models), data quality rules applied, all critical quality checks passed
5. **Monitoring Active & Insight Delivered** — Continuous quality monitoring is running, alerts are configured, and Data Product is accessible for consumption in SAP Analytics Cloud

## Business Architecture (RBA)

### End-to-End Process

Governance (with cross-cutting to Idea to Release for Software and Plan to Fulfill)

### Process Hierarchy

```
Governance (E2E)
└── Manage Information Technology (generic)
    └── Manage IT governance (generic) [BPS-456]
        └── Operate IT Governance Framework
└── Manage Governance, Risk and Compliance (generic)
    └── Manage cybersecurity, data protection and privacy (generic) [BPS-400]
        └── Manage data privacy
        └── Manage data protection
    └── Manage identity and access governance (generic) [BPS-399]
        └── Manage access governance and authorisations
Idea to Release for Software (variant)
└── Solution lifecycle & compliance
    └── SAP and non-SAP system integration
    └── Custom data product development
Plan to Fulfill (cross-cutting)
└── Quality improvement
    └── Data quality rule definition and enforcement
```

### Summary

The challenge maps primarily to the IT Governance sub-process (BPS-456) for lifecycle orchestration and compliance, with cross-cutting coverage of data privacy/protection (BPS-400), identity governance (BPS-399), the "Idea to Release for Software" industry variant for custom Data Product development and SAP/non-SAP integration, and Plan to Fulfill quality sub-processes for data quality enforcement.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Gap? | Notes / assumptions |
|---|---|---|---|---|---|---|
| Discover BDC landscape (spaces, connections, Data Products) | SAP Datasphere – Catalog (OData), Connections (REST), Tasks (REST) | Catalog (EDMX + OpenAPI), Connections (OpenAPI), Tasks (OpenAPI) | None found — MCP servers must be generated | — | Yes | Custom MCP servers needed for Catalog, Connections, Tasks APIs |
| Activate SAP-managed Data Products (S/4HANA, SuccessFactors, Ariba) | SAP Business Data Cloud – Data Products API (REST) | `sap.clm:apiResource:DataProducts:v1` | None found | — | Yes | Custom MCP server needed; human-in-the-loop confirmation for deployment steps |
| Integrate non-SAP systems generically (REST/JDBC) | Databricks (external); SAP Connections API for registration | Connections (OpenAPI) | None found | — | Yes | Agent retrieves integration docs autonomously; Jira (REST) + PostgreSQL (JDBC) as demos |
| Create custom Data Products (SQL Views, Graphical Views, Transformation Flows, Analytic Models) | SAP Datasphere – Tasks (REST), Catalog (OData) | Tasks (OpenAPI), Catalog (EDMX + OpenAPI) | None found | — | Yes | Agent generates artifact definitions and deploys via Tasks + Catalog APIs |
| Data quality — define rules, enforce, monitor continuously, block on critical violations | SAP Data Quality Management microservices (REST); Datasphere monitoring | DQM (OpenAPI), Monitoring Query (REST) | None found | — | Yes | Quality gate logic built into agent; Monitoring Query API for continuous checks |
| Governance and metadata management | Metadata Management Cloud Edition (REST); Enterprise Information Management (REST) | Both OpenAPI | None found | — | Yes | Agent writes/reads metadata; custom MCP server needed |
| Monitor Data Product health and lifecycle | Monitoring Query Cloud Edition (REST) | Monitoring Query (OpenAPI) | None found | — | Yes | Custom MCP server needed |
| Consume Data Products in SAP Analytics Cloud | SAP Analytics Cloud (separate platform) | SAC API (not discovered in BDC scope) | None found | — | Yes | SAC integration layer needed; agent pushes models/stories to SAC via SAC REST API |
| Data sharing and replication management | Packaging Data Replication (REST), Data Sharing Cockpit (REST) | Both OpenAPI | None found | — | Partial | Replication Flows excluded from Datasphere API scope (wrong spec); Packaging Replication usable |
| Certificates and secure connectivity | Certificates (REST) | Certificates (OpenAPI) | None found | — | Maybe | Required for secure JDBC/HTTPS connections to non-SAP systems |

### Key findings

- No MCP servers exist for any of the discovered APIs — all BDC/Datasphere APIs require custom MCP server generation from the provided OpenAPI/EDMX specs
- The Data Products API (`sap.clm:apiResource:DataProducts:v1`) is the primary entry point for SAP-managed Data Product activation; it has an ORD ID but no MCP server
- Non-SAP integration is generic by design: the agent's pattern is to retrieve system documentation and integration capabilities dynamically, then register the connection via the Connections API; Jira (REST) and PostgreSQL (JDBC) are reference demos only
- SAC integration requires the SAP Analytics Cloud REST API — not part of the BDC APIs discovered; must be added as a separate MCP server
- Data quality enforcement requires both the DQM microservices API and the Monitoring Query API working in concert with the agent's quality gate logic
- Human-in-the-loop is required for all deployment/activation decisions; the agent operates autonomously only for read and discovery operations

## Recommendations

### Autonomous Data Product Lifecycle Agent — SAP Business Data Cloud

#### Executive Summary

AI agent with MCP tool layer over BDC/Datasphere APIs + SAC, enforcing a human-in-the-loop gate at every deployment step

#### Recommended Solution

A pro-code Python AI Agent (A2A protocol) with a full MCP tool layer covering: SAP Business Data Cloud Data Products API, Datasphere Catalog, Connections, Tasks, Monitoring Query, Metadata Management, DQM microservices, Data Sharing Cockpit, and SAP Analytics Cloud REST API. The agent implements five key capability groups: (1) Landscape Discovery, (2) SAP-managed Data Product Activation, (3) Non-SAP Integration via Databricks (generic pattern, Jira + PostgreSQL as demos), (4) Custom Data Product Creation in Datasphere, (5) Data Quality Governance + Monitoring, with SAC consumption as the delivery layer. Human-in-the-loop confirmation gates are enforced before any deployment or activation action.

#### Problem Statement

Data platform teams must manually orchestrate across 8+ APIs and UI systems to bring a single Data Product to life in SAP Business Data Cloud. There is no intelligent layer that can discover the landscape, propose the right activation path, enforce quality, and surface results in SAC — all from a natural language request.

#### Affected User Roles

- Data Engineers / Data Platform Teams
- Data Product Owners / Data Stewards
- Business Analysts

#### Important factors

##### Reduces expert dependency through autonomous orchestration

The agent eliminates the need for deep API knowledge across Datasphere, BDC, Databricks, and SAC — any user can trigger a full Data Product lifecycle through natural language.

##### Generic non-SAP integration pattern future-proofs the solution

By dynamically retrieving integration documentation for any REST/JDBC-capable system, the agent is not limited to Jira or PostgreSQL — it can onboard any non-SAP system without code changes.

##### Human-in-the-loop gates prevent unintended production changes

All destructive or deployment-class actions (activation, replication start, model deployment to SAC) require explicit user confirmation, reducing operational risk.

##### Data quality as a first-class deployment gate

Quality rules are defined, monitored continuously, and enforced as a hard gate — Data Products with critical violations cannot be deployed, protecting downstream consumers.

#### Potential risks

##### API coverage gaps

Several BDC APIs have no ORD IDs and no pre-built MCP servers — all MCP translation files must be generated from raw OpenAPI specs; spec quality may vary.

##### Databricks non-SAP integration complexity

Generic integration requires the agent to autonomously interpret third-party API documentation — LLM accuracy on unfamiliar API specs may vary; human review of generated connection specs is recommended.

##### SAC integration scope

SAP Analytics Cloud has a separate REST API surface that is not part of the BDC API discovery; this must be sourced and implemented as an additional MCP server.

#### Recommended solution category

AI Agent

#### Intent fit
92%
