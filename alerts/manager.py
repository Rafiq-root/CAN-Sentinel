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

INPUT HARDENING (documented):
  Every event is validated at the pipeline boundary (alerts/validation.py).
  Invalid events are REJECTED and logged (never raised) so one malformed
  event cannot crash the alerting service while an attack is in progress.

STATUS LIFECYCLE (documented):
  NEW -> ACKNOWLEDGED -> RESOLVED, or NEW/ACKNOWLEDGED -> FALSE_POSITIVE.
  Forward-only (see schema.VALID_TRANSITIONS); every transition is recorded
  in the alert's status_history with a timestamp and optional analyst note.

PERSISTENCE (documented):
  With history_path set, the manager loads existing history at startup and
  writes the full history back after EVERY change (new alert, folded
  duplicate, status transition). The dashboard can therefore restart at any
  time without losing alerts. Without history_path the manager is purely
  in-memory (backward compatible). A corrupt or unreadable history file
  never crashes the manager: it starts fresh and records the problem in
  self.persistence_errors.

Integration (for Members 1 & 4):
    from alerts.manager import AlertManager
    mgr = AlertManager(history_path="alert_history.json")
    alert = mgr.process_event(event_dict)      # Alert (new/folded) or None if invalid
    mgr.acknowledge(alert_id, note="...")      # lifecycle transitions
    mgr.get_alerts(severity="HIGH", limit=20)  # newest-first query for UI
    mgr.stats()                                # severity/status counts + rejected count
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .schema import Alert, Status, VALID_TRANSITIONS, new_alert_id, utc_now_iso
from .severity_rules import canonical_can_id, classify
from .storage import load_alerts_json, save_alerts_json
from .validation import validate_event


class AlertManager:
    """Turns detection events into traceable alerts with duplicate folding."""

    def __init__(self, dedupe_window_seconds: int = 10, history_path: str | Path | None = None):
        self.dedupe_window_seconds = dedupe_window_seconds
        self.alerts: list[Alert] = []                     # full history, oldest first
        self._active: dict[tuple[str, str], Alert] = {}   # (can_id, RULE) -> newest alert
        self._by_id: dict[str, Alert] = {}                # alert_id -> Alert
        self.rejected_events: list[dict] = []             # boundary rejection log (in-memory)
        self.persistence_errors: list[str] = []           # history load/save problems (never fatal)
        self.last_error: str = ""                         # reason of the last failed call
        self._history_path = Path(history_path) if history_path else None
        if self._history_path is not None:
            self._load()

    # ---------- core ----------

    def process_event(self, event: dict) -> Alert | None:
        """Process one detection event.

        Returns the new or updated Alert, or None when the event failed
        boundary validation (rejection is recorded in self.rejected_events).
        """
        ok, error = validate_event(event)
        if not ok:
            self.rejected_events.append(
                {"rejected_at": utc_now_iso(), "reason": error, "event": str(event)[:200]}
            )
            return None

        can_id = canonical_can_id(event.get("can_id", ""))
        rule = str(event.get("rule", "")).upper()
        severity, category = classify(event)
        ts = event.get("timestamp") or utc_now_iso()

        key = (can_id, rule)
        existing = self._active.get(key)
        if existing is not None and self._within_window(existing.last_seen, ts):
            existing.occurrences += 1
            existing.last_seen = ts
            self._persist()
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
        self._by_id[alert.alert_id] = alert
        self._persist()
        return alert

    # ---------- status lifecycle ----------

    def set_status(self, alert_id: str, new_status: str, note: str = "") -> Alert | None:
        """Transition an alert's status following the documented lifecycle.

        Returns the updated Alert, or None with the reason in self.last_error
        when the alert is unknown, the status name is invalid, or the
        transition is not allowed (e.g. RESOLVED -> NEW).
        """
        self.last_error = ""
        alert = self._by_id.get(alert_id)
        if alert is None:
            self.last_error = f"unknown alert_id '{alert_id}'"
            return None
        try:
            target = Status(str(new_status).strip().upper())
        except ValueError:
            self.last_error = f"invalid status '{new_status}'"
            return None
        if target not in VALID_TRANSITIONS[alert.status]:
            self.last_error = f"invalid transition {alert.status.value} -> {target.value}"
            return None
        alert.status = target
        alert.status_history.append(
            {"status": target.value, "at": utc_now_iso(), "note": note}
        )
        self._persist()
        return alert

    def acknowledge(self, alert_id: str, note: str = "") -> Alert | None:
        """NEW/... -> ACKNOWLEDGED (analyst has seen the alert)."""
        return self.set_status(alert_id, Status.ACKNOWLEDGED.value, note)

    def resolve(self, alert_id: str, note: str = "") -> Alert | None:
        """... -> RESOLVED (incident handled; terminal state)."""
        return self.set_status(alert_id, Status.RESOLVED.value, note)

    def mark_false_positive(self, alert_id: str, note: str = "") -> Alert | None:
        """... -> FALSE_POSITIVE (feeds detection-rule tuning; terminal state)."""
        return self.set_status(alert_id, Status.FALSE_POSITIVE.value, note)

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
        """Aggregate counts for the dashboard (includes rejected events)."""
        by_severity = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        by_status: dict[str, int] = {}
        for a in self.alerts:
            by_severity[a.severity.value] += 1
            by_status[a.status.value] = by_status.get(a.status.value, 0) + 1
        return {"total": len(self.alerts), "by_severity": by_severity,
                "by_status": by_status, "rejected": len(self.rejected_events)}

    # ---------- persistence ----------

    def save(self) -> None:
        """Explicitly flush history to disk (no-op without history_path)."""
        self._persist()

    def _load(self) -> None:
        """Load history from disk at startup. Corrupt file -> fresh start."""
        try:
            data = load_alerts_json(self._history_path)   # [] when file missing
        except (ValueError, OSError) as exc:
            self.persistence_errors.append(f"could not load history ({exc}); starting fresh")
            return
        for d in data:
            try:
                alert = Alert.from_dict(d)
            except (KeyError, ValueError, TypeError) as exc:
                self.persistence_errors.append(f"skipped corrupt alert record: {exc}")
                continue
            self.alerts.append(alert)
            self._by_id[alert.alert_id] = alert
            self._active[(alert.can_id, alert.source_rule)] = alert  # last (newest) wins

    def _persist(self) -> None:
        """Write full history (oldest first) after every change."""
        if self._history_path is None:
            return
        try:
            save_alerts_json([a.to_dict() for a in self.alerts], self._history_path)
        except OSError as exc:
            self.persistence_errors.append(f"could not save history ({exc})")

    # ---------- internals ----------

    def _within_window(self, earlier: str, later: str) -> bool:
        """True when 'later' falls within dedupe_window_seconds of 'earlier'."""
        try:
            t1 = datetime.fromisoformat(earlier.replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(later.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return True  # defense in depth: prefer folding over spamming
        return (t2 - t1).total_seconds() <= self.dedupe_window_seconds
