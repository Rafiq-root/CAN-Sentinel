"""
CAN-Sentinel - Alert Schema (Member 3: Security Analysis & Alert Management)

Defines the Alert data model produced by this module and consumed by the
dashboard (Member 4).

Pipeline: Member 1 (CAN data) -> Member 2 (detection) -> MEMBER 3 (alerts) -> Member 4 (dashboard)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum


class Severity(str, Enum):
    """Alert severity levels - rules documented in severity_rules.py."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Status(str, Enum):
    """Alert lifecycle: NEW -> ACKNOWLEDGED -> RESOLVED (or FALSE_POSITIVE)."""
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


# Valid lifecycle transitions (documented rule): FORWARD-ONLY.
# Rationale: terminal states cannot be reopened, so an analyst can never
# silently 'unresolve' an alert - every change leaves an audit trail entry.
VALID_TRANSITIONS: dict[Status, set[Status]] = {
    Status.NEW: {Status.ACKNOWLEDGED, Status.RESOLVED, Status.FALSE_POSITIVE},
    Status.ACKNOWLEDGED: {Status.RESOLVED, Status.FALSE_POSITIVE},
    Status.RESOLVED: set(),          # terminal
    Status.FALSE_POSITIVE: set(),    # terminal
}


def utc_now_iso() -> str:
    """Current UTC time as ISO-8601 string, e.g. 2026-10-18T14:30:00.123Z"""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def new_alert_id() -> str:
    """Readable, unique alert ID, e.g. ALR-20261018-A3F9C2"""
    return f"ALR-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"


@dataclass
class Alert:
    """One security alert, derived from one or more detection events."""
    alert_id: str
    timestamp: str               # when this alert was raised (ISO-8601 UTC)
    can_id: str                  # e.g. "0x1A4" (canonical hex string)
    severity: Severity
    category: str                # e.g. "high_frequency", "unknown_id"
    reason: str                  # human-readable explanation
    status: Status = Status.NEW
    occurrences: int = 1         # how many detection events folded into this alert
    first_seen: str = ""
    last_seen: str = ""
    source_rule: str = ""        # detection rule that fired (e.g. "HIGH_FREQUENCY")
    raw_details: dict = field(default_factory=dict)
    status_history: list = field(default_factory=list)  # audit trail of transitions (JSON only)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        d["status"] = self.status.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "Alert":
        """Rebuild an Alert from its dict form (history reload).

        Unknown/missing optional fields fall back to defaults so history
        files written by older versions still load.
        """
        return cls(
            alert_id=d["alert_id"],
            timestamp=d["timestamp"],
            can_id=d["can_id"],
            severity=Severity(d["severity"]),
            category=d["category"],
            reason=d.get("reason", ""),
            status=Status(d.get("status", "NEW")),
            occurrences=int(d.get("occurrences", 1)),
            first_seen=d.get("first_seen", ""),
            last_seen=d.get("last_seen", ""),
            source_rule=d.get("source_rule", ""),
            raw_details=d.get("raw_details") or {},
            status_history=list(d.get("status_history") or []),
        )
