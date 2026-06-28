"""Shared test helpers for bdc-data-lifecycle-agent tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure app/ is on sys.path for all tests
APP_PATH = str(Path(__file__).parent.parent / "app")
if APP_PATH not in sys.path:
    sys.path.insert(0, APP_PATH)


def parse_result(result) -> dict:
    """Parse a tool result (string or dict) into a dict."""
    if isinstance(result, str):
        return json.loads(result)
    return result
