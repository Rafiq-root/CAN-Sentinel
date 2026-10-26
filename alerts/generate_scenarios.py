"""
CAN-Sentinel - Attack Scenario Runner (Member 3).

Runs each detection-event scenario in alerts/samples/scenarios/ through the
AlertManager, writes the resulting alert history (JSON + CSV) next to the
scenario, and prints a summary. Demonstrates module behaviour under three
canonical automotive attacks:

  1. DoS flood         -> alert-storm suppression (one alert, occurrences grow)
  2. Critical-ID spoof -> severity escalation (MEDIUM base -> HIGH)
  3. Replay bursts     -> window-boundary duplicate folding

Usage (from repository root):
    python3 -m alerts.generate_scenarios
"""

import json
from pathlib import Path

from .manager import AlertManager
from .storage import export_alerts_csv, save_alerts_json

SCENARIOS = Path(__file__).resolve().parent / "samples" / "scenarios"


def run_scenario(scenario: dict) -> AlertManager:
    """Process all events of one scenario through a fresh AlertManager."""
    manager = AlertManager()
    for event in scenario["events"]:
        manager.process_event(event)
    return manager


def main() -> None:
    for path in sorted(SCENARIOS.glob("*.json")):
        if path.stem.endswith("_alerts"):    # skip previously generated outputs
            continue
        scenario = json.loads(path.read_text())
        manager = run_scenario(scenario)

        alerts = manager.get_alerts()
        save_alerts_json(alerts, path.with_name(path.stem + "_alerts.json"))
        export_alerts_csv(alerts, path.with_name(path.stem + "_alerts.csv"))

        print(f"[{scenario['name']}]")
        print(f"  events in: {len(scenario['events'])}  ->  alerts out: {len(alerts)}")
        for a in alerts:
            print(f"    {a['can_id']}  {a['severity']:<6} occurrences={a['occurrences']}  ({a['category']})")
        print()
