"""
CAN-Sentinel - Sample alert log generator (Member 3).

Runs the sample detection events through the AlertManager and writes the
resulting alert history to alerts/samples/ in both JSON and CSV form.
Demonstrates the full M2 -> M3 pipeline; serves as the module's sample-log
deliverable.

Usage (from repository root):
    python3 -m alerts.generate_samples
"""

import json
from pathlib import Path

from .manager import AlertManager
from .storage import export_alerts_csv, save_alerts_json

SAMPLES = Path(__file__).resolve().parent / "samples"


def main() -> None:
    events = json.loads((SAMPLES / "sample_detection_events.json").read_text())
    manager = AlertManager()
    for event in events:
        manager.process_event(event)

    alerts = manager.get_alerts()
    save_alerts_json(alerts, SAMPLES / "sample_alerts.json")
    export_alerts_csv(alerts, SAMPLES / "sample_alerts.csv")

    folded = [a["alert_id"] for a in alerts if a["occurrences"] > 1]
    print(f"Saved {len(alerts)} alerts "
          f"({len(folded)} with folded duplicates) -> alerts/samples/sample_alerts.json / .csv")
    print(f"Stats: {manager.stats()}")


if __name__ == "__main__":
    main()
