"""Frozen M3 -> M4 contract: the dashboard_payload() v2 schema.

This file IS the contract between member-3 (alerts) and member-4 (dashboard).
Every key the dashboard may read is pinned here by exact set, so a shape
change fails the test suite instead of the dashboard. If a change is ever
intentional, member-3 announces it and this file moves with it.

Companions:
  alerts/samples/dashboard_payload_v2_example.json  committed example payload
  docs/m3-m4-contract.md                            one-page wiring note
"""
import json
from pathlib import Path

from alerts.dashboard_feed import dashboard_payload
from alerts.generate_dashboard_example import build_example_manager
from alerts.manager import AlertManager

TOP_LEVEL_KEYS = {"generated_at", "summary", "critical_active", "recent"}
SUMMARY_KEYS = {"total_alerts", "active_alerts", "by_severity",
                "by_status", "rejected_events"}
SEVERITY_KEYS = {"HIGH", "MEDIUM", "LOW"}
STATUS_KEYS = {"NEW", "ACKNOWLEDGED", "RESOLVED", "FALSE_POSITIVE"}
RECENT_ROW_KEYS = {"alert_id", "timestamp", "can_id", "rule", "severity",
                   "status", "occurrences", "first_seen", "last_seen", "reason"}
PANEL_ROW_KEYS = {"can_id", "alert_count", "total_occurrences",
                  "highest_severity", "top_rule", "first_seen", "last_seen"}

FIXTURE = (Path(__file__).resolve().parents[1] / "samples"
           / "dashboard_payload_v2_example.json")


def _assert_int_block(block, key_set):
    assert set(block) == key_set
    assert all(isinstance(v, int) for v in block.values()), block


def test_top_level_shape_is_frozen():
    p = dashboard_payload(build_example_manager())
    assert set(p) == TOP_LEVEL_KEYS
    assert isinstance(p["generated_at"], str) and p["generated_at"].endswith("Z")
    assert isinstance(p["summary"], dict)
    assert isinstance(p["critical_active"], list)
    assert isinstance(p["recent"], list)


def test_summary_block_shape_is_frozen():
    s = dashboard_payload(build_example_manager())["summary"]
    assert set(s) == SUMMARY_KEYS
    for k in ("total_alerts", "active_alerts", "rejected_events"):
        assert isinstance(s[k], int)
    _assert_int_block(s["by_severity"], SEVERITY_KEYS)
    _assert_int_block(s["by_status"], STATUS_KEYS)


def test_recent_row_keys_are_frozen():
    recent = dashboard_payload(build_example_manager())["recent"]
    assert recent, "example scenario must produce alert rows"
    for row in recent:
        assert set(row) == RECENT_ROW_KEYS
    # types pinned only where behavior tests already prove them;
    # alert_id/reason stay opaque to the dashboard
    assert isinstance(recent[0]["occurrences"], int)
    assert recent[0]["severity"] in SEVERITY_KEYS
    assert recent[0]["status"] in STATUS_KEYS


def test_panel_row_keys_are_frozen():
    panel = dashboard_payload(build_example_manager())["critical_active"]
    assert panel, "example scenario must include at least one critical system"
    for row in panel:
        assert set(row) == PANEL_ROW_KEYS
        assert isinstance(row["alert_count"], int)
        assert isinstance(row["total_occurrences"], int)
        assert row["highest_severity"] in SEVERITY_KEYS


def test_empty_manager_keeps_every_key():
    p = dashboard_payload(AlertManager())
    assert set(p) == TOP_LEVEL_KEYS                  # empty state renders too
    assert set(p["summary"]) == SUMMARY_KEYS
    assert p["critical_active"] == [] and p["recent"] == []


def test_payload_survives_a_json_round_trip():
    p = dashboard_payload(build_example_manager())
    assert json.loads(json.dumps(p)) == p            # wire format == payload


def test_example_scenario_folds_and_rejects():
    p = dashboard_payload(build_example_manager())
    assert p["summary"]["rejected_events"] == 1      # int can_id rejected
    dos = [r for r in p["recent"] if r["can_id"] == "0x000"]
    assert dos and dos[0]["occurrences"] == 10       # burst folded to 1 alert


def test_committed_fixture_keeps_the_contract():
    p = json.loads(FIXTURE.read_text())
    assert set(p) == TOP_LEVEL_KEYS
    assert set(p["summary"]) == SUMMARY_KEYS
    assert set(p["summary"]["by_severity"]) == SEVERITY_KEYS
    assert set(p["summary"]["by_status"]) == STATUS_KEYS
    assert p["recent"] and set(p["recent"][0]) == RECENT_ROW_KEYS
    for row in p["critical_active"]:
        assert set(row) == PANEL_ROW_KEYS
