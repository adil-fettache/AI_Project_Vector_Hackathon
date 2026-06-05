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
        id="data-product-lifecycle-agent",
        name="data-product-lifecycle-agent",
        description="An autonomous AI agent that orchestrates the end-to-end lifecycle of SAP-managed and custom Data Products in SAP Business Data Cloud, covering discovery, SAP and non-SAP source integration, activation, data quality validation, governance, analytical modeling, and continuous lifecycle monitoring.",
        tags=["data-product", "lifecycle", "datasphere", "sap-bdc", "governance", "integration"],
        examples=["Scan the BDC catalog for available Finance Data Products I can activate", "Create a connection to S/4HANA and configure a replication flow for table ACDOCA", "Check for duplicate Data Products before I create a custom one for my Salesforce source"],
    )
    agent_card = AgentCard(
        name="data-product-lifecycle-agent",
        description="An autonomous AI agent that orchestrates the end-to-end lifecycle of SAP-managed and custom Data Products in SAP Business Data Cloud, covering discovery, SAP and non-SAP source integration, activation, data quality validation, governance, analytical modeling, and continuous lifecycle monitoring.",
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
