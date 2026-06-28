# CRITICAL: Initialize telemetry BEFORE importing AI frameworks
from sap_cloud_sdk.aicore import set_aicore_config
from sap_cloud_sdk.core.telemetry import auto_instrument

set_aicore_config()
auto_instrument()

import logging
import os

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agent_executor import AgentExecutor
from opentelemetry.instrumentation.starlette import StarletteInstrumentor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))


@click.command()
@click.option("--host", default=HOST)
@click.option("--port", default=PORT)
def main(host: str, port: int):
    skill = AgentSkill(
        id="bdc-data-lifecycle-agent",
        name="bdc-data-lifecycle-agent",
        description=(
            "Autonomous Data Product Lifecycle Agent for SAP Business Data Cloud (BDC). "
            "Orchestrates the full end-to-end lifecycle across BDC, Datasphere, Databricks, "
            "HANA Data Lake (HDL), BDC Cockpit, SAP source systems (S/4HANA, SuccessFactors, Ariba, "
            "Fieldglass, Concur), and non-SAP sources. "
            "SAP path: searches BDC managed catalog, activates/reuses SAP-managed Data Products, "
            "configures Datasphere connections, triggers replication and transformation flows. "
            "Non-SAP path: classifies integration protocol from docs (REST/OData/GraphQL/JDBC/SFTP/SDK), "
            "generates Databricks DPE SDK notebooks (HdlPort/HdlConfig/Folder), lands data in HDL "
            "(INBOUND->TRANSFORMATION->OUTPUTPORT), registers and publishes Data Products in BDC Cockpit. "
            "Enforces HITL approval before every write/destructive action. "
            "Includes data quality gate, governance metadata, lineage, monitoring, and alerting."
        ),
        tags=["bdc", "data", "lifecycle", "agent", "datasphere", "databricks", "hdl", "s4hana", "successfactors"],
        examples=[
            "Discover my BDC landscape and list all data products",
            "I want to integrate Jira Issues into BDC as a Data Product",
            "Find and activate the S/4HANA Sales Order data product in my Datasphere space",
            "Generate a Databricks notebook to extract data from a REST API and land it in HDL",
            "Run the quality gate for the Employee Data Product before publishing",
            "What Databricks dependencies do I need for a JDBC integration with PostgreSQL?",
        ],
    )
    agent_card = AgentCard(
        name="bdc-data-lifecycle-agent",
        description=(
            "Autonomous Data Product Lifecycle Agent for SAP Business Data Cloud (BDC). "
            "Full BDC landscape scope: BDC catalog, Datasphere, Databricks, HANA Data Lake (HDL), "
            "BDC Cockpit, SAP sources (S/4HANA, SuccessFactors, Ariba, Fieldglass, Concur), "
            "and non-SAP sources via any integration protocol. "
            "Enforces human-in-the-loop approval before all write/destructive actions."
        ),
        url=os.environ.get("AGENT_PUBLIC_URL", f"http://{host}:{port}/"),
        version="1.0.0",
        default_input_modes=["text", "text/plain"],
        default_output_modes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True, push_notifications=False),
        skills=[skill],
    )
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=AgentExecutor(),
            task_store=InMemoryTaskStore(),
        ),
    )
    app = server.build()
    StarletteInstrumentor().instrument_app(app)

    logger.info(f"Starting A2A server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
