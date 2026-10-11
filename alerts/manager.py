"""
CAN-Sentinel - Alert Manager (Member 3: Security Analysis & Alert Management)

Consumes detection events from the Intrusion Detection Engine (Member 2),
classifies them via the documented severity rules, and maintains alert
history with duplicate folding.

DUPLICATE HANDLING (documented rule):
  A detection event is a DUPLICATE of an existing alert when both share the
  same (can_id, rule) and occur within the dedupe window (default 10 s).
  Duplicates fold into the existing alert: occurrences += 1, last_seen
  updated. No new alert is raised (prevents alert flooding during an attack).

Integration (for Members 1 & 4):
    from alerts.manager import AlertManager
    mgr = AlertManager()
    alert = mgr.process_event(event_dict)      # Alert (new or folded)
    mgr.get_alerts(severity="HIGH", limit=20)  # newest-first query for UI
    mgr.stats()                                # severity/status counts
"""

from __future__ import annotations

from datetime import datetime

from .schema import Alert, new_alert_id, utc_now_iso
from .severity_rules import canonical_can_id, classify


class AlertManager:
    """Turns detection events into traceable alerts with duplicate folding."""

    def __init__(self, dedupe_window_seconds: int = 10):
        self.dedupe_window_seconds = dedupe_window_seconds
        self.alerts: list[Alert] = []                    # full history, oldest first
        self._active: dict[tuple[str, str], Alert] = {}  # (can_id, RULE) -> newest alert

    # ---------- core ----------

    def process_event(self, event: dict) -> Alert:
        """Process one detection event; return the new or updated Alert."""
        can_id = canonical_can_id(event.get("can_id", ""))
        rule = str(event.get("rule", "")).upper()
        severity, category = classify(event)
        ts = event.get("timestamp") or utc_now_iso()

        key = (can_id, rule)
        existing = self._active.get(key)
        if existing is not None and self._within_window(existing.last_seen, ts):
            existing.occurrences += 1
            existing.last_seen = ts
            return existing

        alert = Alert(
            alert_id=new_alert_id(),
            timestamp=ts,
            can_id=can_id,
            severity=severity,
            category=category,
            reason=str(event.get("reason", "")),
            first_seen=ts,
            last_seen=ts,
            source_rule=rule,
            raw_details=dict(event.get("details", {})),
        )
        self.alerts.append(alert)
        self._active[key] = alert
        return alert

    # ---------- query API (dashboard / Member 4) ----------

    def get_alerts(self, severity: str | None = None, status: str | None = None,
                   can_id: str | None = None, limit: int | None = None) -> list[dict]:
        """Return alerts (newest first) as dicts with optional filters."""
        out: list[dict] = []
        for a in reversed(self.alerts):
            if severity and a.severity.value != severity.upper():
                continue
            if status and a.status.value != status.upper():
                continue
            if can_id and a.can_id != canonical_can_id(can_id):
                continue
            out.append(a.to_dict())
            if limit is not None and len(out) >= limit:
                break
        return out

    def stats(self) -> dict:
        """Aggregate counts for the dashboard."""
        by_severity = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        by_status: dict[str, int] = {}
        for a in self.alerts:
            by_severity[a.severity.value] += 1
            by_status[a.status.value] = by_status.get(a.status.value, 0) + 1
        return {"total": len(self.alerts), "by_severity": by_severity, "by_status": by_status}

    # ---------- internals ----------

    def _within_window(self, earlier: str, later: str) -> bool:
        """True when 'later' falls within dedupe_window_seconds of 'earlier'."""
        try:
            t1 = datetime.fromisoformat(earlier.replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(later.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return True  # unparseable time -> prefer folding over spamming
        return (t2 - t1).total_seconds() <= self.dedupe_window_seconds
