"""M3 analyst session report: AlertManager state -> markdown report.

    python3 -m alerts.report [history.json]

Complements the machine formats in storage.py (JSON for tools, CSV for
spreadsheets) with the format a human reads: totals, severity and
lifecycle breakdowns, the critical-ID triage list, top offending CAN
IDs, and the most recent alerts. Works on any manager - live, or
reloaded from persisted history.
"""

from __future__ import annotations

import os
import sys
from collections import Counter

from .dashboard_feed import dashboard_payload
from .manager import AlertManager

_DEFAULT_HISTORY = "alerts/samples/sample_alerts.json"


def build_report(manager, title="CAN-Sentinel Alert Session Report",
                 top_n=5, recent_n=10):
    """Render an analyst-facing markdown report of the alert session."""
    payload = dashboard_payload(manager)
    summary = payload["summary"]
    severity = summary["by_severity"]
    status = summary["by_status"]
    alerts = manager.get_alerts()

    lines = [
        "# " + title,
        "",
        "Generated: %s" % payload["generated_at"],
        "",
        "## Summary",
        "",
        "- Total alerts: %d (active: %d)"
        % (summary["total_alerts"], summary["active_alerts"]),
        "- Severity: HIGH %d / MEDIUM %d / LOW %d"
        % (severity["HIGH"], severity["MEDIUM"], severity["LOW"]),
        "- Lifecycle: NEW %d / ACKNOWLEDGED %d / RESOLVED %d / FALSE_POSITIVE %d"
        % (status["NEW"], status["ACKNOWLEDGED"],
           status["RESOLVED"], status["FALSE_POSITIVE"]),
        "- Rejected events: %d (invalid input logged, pipeline unaffected)"
        % summary["rejected_events"],
        "",
        "## Critical IDs - active (triage list)",
        "",
    ]

    if payload["critical_active"]:
        for row in payload["critical_active"]:
            lines.append("- %s  rule=%s  severity=%s  status=%s  occurrences=%d"
                         % (row["can_id"], row["rule"], row["severity"],
                            row["status"], row["occurrences"]))
    else:
        lines.append("- none")

    lines += ["", "## Top offending CAN IDs", ""]
    if alerts:
        for can_id, count in Counter(
                a["can_id"] for a in alerts).most_common(top_n):
            lines.append("- %s: %d alert(s)" % (can_id, count))
    else:
        lines.append("- none")

    lines += ["", "## Most recent alerts", ""]
    if payload["recent"]:
        for row in payload["recent"][:recent_n]:
            lines.append("- %s  %s  %s  %s  %s"
                         % (row["timestamp"], row["can_id"], row["rule"],
                            row["severity"], row["status"]))
    else:
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    path = argv[0] if argv else _DEFAULT_HISTORY
    if not os.path.exists(path):
        print("usage: python3 -m alerts.report [alerts_history.json]")
        return 1
    try:
        manager = AlertManager(history_path=path)
    except (OSError, ValueError) as exc:
        print("could not load history file %s: %s" % (path, exc))
        return 1
    print(build_report(manager))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
