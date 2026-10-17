"""Tests for the alert status lifecycle (Member 3).

Proves the documented rules: forward-only transitions, terminal states,
audit-trail recording, and graceful rejection of illegal transitions.
"""
from alerts.manager import AlertManager
from alerts.schema import Status
from alerts.storage import CSV_COLUMNS


def _mgr_with_alert():
    m = AlertManager()
    a = m.process_event({"event_id": "e1", "timestamp": "2026-10-17T09:00:00Z",
                         "can_id": "0x7FF", "rule": "UNKNOWN_ID", "reason": "test", "details": {}})
    return m, a


def test_new_alert_starts_new():
    _, a = _mgr_with_alert()
    assert a.status is Status.NEW
    assert a.status_history == []


def test_full_lifecycle_new_ack_resolved():
    m, a = _mgr_with_alert()
    assert m.acknowledge(a.alert_id).status is Status.ACKNOWLEDGED
    assert m.resolve(a.alert_id).status is Status.RESOLVED
    assert len(a.status_history) == 2


def test_false_positive_from_new():
    m, a = _mgr_with_alert()
    assert m.mark_false_positive(a.alert_id).status is Status.FALSE_POSITIVE


def test_resolved_is_terminal():
    m, a = _mgr_with_alert()
    m.acknowledge(a.alert_id)
    m.resolve(a.alert_id)
    assert m.set_status(a.alert_id, "NEW") is None
    assert "invalid transition" in m.last_error
    assert m.acknowledge(a.alert_id) is None


def test_acknowledged_cannot_return_to_new():
    m, a = _mgr_with_alert()
    m.acknowledge(a.alert_id)
    assert m.set_status(a.alert_id, "NEW") is None
    assert "invalid transition" in m.last_error


def test_same_status_is_rejected():
    m, a = _mgr_with_alert()
    assert m.set_status(a.alert_id, "NEW") is None      # NEW -> NEW is a no-op


def test_unknown_alert_id():
    m, _ = _mgr_with_alert()
    assert m.acknowledge("ALR-19990101-NOPE00") is None
    assert "unknown alert_id" in m.last_error


def test_invalid_status_name():
    m, a = _mgr_with_alert()
    assert m.set_status(a.alert_id, "DISMISSED") is None
    assert "invalid status" in m.last_error


def test_status_history_records_note_and_timestamp():
    m, a = _mgr_with_alert()
    m.acknowledge(a.alert_id, note="investigating")
    entry = a.status_history[-1]
    assert entry["status"] == "ACKNOWLEDGED"
    assert entry["note"] == "investigating"
    assert entry["at"]


def test_stats_reflects_status_changes():
    m, a = _mgr_with_alert()
    m.resolve(a.alert_id)
    assert m.stats()["by_status"] == {"RESOLVED": 1}


def test_history_in_json_dict_but_not_csv_columns():
    m, a = _mgr_with_alert()
    m.acknowledge(a.alert_id, note="checked")
    d = m.get_alerts()[0]
    assert d["status"] == "ACKNOWLEDGED"
    assert d["status_history"][0]["note"] == "checked"
    assert "status_history" not in CSV_COLUMNS
