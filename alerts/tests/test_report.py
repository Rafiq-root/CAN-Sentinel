"""Tests for the analyst session report (alerts/report.py)."""
from alerts.manager import AlertManager
from alerts.report import build_report


def _ev(can_id, rule, ts):
    return {"can_id": can_id, "rule": rule, "timestamp": ts}


def test_report_shows_summary_counts():
    m = AlertManager()
    m.process_event(_ev("0x123", "SPOOFED_ID", "2026-10-28T10:00:00Z"))
    m.process_event(_ev("0x124", "UNKNOWN_ID", "2026-10-28T10:01:00Z"))
    r = build_report(m)
    assert "Total alerts: 2 (active: 2)" in r
    assert "Severity: HIGH 1 / MEDIUM 1 / LOW 0" in r
    assert "Rejected events: 0" in r


def test_report_counts_rejected_events():
    m = AlertManager()
    m.process_event({"can_id": 291, "rule": "UNKNOWN_ID"})   # int -> rejected
    r = build_report(m)
    assert "Rejected events: 1" in r
    assert "Total alerts: 0" in r


def test_report_top_offending_can_ids_ordered():
    m = AlertManager()
    for rule in ("SPOOFED_ID", "UNKNOWN_ID", "HIGH_FREQUENCY"):
        m.process_event(_ev("0x123", rule, "2026-10-28T10:00:00Z"))
    m.process_event(_ev("0x124", "UNKNOWN_ID", "2026-10-28T10:01:00Z"))
    r = build_report(m)
    assert "0x123: 3 alert(s)" in r
    assert "0x124: 1 alert(s)" in r
    assert r.index("0x123") < r.index("0x124")     # worst offender listed first


def test_report_triage_lists_active_critical():
    m = AlertManager()
    m.process_event(_ev("0x000", "HIGH_FREQUENCY", "2026-10-28T10:00:00Z"))
    r = build_report(m)
    triage = r.split("Critical IDs")[1].split("##")[0]
    assert "0x000" in triage
    assert "occurrences=1" in triage


def test_report_resolved_critical_leaves_triage():
    m = AlertManager()
    m.process_event(_ev("0x0D2", "UNKNOWN_ID", "2026-10-28T10:00:00Z"))
    m.resolve(m.get_alerts()[0]["alert_id"])
    r = build_report(m)
    triage = r.split("Critical IDs")[1].split("##")[0]
    assert "none" in triage


def test_report_recent_section_newest_first():
    m = AlertManager()
    m.process_event(_ev("0x201", "UNKNOWN_ID", "2026-10-28T10:00:00Z"))
    m.process_event(_ev("0x202", "UNKNOWN_ID", "2026-10-28T10:05:00Z"))
    r = build_report(m)
    recent = r.split("Most recent alerts")[1]
    assert recent.index("0x202") < recent.index("0x201")


def test_report_reads_persisted_history(tmp_path):
    hist = tmp_path / "history.json"
    m = AlertManager(history_path=str(hist))
    m.process_event(_ev("0x1A4", "SPOOFED_ID", "2026-10-28T10:00:00Z"))
    reloaded = AlertManager(history_path=str(hist))   # auto-persistence
    r = build_report(reloaded)
    assert "Total alerts: 1" in r
    assert "0x1A4" in r
