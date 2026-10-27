"""One-command demo of the M3 alert pipeline (mid-review live run).

    python3 -m alerts.demo

Shows every core behaviour end to end: DoS dedupe folding, critical-ID
severity escalation, reject-and-log validation, forward-only lifecycle,
stats, and the render-ready M4 dashboard payload.
"""
import json

from .dashboard_feed import dashboard_payload
from .manager import AlertManager

TS = "2026-10-27T10:00:%02dZ"


def run_demo():
    m = AlertManager()
    report = []

    # [1] DoS flood: 10 events on the brake ID inside the 10s dedupe window
    for i in range(10):
        m.process_event({"can_id": "0x000", "rule": "HIGH_FREQUENCY",
                         "timestamp": TS % i})
    dos = next(a for a in m.get_alerts() if a["can_id"] == "0x000")
    report.append("[1] DoS flood       : 10 events on 0x000 (brake) within 10s")
    report.append("    -> 1 alert, severity %s, occurrences=%d (dedupe folding)"
                  % (dos["severity"], dos["occurrences"]))

    # [2] Critical-ID escalation: UNKNOWN_ID is MEDIUM, airbag 0x0D2 is not
    m.process_event({"can_id": "0x0D2", "rule": "UNKNOWN_ID",
                     "timestamp": "2026-10-27T10:01:00Z"})
    airbag = next(a for a in m.get_alerts() if a["can_id"] == "0x0D2")
    report.append("[2] Critical-ID     : airbag 0x0D2 + UNKNOWN_ID (normally MEDIUM)")
    report.append("    -> severity %s (CRITICAL_CAN_IDS escalation - M3 owns severity)"
                  % airbag["severity"])

    # [3] Reject-and-log: int can_id violates the hex-string contract
    m.process_event({"can_id": 291, "rule": "UNKNOWN_ID"})
    report.append("[3] Reject-and-log  : event with int can_id=291")
    report.append("    -> rejected=%d, pipeline alive, alerts unaffected"
                  % len(m.rejected_events))

    # [4] Lifecycle: acknowledge the DoS alert, resolve the airbag alert
    m.acknowledge(dos["alert_id"])
    m.resolve(airbag["alert_id"])
    report.append("[4] Lifecycle       : DoS alert ACKNOWLEDGED, airbag alert RESOLVED")
    report.append("    -> forward-only transitions, audit trail in status_history")

    # [5] Totals
    report.append("[5] Totals          : alerts=%d, rejected=%d"
                  % (len(m.get_alerts()), len(m.rejected_events)))

    # [6] The M4 dashboard feed, exactly what Member 4 renders
    payload = dashboard_payload(m)
    report.append("[6] Dashboard payload (M4 feed - dashboard_feed.py):")
    report.append(json.dumps(payload, indent=2))

    text = "\n".join(report)
    print(text)
    return text


if __name__ == "__main__":
    run_demo()
