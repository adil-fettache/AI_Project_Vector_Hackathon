# Specification

> **Guidelines**: Read [guidelines.md](./guidelines.md) before executing ANY tasks below.

Check off items as completed.

## Solution Setup

- [x] Invoke `setup-solution` skill to register `bdc-data-lifecycle-agent` as a new asset in `solution.yaml` with an `asset.yaml`
- [x] Validate `assets/bdc-data-lifecycle-agent/asset.yaml` and `solution.yaml` exist and are well-formed
- [x] Confirm existing MCP server assets are still registered in `solution.yaml`:
  - `catalog-datasphere-mcp-server`
  - `connections-datasphere-mcp-server`
  - `tasks-datasphere-mcp-server`

## Asset Implementation

- [x] Execute `specification/bdc-data-lifecycle-agent/specification.md` (all items)

## API Discovery Results

The following APIs were discovered for this solution. All require custom MCP server generation from their respective OpenAPI/EDMX specs. Re-run `sap_knowledge_graph_api_discovery` at implementation time to get fresh pre-signed download URLs.

| API Name | Type | ORD ID | Target MCP Server |
|---|---|---|---|
| Data Products | REST/OpenAPI | `sap.clm:apiResource:DataProducts:v1` | `bdc-data-products-mcp-server` |
| Catalog | OData/EDMX | — | `catalog-datasphere-mcp-server` (existing) |
| Connections | REST/OpenAPI | — | `connections-datasphere-mcp-server` (existing) |
| Tasks | REST/OpenAPI | — | `tasks-datasphere-mcp-server` (existing) |
| Monitoring | REST/OpenAPI | — | `monitoring-datasphere-mcp-server` (new) |
| Monitoring Query (Cloud Edition) | REST/OpenAPI | — | `monitoring-datasphere-mcp-server` (new, combined) |
| Metadata Management (Cloud Edition) | REST/OpenAPI | — | `metadata-management-mcp-server` (new) |
| SAP Data Quality Management microservices | REST/OpenAPI | — | `dqm-mcp-server` (new) |
| Certificates | REST/OpenAPI | — | `certificates-datasphere-mcp-server` (new) |
| SAP Analytics Cloud Activities Service | REST/OpenAPI | — | `sac-mcp-server` (new) |

## Cross-Implementation Notes

- The `bdc-data-lifecycle-agent` re-uses `catalog-datasphere-mcp-server`, `connections-datasphere-mcp-server`, and `tasks-datasphere-mcp-server` that were built for `datasphere-management-agent`. Verify their ORD IDs are correct before wiring them into `bdc-data-lifecycle-agent/asset.yaml`.
- Both agents coexist in the same solution — no naming conflicts because asset names are unique.
- All 9 MCP servers required by `bdc-data-lifecycle-agent` must appear in `solution.yaml` before deployment.
