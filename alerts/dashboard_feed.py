"""M3 -> M4 dashboard feed: render-ready payload for the web UI.

One function, dashboard_payload(manager), produces everything the
Member-4 dashboard needs to render the alert console:

    generated_at     ISO-8601 UTC "now" (refresh indicator)
    summary          totals: by severity, by status, rejected events
    critical_active  triage panel: active alerts on the ACTIVE vehicle's
                     CRITICAL_CAN_IDS, aggregated PER SYSTEM (one row per
                     attacked can_id): alert_count, total_occurrences,
                     highest_severity, top_rule, first/last seen. Ordered
                     HIGH first, then total occurrences.
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


def _aggregate_critical(active):
    """Collapse active critical alerts into one row per attacked system.

    The panel answers 'what do I need to work on' (one row per attacked
    CAN ID); the recent list answers 'what happened' (one row per alert).
    Aggregation added Nov 1: replaying the real GEM dataset produced 1,291
    tampering alerts, which made a per-alert panel unreadable.
    """
    groups = {}
    for a in active:
        if not _is_critical(a.get("can_id", "")):
            continue
        can_id = a.get("can_id", "")
        g = groups.get(can_id)
        if g is None:
            groups[can_id] = {
                "can_id": can_id,
                "alert_count": 0,
                "total_occurrences": 0,
                "highest_severity": "LOW",
                "top_rule": "",
                "first_seen": a.get("first_seen", ""),
                "last_seen": a.get("last_seen", ""),
                "_rules": {},
                "_sev_rank": 99,
            }
            g = groups[can_id]
        g["alert_count"] += 1
        g["total_occurrences"] += a.get("occurrences", 1) or 1
        sev = _name(a.get("severity", ""))
        if _SEVERITY_RANK.get(sev, 99) < g["_sev_rank"]:
            g["highest_severity"] = sev
            g["_sev_rank"] = _SEVERITY_RANK.get(sev, 99)
        rule = a.get("source_rule", a.get("rule", "")) or ""
        g["_rules"][rule] = g["_rules"].get(rule, 0) + 1
        first, last = a.get("first_seen", ""), a.get("last_seen", "")
        if first and (not g["first_seen"] or first < g["first_seen"]):
            g["first_seen"] = first
        if last and (not g["last_seen"] or last > g["last_seen"]):
            g["last_seen"] = last
    rows = []
    for g in groups.values():
        g["top_rule"] = max(g["_rules"], key=g["_rules"].get) if g["_rules"] else ""
        del g["_rules"]
        del g["_sev_rank"]
        rows.append(g)
    rows.sort(key=lambda g: g["total_occurrences"], reverse=True)
    rows.sort(key=lambda g: _SEVERITY_RANK.get(g["highest_severity"], 99))
    return rows


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

    critical_rows = _aggregate_critical(active)

    return {
        "generated_at": utc_now_iso(),
        "summary": {
            "total_alerts": len(alerts),
            "active_alerts": len(active),
            "by_severity": by_severity,
            "by_status": by_status,
            "rejected_events": len(manager.rejected_events),
        },
        "critical_active": critical_rows,
        "recent": [_flat(a) for a in alerts[:recent_limit]],
    }
