"""Tests for agent.py — covers SampleAgent stream/invoke and decorator functions."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

APP_PATH = str(Path(__file__).parent.parent / "app")
if APP_PATH not in sys.path:
    sys.path.insert(0, APP_PATH)

from agent import SampleAgent, get_model_name, get_temperature, get_system_prompt, AgentResponse


# ---------------------------------------------------------------------------
# Decorator functions
# ---------------------------------------------------------------------------

def test_get_model_name():
    assert isinstance(get_model_name(), str)
    assert len(get_model_name()) > 0


def test_get_temperature():
    assert isinstance(get_temperature(), float)
    assert 0.0 <= get_temperature() <= 1.0


def test_get_system_prompt():
    prompt = get_system_prompt()
    assert "M1" in prompt
    assert "M2" in prompt
    assert "HIGH-RISK" in prompt or "activate_data_product" in prompt


# ---------------------------------------------------------------------------
# SampleAgent construction
# ---------------------------------------------------------------------------

def test_sample_agent_instantiates():
    with patch("agent.ChatLiteLLM"):
        agent = SampleAgent()
        assert agent is not None


# ---------------------------------------------------------------------------
# SampleAgent.stream()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stream_yields_processing_then_complete():
    mock_result = {"messages": [MagicMock(content="Hello, I am the BDC agent.")]}

    with patch("agent.ChatLiteLLM"), \
         patch("agent.create_agent") as mock_create_agent:
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value=mock_result)
        mock_create_agent.return_value = mock_graph

        agent = SampleAgent()
        chunks = []
        async for chunk in agent.stream("list all spaces", "ctx_001"):
            chunks.append(chunk)

    assert len(chunks) >= 2
    assert chunks[0]["content"] == "Processing..."
    assert chunks[-1]["is_task_complete"] is True
    assert "Hello" in chunks[-1]["content"]


@pytest.mark.asyncio
async def test_stream_handles_exception():
    with patch("agent.ChatLiteLLM"), \
         patch("agent.create_agent") as mock_create_agent:
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("LLM error"))
        mock_create_agent.return_value = mock_graph

        agent = SampleAgent()
        chunks = []
        async for chunk in agent.stream("query", "ctx_002"):
            chunks.append(chunk)

    last = chunks[-1]
    assert last["is_task_complete"] is True
    assert "error" in last["content"].lower()


# ---------------------------------------------------------------------------
# SampleAgent.invoke()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoke_returns_completed():
    mock_result = {"messages": [MagicMock(content="Landscape summary")]}

    with patch("agent.ChatLiteLLM"), \
         patch("agent.create_agent") as mock_create_agent:
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value=mock_result)
        mock_create_agent.return_value = mock_graph

        agent = SampleAgent()
        response = await agent.invoke("Discover landscape", "ctx_003")

    assert isinstance(response, AgentResponse)
    assert response.status == "completed"
    assert response.message == "Landscape summary"


@pytest.mark.asyncio
async def test_invoke_returns_error_on_exception():
    with patch("agent.ChatLiteLLM"), \
         patch("agent.create_agent") as mock_create_agent:
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("Network failure"))
        mock_create_agent.return_value = mock_graph

        agent = SampleAgent()
        response = await agent.invoke("query", "ctx_004")

    assert response.status == "error" or "error" in response.message.lower()


# ---------------------------------------------------------------------------
# Thread TTL eviction
# ---------------------------------------------------------------------------

def test_touch_evicts_old_threads():
    import time
    with patch("agent.ChatLiteLLM"), \
         patch("agent.InMemorySaver") as mock_saver:
        mock_saver_instance = MagicMock()
        mock_saver.return_value = mock_saver_instance
        agent = SampleAgent()
        # Manually age a thread
        agent._last_active["old_thread"] = 0.0  # expired immediately
        agent._touch("new_thread")
        assert "old_thread" not in agent._last_active
        mock_saver_instance.delete_thread.assert_called_with("old_thread")
