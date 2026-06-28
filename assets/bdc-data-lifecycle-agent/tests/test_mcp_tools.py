"""Tests for mcp_tools.py — covers mock tool loading, user token helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

APP_PATH = str(Path(__file__).parent.parent / "app")
if APP_PATH not in sys.path:
    sys.path.insert(0, APP_PATH)

import mcp_tools
from mcp_tools import (
    _build_mock_tools,
    get_mcp_tools,
    set_user_token_for_tools,
    reset_user_token_for_tools,
    _MOCK_FILE,
)


# ---------------------------------------------------------------------------
# _build_mock_tools
# ---------------------------------------------------------------------------

def test_build_mock_tools_returns_list_when_file_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_tools, "_MOCK_FILE", tmp_path / "nonexistent.json")
    result = mcp_tools._build_mock_tools()
    assert isinstance(result, list)
    assert len(result) == 0


def test_build_mock_tools_returns_tools_from_valid_file(tmp_path, monkeypatch):
    mock_data = {
        "servers": {
            "test_server": {
                "tools": {
                    "my_tool": {
                        "description": "A test tool",
                        "mock_response": {"result": "ok"},
                        "input_schema": {
                            "properties": {"query": {"type": "string", "description": "Query"}},
                            "required": ["query"],
                        },
                    }
                }
            }
        }
    }
    mock_file = tmp_path / "mcp-mock.json"
    mock_file.write_text(json.dumps(mock_data))
    monkeypatch.setattr(mcp_tools, "_MOCK_FILE", mock_file)

    tools = mcp_tools._build_mock_tools()
    assert len(tools) == 1
    assert tools[0].name == "my_tool"


def test_build_mock_tools_handles_invalid_json(tmp_path, monkeypatch):
    bad_file = tmp_path / "mcp-mock.json"
    bad_file.write_text("NOT_VALID_JSON{{{")
    monkeypatch.setattr(mcp_tools, "_MOCK_FILE", bad_file)
    tools = mcp_tools._build_mock_tools()
    assert tools == []


def test_build_mock_tools_handles_optional_fields(tmp_path, monkeypatch):
    mock_data = {
        "servers": {
            "srv": {
                "tools": {
                    "simple_tool": {
                        "description": "Simple",
                        "mock_response": {},
                        "input_schema": {
                            "properties": {
                                "num": {"type": "integer"},
                                "flag": {"type": "boolean"},
                                "amount": {"type": "number"},
                                "text": {"type": "string"},
                                "opt": {"type": "string"},
                            },
                            "required": ["num", "flag", "amount", "text"],
                        },
                    }
                }
            }
        }
    }
    mock_file = tmp_path / "mcp-mock.json"
    mock_file.write_text(json.dumps(mock_data))
    monkeypatch.setattr(mcp_tools, "_MOCK_FILE", mock_file)

    tools = mcp_tools._build_mock_tools()
    assert len(tools) == 1


# ---------------------------------------------------------------------------
# get_mcp_tools — IBD_TESTING mode
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_mcp_tools_in_testing_mode_returns_list(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_tools, "_MOCK_FILE", tmp_path / "nonexistent.json")
    result = await get_mcp_tools(user_token=None)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_mcp_tools_returns_mock_tools(tmp_path, monkeypatch):
    mock_data = {
        "servers": {
            "s": {
                "tools": {
                    "tool_a": {
                        "description": "A",
                        "mock_response": {},
                        "input_schema": {"properties": {}, "required": []},
                    }
                }
            }
        }
    }
    mock_file = tmp_path / "mcp-mock.json"
    mock_file.write_text(json.dumps(mock_data))
    monkeypatch.setattr(mcp_tools, "_MOCK_FILE", mock_file)
    result = await get_mcp_tools(user_token=None)
    assert len(result) == 1
    assert result[0].name == "tool_a"


# ---------------------------------------------------------------------------
# mock tool coroutine invocation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_tool_coroutine_returns_response(tmp_path, monkeypatch):
    mock_data = {
        "servers": {
            "s": {
                "tools": {
                    "echo_tool": {
                        "description": "Echo",
                        "mock_response": {"echo": "hello"},
                        "input_schema": {"properties": {}, "required": []},
                    }
                }
            }
        }
    }
    mock_file = tmp_path / "mcp-mock.json"
    mock_file.write_text(json.dumps(mock_data))
    monkeypatch.setattr(mcp_tools, "_MOCK_FILE", mock_file)

    tools = mcp_tools._build_mock_tools()
    assert len(tools) == 1
    result = await tools[0].coroutine()
    data = json.loads(result)
    assert data["echo"] == "hello"


# ---------------------------------------------------------------------------
# user token context helpers
# ---------------------------------------------------------------------------

def test_set_and_reset_user_token_complete():
    from mcp_tools import _user_token_context
    ctx_tok = set_user_token_for_tools("my-test-token")
    assert _user_token_context.get() == "my-test-token"
    reset_user_token_for_tools(ctx_tok)


def test_set_user_token_none():
    ctx_tok = set_user_token_for_tools(None)
    from mcp_tools import _user_token_context
    assert _user_token_context.get() is None
    reset_user_token_for_tools(ctx_tok)
