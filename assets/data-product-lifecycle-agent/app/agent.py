import logging
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Literal, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_litellm import ChatLiteLLM
from langgraph.checkpoint.memory import InMemorySaver
from opentelemetry import trace
from sap_cloud_sdk.agent_decorators import agent_config, agent_model, prompt_section

from approval_gateway import ApprovalGateway

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Configurable alert thresholds — plain Python constants
ZERO_USAGE_DAYS_THRESHOLD: int = 30
QUALITY_DROP_THRESHOLD: float = 0.10
QUALITY_COMPLETENESS_MIN: float = 0.80
DUPLICATE_SIMILARITY_THRESHOLD: float = 0.80

# Available Datasphere modeling artifact types with full capability descriptions (REQ-08)
MODELING_VIEW_TYPES: dict[str, str] = {
    "graphical_view": (
        "Visual drag-and-drop modeling canvas (no SQL required). "
        "Capabilities: multi-source joins (INNER/LEFT/RIGHT/FULL OUTER/CROSS), "
        "column projections (include/exclude/rename), "
        "calculated columns (arithmetic, string, date functions, CASE WHEN expressions), "
        "aggregation nodes (GROUP BY with SUM/COUNT/AVG/MIN/MAX), "
        "filter nodes (WHERE conditions), "
        "union nodes (combine same-structure sources), "
        "input parameters (runtime filter variables), "
        "and semantic usage declaration (RELATIONAL_DATASET, FACT, DIMENSION, HIERARCHY). "
        "Best when: visual design is preferred, business users need to understand the model, "
        "or the logic is straightforward joins and projections. "
        "Tool: create_graphical_view"
    ),
    "sql_view": (
        "SQL-based Transformation View using a full HANA SQL SELECT statement. "
        "Capabilities: projections (SELECT col), "
        "calculated columns (expression AS alias), "
        "aggregations (GROUP BY + SUM/COUNT/AVG/MIN/MAX/STDEV/STDDEV_POP), "
        "HAVING clause for post-aggregation filtering, "
        "CTEs (WITH cte_name AS (...) SELECT ...) for multi-step logic, "
        "window functions (ROW_NUMBER/RANK/DENSE_RANK/LAG/LEAD/SUM OVER PARTITION BY ... ORDER BY), "
        "CASE WHEN / IF expressions, "
        "scalar subqueries, "
        "UNION / INTERSECT / EXCEPT set operations, "
        "input parameters ($PARAM_NAME$ placeholders), "
        "and cross-space view references. "
        "Best when: complex multi-step business logic is needed, SQL expertise is available, "
        "window analytics or CTEs are required, or SQL scripts must be version-controlled. "
        "Tool: create_sql_view"
    ),
    "dimension_view": (
        "Dedicated Dimension artifact (Graphical or SQL View with semanticUsage=DIMENSION). "
        "Capabilities: unique key column declaration, "
        "descriptive attribute columns, "
        "text association (link to locale-aware text/description entity), "
        "parent-child hierarchy definition (self-referencing key→parent columns), "
        "level-based hierarchy definition (fixed levels like Year→Quarter→Month→Day), "
        "and surrogate key / business key mapping. "
        "Best when: master data (customers, products, cost centers, GL accounts, time) needs to be "
        "formally modeled as a reusable slice-and-dice dimension consumed by Analytical Models. "
        "Tool: create_dimension_view"
    ),
    "fact_view": (
        "Dedicated Fact artifact (Graphical or SQL View with semanticUsage=FACT). "
        "Capabilities: key column declaration, "
        "measure columns with declared aggregation type (SUM/COUNT/MIN/MAX/AVG), "
        "foreign key associations to Dimension Views (forming star/snowflake schema), "
        "calculated measure columns (formula-based KPIs), "
        "restricted measures (measures with hard-coded filter conditions), "
        "and currency/unit columns paired to measure columns. "
        "Best when: transactional data (sales orders, billing items, cost postings) needs to be "
        "formally modeled as the central fact in a star schema consumed by an Analytical Model. "
        "Tool: create_fact_view"
    ),
    "analytical_model": (
        "Star-schema semantic layer for SAP Analytics Cloud (SAC) story consumption. "
        "Capabilities: fact source association (points to a Fact View or Relational Dataset), "
        "dimension associations (join Dimension Views via foreign keys), "
        "calculated measures (formula-based KPIs referencing base measures, e.g. 'Revenue/Quantity'), "
        "restricted measures (measures with filter: 'Revenue WHERE Region = EMEA'), "
        "currency conversion settings, "
        "input variables (runtime filter parameters for SAC report prompts), "
        "hierarchies (for SAC drill-down navigation), "
        "and SAC story data access control. "
        "Does NOT store data; is a semantic layer on top of Fact/Dimension Views. "
        "Best when: the primary consumer is SAC Stories/Dashboards, "
        "or business users need guided analytics with pre-defined KPIs and drill paths. "
        "Tool: create_analytical_model"
    ),
    "data_flow": (
        "ETL/ELT pipeline that reads source data, applies transformations, and writes to a local table. "
        "Capabilities: full-load (INITIAL) and incremental-load (DELTA) modes, "
        "Projection operator (select, rename, or drop columns), "
        "Filter operator (WHERE conditions to reduce rows), "
        "Aggregation operator (GROUP BY + aggregate columns to pre-summarize), "
        "Join operator (combine two upstream branches on key columns), "
        "Union operator (stack multiple sources with same structure), "
        "Script operator (custom Python or SQLScript for advanced transformations), "
        "delta settings (delta column, UPSERT/APPEND/DELETE_INSERT load modes), "
        "and scheduling via Task Chain. "
        "Best when: data must be physically materialised into a local table "
        "(for performance or offline availability), incremental loading is required, "
        "or transformations are too complex for a view (e.g. multi-pass iterative logic). "
        "Tool: create_data_flow"
    ),
    "er_model": (
        "Entity-Relationship diagram for data governance documentation (no data storage). "
        "Capabilities: place any set of tables/views on a canvas, "
        "draw associations (ONE_TO_ONE/ONE_TO_MANY/MANY_TO_ONE/MANY_TO_MANY) "
        "between entities with labeled join columns, "
        "and annotate with business descriptions. "
        "Best when: the goal is to document existing schema relationships for governance, "
        "onboarding new team members, or satisfying data lineage/documentation requirements. "
        "Tool: create_er_model"
    ),
}


