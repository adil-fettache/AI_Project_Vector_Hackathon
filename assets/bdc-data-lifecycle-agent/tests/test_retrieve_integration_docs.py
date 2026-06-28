"""Test retrieve_integration_docs — mocks doc retrieval, verifies non-empty doc text."""
from tests._helpers import parse_result
from tools import _retrieve_integration_docs


def test_retrieve_docs_returns_tool_name():
    result = parse_result(_retrieve_integration_docs(system_name="Jira"))
    assert result["tool"] == "retrieve_integration_docs"


def test_retrieve_docs_returns_non_empty_docs():
    result = parse_result(_retrieve_integration_docs(system_name="PostgreSQL"))
    assert len(result["docs"]) > 0


def test_retrieve_docs_captures_system_name():
    result = parse_result(_retrieve_integration_docs(system_name="Jira"))
    assert result["system_name"] == "Jira"


def test_retrieve_docs_accepts_url_hint():
    result = parse_result(_retrieve_integration_docs(system_name="MyAPI", url_hint="https://myapi.example.com"))
    assert result["url_hint"] == "https://myapi.example.com"
