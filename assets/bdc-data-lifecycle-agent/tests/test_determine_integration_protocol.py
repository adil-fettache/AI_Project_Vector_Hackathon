"""Test determine_integration_protocol — verifies protocol extracted from docs."""
from tests._helpers import parse_result
from tools import _determine_integration_protocol


def test_detects_rest_protocol():
    docs = "This system exposes a REST API over HTTP with OAuth2 authentication."
    result = parse_result(_determine_integration_protocol(system_name="MyAPI", integration_docs=docs))
    assert result["protocol"] == "REST"


def test_detects_jdbc_protocol():
    docs = "Connect via JDBC driver to the PostgreSQL database on port 5432."
    result = parse_result(_determine_integration_protocol(system_name="PG", integration_docs=docs))
    assert result["protocol"] == "JDBC"


def test_detects_graphql_protocol():
    docs = "Access data using GraphQL queries at the /graphql endpoint."
    result = parse_result(_determine_integration_protocol(system_name="GQL", integration_docs=docs))
    assert result["protocol"] == "GraphQL"


def test_detects_sftp_protocol():
    docs = "Files are transferred via SFTP on port 22."
    result = parse_result(_determine_integration_protocol(system_name="Files", integration_docs=docs))
    assert result["protocol"] == "SFTP"


def test_detects_odata_protocol():
    docs = "OData V4 service available at /odata/v4/."
    result = parse_result(_determine_integration_protocol(system_name="SAP", integration_docs=docs))
    assert result["protocol"] == "OData"


def test_returns_required_parameters():
    docs = "REST API with API key auth."
    result = parse_result(_determine_integration_protocol(system_name="API", integration_docs=docs))
    assert "required_parameters" in result
    assert len(result["required_parameters"]) > 0


def test_protocol_never_hardcoded():
    """Protocol is extracted from docs, not hardcoded — different docs yield different protocols."""
    docs_rest = "REST API endpoint."
    docs_jdbc = "JDBC database connection."
    r1 = parse_result(_determine_integration_protocol("SysA", docs_rest))
    r2 = parse_result(_determine_integration_protocol("SysB", docs_jdbc))
    assert r1["protocol"] != r2["protocol"]
