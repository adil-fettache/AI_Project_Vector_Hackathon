# Bdc Data Lifecycle Agent

An autonomous AI agent that manages the full lifecycle of SAP Business Data Cloud data products including landscape discovery, source integration, data quality enforcement, governance, monitoring, and SAP Analytics Cloud consumption

## Overview

Uses A2A Protocol, LangGraph, LiteLLM, and SAP Cloud SDK.

## Structure

- `app/main.py` - A2A server entry
- `app/agent_executor.py` - Request handling
- `app/agent.py` - Agent logic
