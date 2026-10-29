"""Validation helpers for the CAN-Sentinel dashboard snapshot contract."""
from __future__ import annotations

from typing import Any

REQUIRED_TOP_LEVEL = {
    "schema_version", "run_id", "generated_at", "status",
    "data_mode", "statistics", "ecus", "recent_frames", "alerts",
}

def validate_snapshot(snapshot: dict[str, Any]) -> list[str]:
    """Return a list of schema issues; an empty list means basic validation passed."""
    issues: list[str] = []
    if not isinstance(snapshot, dict):
        return ["Snapshot must be a JSON object."]

    missing = sorted(REQUIRED_TOP_LEVEL - set(snapshot.keys()))
    if missing:
        issues.append(f"Missing top-level fields: {', '.join(missing)}")

    for field in ("statistics",):
        if field in snapshot and not isinstance(snapshot[field], dict):
            issues.append(f"'{field}' must be an object.")
    for field in ("ecus", "recent_frames", "alerts"):
        if field in snapshot and not isinstance(snapshot[field], list):
            issues.append(f"'{field}' must be a list.")

    for idx, frame in enumerate(snapshot.get("recent_frames", [])):
        if not isinstance(frame, dict):
            issues.append(f"Frame at index {idx} must be an object.")
            continue
        for key in ("timestamp", "can_id"):
            if key not in frame:
                issues.append(f"Frame at index {idx} is missing '{key}'.")

    for idx, alert in enumerate(snapshot.get("alerts", [])):
        if not isinstance(alert, dict):
            issues.append(f"Alert at index {idx} must be an object.")
            continue
        for key in ("alert_id", "timestamp", "severity", "message"):
            if key not in alert:
                issues.append(f"Alert at index {idx} is missing '{key}'.")

    return issues