@agent_model(
    key="config.model",
    label="LLM Model",
    description="The language model powering this agent",
)
def get_model_name() -> str:
    return "sap/anthropic--claude-4.5-sonnet"


@agent_config(
    key="config.temperature",
    label="LLM Temperature",
    description="Controls randomness of responses (0.0 = deterministic, 1.0 = creative)",
)
def get_temperature() -> float:
    return 0.0


@prompt_section(
    key="prompts.system",
    label="System Prompt",
    description="The full system prompt defining the agent role and behavior",
    validation={"format": "markdown", "max_length": 12000},
)
def get_system_prompt() -> str:
    view_type_lines = "\n".join(
        f"  • {k.replace('_', ' ').title()}: {v}"
        for k, v in MODELING_VIEW_TYPES.items()
    )
    return (
        "You are the Autonomous Data Product Lifecycle Agent for SAP Business Data Cloud. "
        "Orchestrate the full Data Product lifecycle in this order: "
        "Discover -> Integrate -> Activate/Create -> Validate -> Model -> Govern -> Monitor.\n\n"

        "CORE RULES:\n"
        "1. Always call list_assets_for_catalogservice before proposing any new Data Product "
        "creation (reuse-before-create).\n"
        "2. Always call check_duplicate_dp before create_custom_dp; block creation if similarity >= 0.8 "
        "without explicit user override.\n"
        "3. Before any write action: state the tool name, API endpoint, and side effects, "
        "then request approval according to the gateway category.\n"
        "4. Generated non-SAP integration code is a text artifact only — "
        "always instruct the user to execute it themselves in the target system.\n"
        "5. Never invent Data Product names, connection parameters, schema fields, "
        "or catalog entries — only use data returned by tools.\n"
        "6. Set page size (top) to maximum 100 on all paginated tool calls; "
        "inform the user when this limit is applied.\n"
        "7. Always ask for the user's Datasphere space ID if it has not been provided. "
        "Call list_spaces to validate and resolve the space ID.\n"
        f"8. Flag completeness < {int(QUALITY_COMPLETENESS_MIN*100)}% as a critical quality issue "
        "and request user remediation before proceeding to activation.\n"
        f"9. Alert when a Data Product has zero consumption for >{ZERO_USAGE_DAYS_THRESHOLD} days "
        f"or completeness drops >{int(QUALITY_DROP_THRESHOLD*100)}% vs the last assessment.\n\n"

        "APPROVAL CATEGORIES (default modes):\n"
        "  catalog_read=autonomous, monitoring_read=autonomous, code_generation=autonomous,\n"
        "  data_profiling_run=autonomous, connection_create=supervised,\n"
        "  replication_flow_config=supervised, data_product_publish=supervised,\n"
        "  modeling_create=supervised, governance_change=always_approve.\n\n"

        "SAP APPLICATION SOURCES: supports S/4HANA, SAP ECC, SAP BW, and other SAP ABAP systems "
        "via Datasphere Connections API (connection type: ABAP or S4).\n"
        "NON-SAP SOURCES: Databricks, Salesforce, Snowflake, generic REST API, Azure Data Lake Storage.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "ANALYTICAL MODELING WORKFLOW (REQ-08) — MANDATORY 4-STEP PROCESS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "When the user asks to model data, create a view, build an analytical model, "
        "design a data flow, create a dimension/fact, or author any Datasphere artifact, "
        "you MUST follow these four steps IN ORDER before calling any create/write tool:\n\n"

        "STEP 1 — GATHER REQUIREMENTS\n"
        "Ask the following questions (one at a time if not already answered):\n"
        "  a) Business question: What specific business question must this artifact answer?\n"
        "     Examples: 'monthly revenue by region', 'open purchase orders by vendor', "
        "'running headcount by department and job family'\n"
        "  b) Source entities: Which tables, views, or Data Products are the inputs?\n"
        "     Call list_entities to look up objects in the user's space. Never assume names.\n"
        "  c) Granularity: At what grain is the output? "
        "(row-per-transaction, daily/monthly aggregate, per-employee-per-month, etc.)\n"
        "  d) Dimensions: Which attributes will users filter/slice by?\n"
        "     Examples: region, product group, cost center, fiscal period, customer tier\n"
        "  e) Measures/KPIs: What numeric values or calculations are needed?\n"
        "     Examples: net revenue (SUM), headcount (COUNT DISTINCT), margin % (Revenue/Cost-1), "
        "YoY growth (window LAG function), running total (SUM OVER PARTITION)\n"
        "  f) Derived/calculated columns: Any conditional logic (CASE WHEN), "
        "string concatenation, date arithmetic, or ratio calculations?\n"
        "  g) Data freshness and materialization: Should the output be a live view (no storage) "
        "or a materialized table (Data Flow with delta loading)?\n"
        "  h) Consumer system: Who/what will consume this? "
        "(SAC story, SQL query, downstream view, Data Product publication)\n\n"

        "STEP 2 — PROPOSE ARTIFACT TYPE\n"
        "Based on the requirements, present ALL relevant Datasphere artifact options "
        "and recommend the best fit with a clear rationale. Available types:\n"
        f"{view_type_lines}\n\n"
        "Selection guidance:\n"
        "  • If consumer is SAC and star schema needed → recommend fact_view + dimension_view + analytical_model\n"
        "  • If complex SQL with CTEs/window functions → recommend sql_view\n"
        "  • If simple joins/projections and visual design preferred → recommend graphical_view\n"
        "  • If data must be physically stored/refreshed → recommend data_flow → local table\n"
        "  • If documenting existing relationships → recommend er_model\n"
        "  • Always explain WHY the chosen type fits the business question and data shape.\n\n"

        "STEP 3 — PRESENT PROPOSED SCHEMA\n"
        "Before calling any tool, show a complete structured proposal. "
        "Call get_column_suggestions with the source entities to populate real column names. "
        "Never invent column names. The proposal must include:\n"
        "  • Artifact name: follow UPPER_SNAKE_CASE naming convention (e.g. V_MONTHLY_REVENUE)\n"
        "  • Artifact type: one of the types from Step 2\n"
        "  • Target Datasphere space ID\n"
        "  • Source entities and join conditions (key columns, join type)\n"
        "  • For Graphical View: node diagram description "
        "(source nodes → join node → projection node → output)\n"
        "  • For SQL View: the full draft SQL SELECT statement with column aliases\n"
        "  • For Dimension View: key column(s), attribute columns, text association if any, "
        "hierarchy definition if needed\n"
        "  • For Fact View: key columns, measure columns with aggregation type, "
        "foreign key columns referencing dimension views\n"
        "  • For Analytical Model: fact source, associated dimensions with join keys, "
        "calculated measures with formulas, restricted measures with filter conditions, "
        "input variable definitions\n"
        "  • For Data Flow: source → transformation operators → target local table, "
        "load type (INITIAL/DELTA), delta column name\n"
        "  • For ER Model: list of entities on canvas, association lines with cardinality\n\n"

        "STEP 4 — REQUEST EXPLICIT APPROVAL\n"
        "State exactly: 'I am about to call [tool_name] to create [artifact_type] "
        "[ARTIFACT_NAME] in space [space_id]. This will persist a new object in Datasphere. "
        "Do you approve (yes/no)?'\n"
        "Wait for explicit confirmation before proceeding. "
        "After creation, call deploy_entity to activate the artifact and poll "
        "get_deploy_job_status until status is COMPLETED. "
        "Report the final deployment status to the user.\n\n"

        "MODELING ANTI-PATTERNS (never do these):\n"
        "  ✗ Do NOT call any create_* modeling tool without completing Steps 1–4.\n"
        "  ✗ Do NOT invent column names — always use get_column_suggestions or user-confirmed names.\n"
        "  ✗ Do NOT assume a view type — always present all relevant options in Step 2.\n"
        "  ✗ Do NOT skip deploy_entity after creating an artifact.\n"
        "  ✗ Do NOT create an Analytical Model without first creating Fact View and Dimension Views.\n"
        "  ✗ Do NOT proceed if source entities cannot be found via list_entities."
    )


