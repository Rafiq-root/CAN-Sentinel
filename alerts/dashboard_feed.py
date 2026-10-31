"""M3 -> M4 dashboard feed: render-ready payload for the web UI.

One function, dashboard_payload(manager), produces everything the
Member-4 dashboard needs to render the alert console:

    generated_at     ISO-8601 UTC "now" (refresh indicator)
    summary          totals: by severity, by status, rejected events
    critical_active  ACTIVE alerts on CRITICAL_CAN_IDS (brake/steering/
                     engine/airbag) - the triage panel, HIGH first
    recent           newest-first flat alert rows (table body)

Rows are FLAT dicts (strings/ints only) so the dashboard renders them
with zero knowledge of M3 internals. status_history and raw_details
are deliberately excluded - they stay JSON-only exports (storage.py).

Read-only: calling this never mutates manager state; the UI can poll.
"""

from .schema import utc_now_iso
from .severity_rules import CRITICAL_CAN_IDS

_SEVERITIES = ("HIGH", "MEDIUM", "LOW")
_STATUSES = ("NEW", "ACKNOWLEDGED", "RESOLVED", "FALSE_POSITIVE")
_ACTIVE = ("NEW", "ACKNOWLEDGED")
_SEVERITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _name(value):
    """Enum -> name, anything else -> str; get_alerts() returns strings."""
    return getattr(value, "name", str(value))


def _flat(alert):
    return {
        "alert_id": alert.get("alert_id", ""),
        "timestamp": alert.get("timestamp", ""),
        "can_id": alert.get("can_id", ""),
        "rule": alert.get("source_rule", alert.get("rule", "")),
        "severity": _name(alert.get("severity", "")),
        "status": _name(alert.get("status", "")),
        "occurrences": alert.get("occurrences", 1),
        "first_seen": alert.get("first_seen", ""),
        "last_seen": alert.get("last_seen", ""),
        "reason": alert.get("reason", ""),
    }


def _as_int(value):
    """Best-effort int form of a CAN id (int or hex string like '0x0D2')."""
    if isinstance(value, int):
        return value
    try:
        return int(str(value), 16)
    except (TypeError, ValueError):
        return None


def _is_critical(can_id):
    # Resolved at CALL time, not import time: the active vehicle profile can
    # be swapped (set_vehicle_critical_map) - a payload built after a swap
    # must reflect it, never a stale set captured at import. 4-6 entries.
    value = _as_int(can_id)
    if value is None:
        return False
    return value in {v for v in (_as_int(c) for c in CRITICAL_CAN_IDS)
                     if v is not None}


def dashboard_payload(manager, recent_limit=25):
    """Build the render-ready dashboard dict from an AlertManager."""
    alerts = manager.get_alerts()
    by_severity = {s: 0 for s in _SEVERITIES}
    by_status = {s: 0 for s in _STATUSES}
    active = []
    for a in alerts:
        sev = _name(a.get("severity", ""))
        stat = _name(a.get("status", ""))
        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_status[stat] = by_status.get(stat, 0) + 1
        if stat in _ACTIVE:
            active.append(a)

    critical = [a for a in active if _is_critical(a.get("can_id", ""))]
    critical.sort(key=lambda a: a.get("timestamp", ""), reverse=True)
    critical.sort(key=lambda a: _SEVERITY_RANK.get(_name(a.get("severity", "")), 99))

    return {
        "generated_at": utc_now_iso(),
        "summary": {
            "total_alerts": len(alerts),
            "active_alerts": len(active),
            "by_severity": by_severity,
            "by_status": by_status,
            "rejected_events": len(manager.rejected_events),
        },
        "critical_active": [_flat(a) for a in critical],
        "recent": [_flat(a) for a in alerts[:recent_limit]],
    }
