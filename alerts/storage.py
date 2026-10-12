"""
CAN-Sentinel - Alert History Storage (Member 3)

Persists alert history so it survives restarts and can be consumed by the
dashboard (Member 4). Two formats:

  JSON - full fidelity, machine-readable (primary history store; includes
         raw_details)
  CSV  - flat export for spreadsheets / human review (raw_details is
         dict-valued and therefore kept only in the JSON store)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

CSV_COLUMNS = [
    "alert_id", "timestamp", "can_id", "severity", "category", "reason",
    "status", "occurrences", "first_seen", "last_seen", "source_rule",
]


def save_alerts_json(alerts: list[dict], path) -> None:
    """Write full alert history (list of alert dicts) to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(alerts, indent=2))


def load_alerts_json(path) -> list[dict]:
    """Load alert history from JSON. Missing file -> empty list (fresh start)."""
    path = Path(path)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def export_alerts_csv(alerts: list[dict], path) -> None:
    """Export alerts to CSV with a fixed column order (raw_details excluded)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for alert in alerts:
            writer.writerow(alert)
