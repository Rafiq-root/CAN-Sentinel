"""Tests for attack-scenario behaviour (Member 3).

Each test loads a scenario from alerts/samples/scenarios/ and asserts the
documented expected AlertManager behaviour under that attack pattern.
"""
import json
from pathlib import Path

from alerts.generate_scenarios import run_scenario

SCENARIOS = Path(__file__).resolve().parents[1] / "samples" / "scenarios"


def _load(name: str) -> dict:
    return json.loads((SCENARIOS / name).read_text())


def test_dos_flood_folds_into_single_high_alert():
    m = run_scenario(_load("dos_flood_brake.json"))
    alerts = m.get_alerts()
    assert len(alerts) == 1                          # storm suppression: 10 events -> 1 alert
    assert alerts[0]["severity"] == "HIGH"           # brake ECU + HIGH_FREQUENCY
    assert alerts[0]["occurrences"] == 10


def test_critical_id_spoofing_escalates_to_high():
    m = run_scenario(_load("spoof_critical_id.json"))
    by_id = {a["can_id"]: a for a in m.get_alerts()}
    assert by_id["0x0D2"]["severity"] == "HIGH"      # airbag: escalated MEDIUM -> HIGH
    assert by_id["0x123"]["severity"] == "MEDIUM"    # non-critical: stays at base


def test_replay_bursts_window_boundary():
    m = run_scenario(_load("replay_burst.json"))
    alerts = m.get_alerts()                          # newest first
    assert len(alerts) == 2
    assert all(a["occurrences"] == 2 for a in alerts)
    assert alerts[1]["last_seen"] < alerts[0]["first_seen"]   # gap exceeded window
