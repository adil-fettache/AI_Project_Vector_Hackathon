# Data Product Lifecycle Agent

An autonomous AI agent that orchestrates the end-to-end lifecycle of SAP-managed and custom Data Products in SAP Business Data Cloud, covering discovery, SAP and non-SAP source integration, activation, data quality validation, governance, analytical modeling, and continuous lifecycle monitoring.

## Overview

Uses A2A Protocol, LangGraph, LiteLLM, and SAP Cloud SDK.

## Structure

- `app/main.py` - A2A server entry
- `app/agent_executor.py` - Request handling
- `app/agent.py` - Agent logic
