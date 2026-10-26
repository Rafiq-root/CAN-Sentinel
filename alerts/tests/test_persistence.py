"""Tests for auto-persistence (Member 3).

Proves the documented rules: history loads at startup, every change is
written back, restarts lose nothing, dedupe state is rebuilt from disk,
corrupt files never crash the manager, and the no-path mode stays
in-memory (backward compatible).
"""
from alerts.manager import AlertManager


def _ev(ts, can_id="0x7FF", rule="UNKNOWN_ID"):
    return {"event_id": "x", "timestamp": ts, "can_id": can_id,
            "rule": rule, "reason": "test event", "details": {}}


def test_without_history_path_no_file_written(tmp_path):
    m = AlertManager()
    assert m.process_event(_ev("2026-10-18T10:00:00Z")) is not None
    assert list(tmp_path.iterdir()) == []          # nothing written anywhere


def test_persists_on_new_alert(tmp_path):
    p = tmp_path / "h.json"
    m = AlertManager(history_path=p)
    m.process_event(_ev("2026-10-18T10:00:00Z"))
    assert p.exists()
    assert len(m.get_alerts()) == 1


def test_persists_on_duplicate_fold(tmp_path):
    p = tmp_path / "h.json"
    m = AlertManager(history_path=p)
    m.process_event(_ev("2026-10-18T10:00:00Z"))
    m.process_event(_ev("2026-10-18T10:00:05Z"))           # folds
    m2 = AlertManager(history_path=p)
    assert m2.get_alerts()[0]["occurrences"] == 2


def test_persists_on_status_change(tmp_path):
    p = tmp_path / "h.json"
    m = AlertManager(history_path=p)
    a = m.process_event(_ev("2026-10-18T10:00:00Z"))
    m.acknowledge(a.alert_id, note="investigating")
    m2 = AlertManager(history_path=p)
    loaded = m2.get_alerts()[0]
    assert loaded["status"] == "ACKNOWLEDGED"
    assert loaded["status_history"][0]["note"] == "investigating"


def test_reload_restores_full_state(tmp_path):
    p = tmp_path / "h.json"
    m1 = AlertManager(history_path=p)
    a = m1.process_event(_ev("2026-10-18T10:00:00Z"))
    m1.process_event(_ev("2026-10-18T10:00:03Z"))          # folds into a
    b = m1.process_event(_ev("2026-10-18T10:00:05Z", can_id="0x123"))
    m1.resolve(a.alert_id)
    m2 = AlertManager(history_path=p)
    s = m2.stats()
    assert s["total"] == 2 and s["by_status"] == {"RESOLVED": 1, "NEW": 1}
    by_id = {x["alert_id"]: x for x in m2.get_alerts()}
    assert by_id[a.alert_id]["occurrences"] == 2
    assert by_id[b.alert_id]["can_id"] == "0x123"


def test_reload_rebuilds_active_dedupe_map(tmp_path):
    p = tmp_path / "h.json"
    m1 = AlertManager(history_path=p)
    m1.process_event(_ev("2026-10-18T10:00:00Z"))
    m2 = AlertManager(history_path=p)
    a = m2.process_event(_ev("2026-10-18T10:00:05Z"))      # within window of loaded alert
    assert a.occurrences == 2
    assert len(m2.alerts) == 1


def test_corrupt_history_file_starts_fresh(tmp_path):
    p = tmp_path / "h.json"
    p.write_text("{ this is not valid json !!")
    m = AlertManager(history_path=p)
    assert m.alerts == []
    assert m.persistence_errors                     # problem recorded
    assert m.process_event(_ev("2026-10-18T10:00:00Z")) is not None   # pipeline alive
