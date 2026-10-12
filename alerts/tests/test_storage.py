"""Tests for alert history storage (Member 3)."""
import csv as csv_mod

from alerts.manager import AlertManager
from alerts.storage import CSV_COLUMNS, export_alerts_csv, load_alerts_json, save_alerts_json


def _sample_alerts():
    m = AlertManager()
    m.process_event({"event_id": "e1", "timestamp": "2026-10-12T10:00:00Z",
                     "can_id": "0x7FF", "rule": "UNKNOWN_ID", "reason": "not in allowlist", "details": {}})
    m.process_event({"event_id": "e2", "timestamp": "2026-10-12T10:00:03Z",
                     "can_id": "0x7FF", "rule": "UNKNOWN_ID", "reason": "not in allowlist", "details": {}})  # folds
    m.process_event({"event_id": "e3", "timestamp": "2026-10-12T10:00:05Z",
                     "can_id": "0x1A4", "rule": "HIGH_FREQUENCY", "reason": "flooding", "details": {}})
    return m.get_alerts()


def test_json_round_trip(tmp_path):
    alerts = _sample_alerts()
    p = tmp_path / "history.json"
    save_alerts_json(alerts, p)
    assert load_alerts_json(p) == alerts


def test_load_missing_file_returns_empty(tmp_path):
    assert load_alerts_json(tmp_path / "does-not-exist.json") == []


def test_csv_export_shape(tmp_path):
    alerts = _sample_alerts()
    p = tmp_path / "history.csv"
    export_alerts_csv(alerts, p)
    with p.open() as f:
        reader = csv_mod.DictReader(f)
        rows = list(reader)
    assert reader.fieldnames == CSV_COLUMNS
    assert len(rows) == 2          # duplicate folded -> 2 alerts from 3 events
    assert {r["severity"] for r in rows} == {"MEDIUM", "HIGH"}