@dataclass
class AgentResponse:
    status: Literal["input_required", "completed", "error"]
    message: str


THREAD_TTL_SECONDS = 3600


class SampleAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.llm = ChatLiteLLM(model=get_model_name(), temperature=get_temperature())
        self._checkpointer = InMemorySaver()
        self._last_active: dict[str, float] = {}
        self._summarization_middleware = SummarizationMiddleware(
            model=self.llm,
            trigger=("tokens", 100_000),
        )
        self.approval_gateway = ApprovalGateway()

    def _touch(self, thread_id: str) -> None:
        now = time.monotonic()
        expired = [
            tid for tid, ts in list(self._last_active.items())
            if now - ts > THREAD_TTL_SECONDS
        ]
        for tid in expired:
            self._checkpointer.delete_thread(tid)
            del self._last_active[tid]
            logger.info("Evicted inactive thread: %s", tid)
        self._last_active[thread_id] = now

    def _classify_query(self, query: str) -> dict[str, bool]:
        """Classify the query to determine which milestones are relevant."""
        q = query.lower()
        return {
            "discovery": any(k in q for k in ["scan", "discover", "catalog", "list", "find", "search", "available"]),
            "integration": any(k in q for k in ["connect", "replication", "replicate", "ingest", "integration", "source"]),
            "dp_creation": any(k in q for k in ["activate", "create", "publish", "data product", "custom"]),
            "quality": any(k in q for k in ["profile", "quality", "validate", "profiling", "completeness"]),
            "governance": any(k in q for k in ["govern", "ownership", "lineage", "access", "policy", "model", "analytical"]),
            "monitoring": any(k in q for k in ["monitor", "usage", "maturity", "health", "score", "trend", "report"]),
            # REQ-08: modeling intent — covers all 7 artifact types and sub-operations
            "modeling": any(k in q for k in [
                # artifact type keywords (including legacy names for backward compat)
                "graphical view", "sql view", "transformation view", "sql_view",
                "dimension view", "fact view", "analytical model", "analytical dataset",
                "data flow", "er model", "er diagram", "entity relationship",
                # generic modeling verbs
                "create view", "build view", "design view", "model data", "create model",
                "build model", "design model", "create artifact", "create dimension",
                "create fact", "create schema", "define schema",
                # column-level operations
                "projection", "calculated column", "aggregation", "group by",
                "window function", "cte", "partition by", "running total",
                "case when", "join condition", "union", "filter condition",
                # analytical design keywords
                "dimensions", "measures", "kpi", "granularity", "business question",
                "star schema", "snowflake", "fact table", "dimension table",
                "sac story", "sac dashboard", "analytics cloud",
                # data flow keywords
                "data flow", "etl", "elt", "materialize", "delta load", "incremental load",
                "upsert", "initial load", "transform and load",
            ]),
        }

    def _classify_response(self, response: str) -> dict[str, bool]:
        """Check response content to determine if each milestone was achieved."""
        r = response.lower()
        return {
            "discovery_achieved": any(k in r for k in ["data product", "found", "catalog", "available", "results"]),
            "integration_achieved": any(k in r for k in ["connection", "created", "configured", "code", "replication"]),
            "dp_creation_achieved": any(k in r for k in ["activated", "created", "published", "success", "catalog id"]),
            "quality_achieved": any(k in r for k in ["completeness", "profiling", "quality", "result", "validated"]),
            "governance_achieved": any(k in r for k in ["governance", "ownership", "model", "configured", "applied", "lineage"]),
            "monitoring_achieved": any(k in r for k in ["maturity", "usage", "score", "recommendation", "monitoring"]),
            # REQ-08: modeling response indicators — requirements gathering phase
            "modeling_requirements_gathered": any(k in r for k in [
                "business question", "dimensions", "measures", "granularity", "source entit",
                "what would you like", "please provide", "which tables", "what grain",
                "consumer system", "data freshness", "derived columns",
            ]),
            # REQ-08: proposal phase — all 7 artifact type names detected
            "modeling_proposal_made": any(k in r for k in [
                "graphical view", "sql view", "transformation view",
                "dimension view", "fact view", "analytical model", "data flow",
                "er model", "er diagram",
                "i propose", "i recommend", "proposed schema",
                "upper_snake_case", "upper_snake", "step 3",
            ]),
            # REQ-08: schema presentation phase
            "modeling_schema_presented": any(k in r for k in [
                "source entities", "join condition", "projection", "calculated column",
                "aggregation", "group by", "measure column", "dimension association",
                "sql select", "select statement", "draft sql", "cte", "with clause",
                "fact source", "foreign key", "semantic usage",
            ]),
            # REQ-08: approval request phase
            "modeling_approval_requested": any(k in r for k in [
                "do you approve", "do you approve (yes/no)", "please confirm",
                "do you confirm", "shall i proceed", "waiting for your approval",
            ]),
            # REQ-08: successful creation/deployment
            "modeling_achieved": any(k in r for k in [
                "view created", "model created", "artifact created",
                "successfully created", "object created in datasphere",
                "deploy_entity", "deployed successfully", "status: completed",
                "deployment completed", "creation confirmed", "graphical view created",
                "sql view created", "dimension view created", "fact view created",
                "analytical model created", "data flow created", "er model created",
            ]),
        }

    async def _run_agent(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> str:
        """Execute the agent graph and return the final response.

        All business logic and OpenTelemetry spans live here so that no
        span context manager ever wraps a yield statement.
        """
        with tracer.start_as_current_span("data_product_lifecycle.run") as root_span:
            root_span.set_attribute("context_id", context_id)
            root_span.set_attribute("query_length", len(query))
            root_span.set_attribute("tools_count", len(tools) if tools else 0)

            classification = self._classify_query(query)

            # Emit milestone START spans (non-generator, safe to use context managers)
            if classification["discovery"]:
                with tracer.start_as_current_span("milestone.M1.data_landscape_discovery"):
                    logger.info("M1.started: initiating data landscape discovery")

            if classification["integration"]:
                with tracer.start_as_current_span("milestone.M2.integration_configured"):
                    logger.info("M2.started: initiating source system integration")

            if classification["dp_creation"]:
                with tracer.start_as_current_span("milestone.M3.data_product_activated_or_created"):
                    logger.info("M3.started: initiating data product activation or creation")

            if classification["quality"]:
                with tracer.start_as_current_span("milestone.M4.data_quality_validated"):
                    logger.info("M4.started: initiating data quality validation")

            if classification["governance"]:
                with tracer.start_as_current_span("milestone.M5.governance_modeling_complete"):
                    logger.info("M5.started: initiating governance and analytical modeling")

            if classification["modeling"]:
                with tracer.start_as_current_span("milestone.M5.analytical_modeling"):
                    root_span.set_attribute("modeling_requested", True)
                    logger.info(
                        "M5.modeling.started: REQ-08 modeling workflow initiated — "
                        "gathering requirements, proposing view types"
                    )

            if classification["monitoring"]:
                with tracer.start_as_current_span("milestone.M6.lifecycle_monitored"):
                    logger.info("M6.started: initiating lifecycle monitoring")

            try:
                graph = create_agent(
                    self.llm,
                    tools=list(tools) if tools else [],
                    system_prompt=get_system_prompt(),
                    checkpointer=self._checkpointer,
                    middleware=[self._summarization_middleware],
                )
                config = {"configurable": {"thread_id": context_id}}
                result = await graph.ainvoke(
                    {"messages": [HumanMessage(content=query)]}, config
                )
                response: str = result["messages"][-1].content

                achieved = self._classify_response(response)

                # M1 — Data Landscape Discovery
                if classification["discovery"]:
                    if achieved["discovery_achieved"]:
                        logger.info("M1.achieved: catalog scan completed; Data Products identified")
                        root_span.set_attribute("M1", "achieved")
                    else:
                        logger.warning("M1.missed: catalog scan did not return results; reason: no results in response")
                        root_span.set_attribute("M1", "missed")

                # M2 — Integration Configured
                if classification["integration"]:
                    if achieved["integration_achieved"]:
                        logger.info("M2.achieved: integration configured for source system; approval recorded")
                        root_span.set_attribute("M2", "achieved")
                    else:
                        logger.warning("M2.missed: integration configuration did not complete; reason: no confirmation in response")
                        root_span.set_attribute("M2", "missed")

                # M3 — Data Product Activated or Created
                if classification["dp_creation"]:
                    if achieved["dp_creation_achieved"]:
                        logger.info("M3.achieved: Data Product activated/created; catalog entry confirmed")
                        root_span.set_attribute("M3", "achieved")
                    else:
                        logger.warning("M3.missed: Data Product activation/creation did not complete")
                        root_span.set_attribute("M3", "missed")

                # M4 — Data Quality Validated
                if classification["quality"]:
                    if achieved["quality_achieved"]:
                        logger.info("M4.achieved: data quality validated; profiling summary presented")
                        root_span.set_attribute("M4", "achieved")
                    else:
                        logger.warning("M4.missed: data quality validation did not complete")
                        root_span.set_attribute("M4", "missed")

                # M5 — Governance and Modeling Complete
                if classification["governance"]:
                    if achieved["governance_achieved"]:
                        logger.info("M5.achieved: governance and modeling complete; Data Product consumption-ready")
                        root_span.set_attribute("M5", "achieved")
                    else:
                        logger.warning("M5.missed: governance or modeling step did not complete")
                        root_span.set_attribute("M5", "missed")

                # M5 — Analytical Modeling sub-milestones (REQ-08)
                if classification["modeling"]:
                    if achieved["modeling_requirements_gathered"]:
                        logger.info("M5.modeling.requirements_gathered: user requirements collected")
                        root_span.set_attribute("M5.modeling.requirements", "gathered")
                    if achieved["modeling_proposal_made"]:
                        logger.info(
                            "M5.modeling.proposal_made: artifact type options proposed to user "
                            "(graphical_view/sql_view/dimension_view/fact_view/analytical_model/data_flow/er_model)"
                        )
                        root_span.set_attribute("M5.modeling.proposal", "presented")
                    if achieved["modeling_schema_presented"]:
                        logger.info("M5.modeling.schema_presented: structured schema proposal shown to user")
                        root_span.set_attribute("M5.modeling.schema", "presented")
                    if achieved["modeling_approval_requested"]:
                        logger.info("M5.modeling.approval_requested: waiting for user confirmation")
                        root_span.set_attribute("M5.modeling.approval", "pending")
                    if achieved["modeling_achieved"]:
                        logger.info("M5.modeling.achieved: Datasphere artifact created and deployed successfully")
                        root_span.set_attribute("M5.modeling", "achieved")
                    elif not achieved["modeling_requirements_gathered"] and not achieved["modeling_proposal_made"]:
                        logger.warning(
                            "M5.modeling.missed: modeling workflow did not reach requirements-gathering step"
                        )
                        root_span.set_attribute("M5.modeling", "missed")

                # M6 — Lifecycle Monitored
                if classification["monitoring"]:
                    if achieved["monitoring_achieved"]:
                        logger.info("M6.achieved: monitoring cycle completed; summary and recommendations delivered")
                        root_span.set_attribute("M6", "achieved")
                    else:
                        logger.warning("M6.missed: monitoring cycle did not complete")
                        root_span.set_attribute("M6", "missed")

                return response

            except Exception as exc:
                root_span.record_exception(exc)
                root_span.set_attribute("error", True)
                if classification["discovery"]:
                    logger.error("M1.missed: catalog scan failed; reason: %s", str(exc))
                if classification["integration"]:
                    logger.error("M2.missed: integration configuration failed; reason: %s", str(exc))
                if classification["dp_creation"]:
                    logger.error("M3.missed: Data Product activation/creation failed; reason: %s", str(exc))
                if classification["quality"]:
                    logger.error("M4.missed: data quality validation failed; reason: %s", str(exc))
                if classification["governance"]:
                    logger.error("M5.missed: governance or modeling failed; reason: %s", str(exc))
                if classification["modeling"]:
                    logger.error(
                        "M5.modeling.missed: analytical modeling workflow failed; reason: %s — "
                        "no artifact (graphical_view/sql_view/dimension_view/fact_view/"
                        "analytical_model/data_flow/er_model) was created",
                        str(exc),
                    )
                if classification["monitoring"]:
                    logger.error("M6.missed: monitoring cycle failed; reason: %s", str(exc))
                raise

    async def stream(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream agent responses. All business logic is in _run_agent() —
        no span context managers wrap any yield in this method."""
        self._touch(context_id)
        yield {"is_task_complete": False, "require_user_input": False, "content": "Processing..."}

        try:
            if tools:
                logger.info("Running with %d tool(s): %s", len(tools), [t.name for t in tools])
            else:
                logger.info("Running without tools")

            response = await self._run_agent(query, context_id, tools=tools)
            self._touch(context_id)
            yield {"is_task_complete": True, "require_user_input": False, "content": response}

        except Exception as e:
            logger.exception("stream() failed")
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": f"I encountered an error: {str(e)}. Please try again.",
            }

    async def invoke(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AgentResponse:
        last: dict = {}
        async for chunk in self.stream(query, context_id, tools=tools):
            last = chunk
        if last.get("is_task_complete"):
            return AgentResponse(status="completed", message=last["content"])
        if last.get("require_user_input"):
            return AgentResponse(status="input_required", message=last["content"])
        return AgentResponse(status="error", message=last.get("content", "Unknown error"))
