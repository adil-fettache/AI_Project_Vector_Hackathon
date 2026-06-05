"""Approval Gateway for the Data Product Lifecycle Agent.

Controls which action categories require human approval before execution.
All write tools must call requires_approval() before invoking Datasphere APIs.
"""
import logging
import time
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ApprovalMode(str, Enum):
    AUTONOMOUS = "autonomous"
    SUPERVISED = "supervised"
    ALWAYS_APPROVE = "always_approve"


# Default per-category approval configuration — plain Python constant (NOT a decorator)
APPROVAL_CONFIG: dict[str, ApprovalMode] = {
    "catalog_read":           ApprovalMode.AUTONOMOUS,
    "monitoring_read":        ApprovalMode.AUTONOMOUS,
    "code_generation":        ApprovalMode.AUTONOMOUS,
    "connection_create":      ApprovalMode.SUPERVISED,
    "replication_flow_config": ApprovalMode.SUPERVISED,
    "data_product_publish":   ApprovalMode.SUPERVISED,
    "governance_change":      ApprovalMode.ALWAYS_APPROVE,
    "analytical_model_create": ApprovalMode.SUPERVISED,
    "data_profiling_run":     ApprovalMode.AUTONOMOUS,
}


class ApprovalGateway:
    """Manages per-action-category approval modes.

    Usage:
        gw = ApprovalGateway()
        if gw.requires_approval("connection_create"):
            msg = gw.format_approval_request(...)
            # surface msg to user and wait for "approve" / "reject"
        gw.log_decision("connection_create", "create_connection", "approved")
    """

    def __init__(self, config: Optional[dict[str, ApprovalMode]] = None):
        self._config: dict[str, ApprovalMode] = dict(config if config is not None else APPROVAL_CONFIG)

    def get_mode(self, category: str) -> ApprovalMode:
        """Return approval mode for category; defaults to ALWAYS_APPROVE if unknown."""
        return self._config.get(category, ApprovalMode.ALWAYS_APPROVE)

    def requires_approval(self, category: str) -> bool:
        """Return True if category needs human approval."""
        return self.get_mode(category) in (ApprovalMode.SUPERVISED, ApprovalMode.ALWAYS_APPROVE)

    def format_approval_request(
        self,
        action_category: str,
        tool_name: str,
        target_api: str,
        description: str,
        side_effects: str,
    ) -> str:
        """Format a structured approval request to present to the user."""
        mode = self.get_mode(action_category)
        note = (
            "This action **cannot be skipped** — explicit approval is required."
            if mode == ApprovalMode.ALWAYS_APPROVE
            else "Please approve or reject before execution."
        )
        return (
            f"**Approval Required — {action_category.replace('_', ' ').title()}**\n\n"
            f"- **Action**: {description}\n"
            f"- **Tool**: `{tool_name}`\n"
            f"- **API**: `{target_api}`\n"
            f"- **Side effects**: {side_effects}\n\n"
            f"{note}\n\nReply **approve** to proceed or **reject** to cancel."
        )

    def format_autonomous_notice(self, category: str, tool_name: str, target_api: str, description: str) -> str:
        """Format a notice for autonomous (no-approval) actions."""
        return f"[autonomous:{category}] `{tool_name}` → `{target_api}`: {description}"

    def log_decision(
        self,
        category: str,
        tool_name: str,
        decision: str,
        target_api: str = "",
        user: str = "unknown",
    ) -> None:
        """Emit a structured audit log entry for the approval decision."""
        logger.info(
            "APPROVAL_AUDIT | ts=%s | category=%s | tool=%s | api=%s | decision=%s | user=%s",
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            category, tool_name, target_api or "n/a", decision, user,
        )

    def get_config_summary(self) -> str:
        """Return human-readable summary of current approval configuration."""
        icons = {"autonomous": "🟢", "supervised": "🟡", "always_approve": "🔴"}
        lines = ["**Approval Configuration**\n"]
        for cat, mode in self._config.items():
            lines.append(f"- {icons.get(mode.value, '⚪')} `{cat}`: **{mode.value}**")
        lines.append(
            "\n🟢 autonomous = executes immediately  "
            "🟡 supervised = needs your approval  "
            "🔴 always_approve = never skippable"
        )
        return "\n".join(lines)

    def update_mode(self, category: str, mode: ApprovalMode) -> None:
        """Update the approval mode for a category and log the change."""
        old = self._config.get(category, ApprovalMode.ALWAYS_APPROVE)
        self._config[category] = mode
        logger.info("APPROVAL_CONFIG_CHANGE | category=%s | %s -> %s", category, old.value, mode.value)
