"""Regenerate the committed M3 -> M4 example payload.

Writes alerts/samples/dashboard_payload_v2_example.json from a fixed
scenario so member-4 can develop the dashboard against a real payload
without running the detection pipeline:

    python -m alerts.generate_dashboard_example
"""
import json
from pathlib import Path

from alerts.dashboard_feed import dashboard_payload
from alerts.manager import AlertManager

FIXTURE = (Path(__file__).resolve().parent / "samples"
           / "dashboard_payload_v2_example.json")


def build_example_manager():
    """Fixed scenario: DoS burst + HIGH/MEDIUM/LOW singles + rejection + resolve."""
    m = AlertManager()
    for i in range(10):                                   # DoS burst -> 1 folded alert
        m.process_event({"can_id": "0x000", "rule": "HIGH_FREQUENCY",
                         "timestamp": "2026-11-03T09:30:%02dZ" % i})
    m.process_event({"can_id": "0x123", "rule": "SPOOFED_ID",
                     "timestamp": "2026-11-03T09:31:00Z"})
    m.process_event({"can_id": "0x201", "rule": "UNKNOWN_ID",
                     "timestamp": "2026-11-03T09:32:00Z"})
    m.process_event({"can_id": "0x301", "rule": "MALFORMED_FRAME",
                     "timestamp": "2026-11-03T09:33:00Z"})
    m.process_event({"can_id": 291, "rule": "UNKNOWN_ID"})   # int id -> rejected
    resolved = [a for a in m.get_alerts() if a["can_id"] == "0x201"][0]
    m.resolve(resolved["alert_id"])                     # show a RESOLVED row
    return m


def main():
    payload = dashboard_payload(build_example_manager())
    FIXTURE.write_text(json.dumps(payload, indent=2) + "\n")
    print("wrote %s" % FIXTURE)
    print("summary: %s" % json.dumps(payload["summary"]))
    print("panel: %s" % json.dumps(payload["critical_active"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
