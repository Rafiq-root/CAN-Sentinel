"""Tests for AlertManager duplicate folding and queries (Member 3)."""
from alerts.manager import AlertManager
from alerts.schema import Severity


def _ev(rule, can_id, ts):
    return {"event_id": "x", "timestamp": ts, "can_id": can_id,
            "rule": rule, "reason": "test event", "details": {}}


def test_single_event_creates_one_alert():
    m = AlertManager()
    a = m.process_event(_ev("UNKNOWN_ID", "0x7FF", "2026-10-12T10:00:00Z"))
    assert a.occurrences == 1
    assert a.severity is Severity.MEDIUM
    assert len(m.alerts) == 1


def test_duplicates_within_window_fold():
    m = AlertManager(dedupe_window_seconds=10)
    a1 = m.process_event(_ev("UNKNOWN_ID", "0x7FF", "2026-10-12T10:00:00Z"))
    a2 = m.process_event(_ev("UNKNOWN_ID", "0x7FF", "2026-10-12T10:00:05Z"))
    assert a1.alert_id == a2.alert_id
    assert a2.occurrences == 2
    assert a2.last_seen == "2026-10-12T10:00:05Z"
    assert len(m.alerts) == 1


def test_after_window_new_alert():
    m = AlertManager(dedupe_window_seconds=10)
    m.process_event(_ev("UNKNOWN_ID", "0x7FF", "2026-10-12T10:00:00Z"))
    a2 = m.process_event(_ev("UNKNOWN_ID", "0x7FF", "2026-10-12T10:00:30Z"))
    assert len(m.alerts) == 2
    assert a2.occurrences == 1


def test_different_can_ids_separate_alerts():
    m = AlertManager()
    m.process_event(_ev("UNKNOWN_ID", "0x7FF", "2026-10-12T10:00:00Z"))
    m.process_event(_ev("UNKNOWN_ID", "0x7FE", "2026-10-12T10:00:01Z"))
    assert len(m.alerts) == 2


def test_different_rules_same_can_id_separate_alerts():
    m = AlertManager()
    m.process_event(_ev("UNKNOWN_ID", "0x7FF", "2026-10-12T10:00:00Z"))
    m.process_event(_ev("HIGH_FREQUENCY", "0x7FF", "2026-10-12T10:00:01Z"))
    assert len(m.alerts) == 2


def test_get_alerts_filters_and_order():
    m = AlertManager()
    m.process_event(_ev("UNKNOWN_ID", "0x7FE", "2026-10-12T10:00:00Z"))      # MEDIUM
    m.process_event(_ev("HIGH_FREQUENCY", "0x1A4", "2026-10-12T10:00:01Z"))  # HIGH (critical ID)
    high = m.get_alerts(severity="HIGH")
    assert len(high) == 1 and high[0]["can_id"] == "0x1A4"
    assert m.get_alerts()[0]["can_id"] == "0x1A4"   # newest first
    assert len(m.get_alerts(limit=1)) == 1


def test_stats_counts():
    m = AlertManager()
    m.process_event(_ev("UNKNOWN_ID", "0x7FE", "2026-10-12T10:00:00Z"))      # MEDIUM
    m.process_event(_ev("HIGH_FREQUENCY", "0x1A4", "2026-10-12T10:00:01Z"))  # HIGH
    s = m.stats()
    assert s["total"] == 2
    assert s["by_severity"] == {"LOW": 0, "MEDIUM": 1, "HIGH": 1}
