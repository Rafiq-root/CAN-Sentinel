"""Tests for the M3 -> M4 dashboard feed (alerts/dashboard_feed.py)."""
from alerts.adapters.from_m2 import ingest_rows
from alerts.dashboard_feed import dashboard_payload
from alerts.manager import AlertManager


def _ev(can_id, rule, ts):
    return {"can_id": can_id, "rule": rule, "timestamp": ts}


def test_empty_manager_gives_zeroed_payload():
    p = dashboard_payload(AlertManager())
    assert p["summary"]["total_alerts"] == 0
    assert p["summary"]["by_severity"] == {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    assert p["summary"]["rejected_events"] == 0
    assert p["recent"] == []
    assert p["critical_active"] == []
    assert p["generated_at"].endswith("Z")


def test_summary_counts_by_severity():
    m = AlertManager()
    m.process_event(_ev("0x123", "SPOOFED_ID", "2026-10-23T10:00:00Z"))
    m.process_event(_ev("0x124", "UNKNOWN_ID", "2026-10-23T10:01:00Z"))
    m.process_event(_ev("0x125", "MALFORMED_FRAME", "2026-10-23T10:02:00Z"))
    s = dashboard_payload(m)["summary"]
    assert s["by_severity"] == {"HIGH": 1, "MEDIUM": 1, "LOW": 1}
    assert s["total_alerts"] == 3


def test_summary_counts_by_status():
    m = AlertManager()
    for cid in ("0x123", "0x124", "0x125"):
        m.process_event(_ev(cid, "UNKNOWN_ID", "2026-10-23T10:00:00Z"))
    s = dashboard_payload(m)["summary"]
    assert s["by_status"] == {"NEW": 3, "ACKNOWLEDGED": 0,
                              "RESOLVED": 0, "FALSE_POSITIVE": 0}
    assert s["active_alerts"] == 3


def test_recent_rows_flat_and_newest_first():
    m = AlertManager()
    for i, cid in enumerate(("0x201", "0x202", "0x203")):
        m.process_event(_ev(cid, "UNKNOWN_ID", "2026-10-23T10:0%d:00Z" % i))
    p = dashboard_payload(m, recent_limit=2)
    assert len(p["recent"]) == 2
    row = p["recent"][0]
    assert row["can_id"] == "0x203"          # newest first
    for key in ("alert_id", "timestamp", "can_id", "rule", "severity",
                "status", "occurrences", "first_seen", "last_seen", "reason"):
        assert key in row
    assert row["severity"] == "MEDIUM"
    assert isinstance(row["occurrences"], int)


def test_rule_column_uses_source_rule():
    m = AlertManager()
    m.process_event(_ev("0x123", "SPOOFED_ID", "2026-10-23T10:00:00Z"))
    assert dashboard_payload(m)["recent"][0]["rule"] == "SPOOFED_ID"


def test_critical_active_surfaces_brake_alert():
    m = AlertManager()
    m.process_event(_ev("0x000", "SPOOFED_ID", "2026-10-23T10:00:00Z"))   # brake
    m.process_event(_ev("0x123", "SPOOFED_ID", "2026-10-23T10:01:00Z"))   # ordinary
    p = dashboard_payload(m)
    assert [r["can_id"] for r in p["critical_active"]] == ["0x000"]
    assert p["recent"][0]["can_id"] == "0x123"   # ordinary still in recent


def test_resolved_critical_leaves_triage_panel():
    m = AlertManager()
    m.process_event(_ev("0x0D2", "SPOOFED_ID", "2026-10-23T10:00:00Z"))   # airbag
    aid = m.get_alerts()[0]["alert_id"]
    m.resolve(aid)
    p = dashboard_payload(m)
    assert p["critical_active"] == []
    assert p["summary"]["total_alerts"] == 1        # still counted overall
    assert p["summary"]["active_alerts"] == 0
    assert p["recent"][0]["status"] == "RESOLVED"


def test_rejected_events_counted_in_summary():
    m = AlertManager()
    m.process_event({"can_id": 291, "rule": "UNKNOWN_ID"})   # int id -> rejected
    s = dashboard_payload(m)["summary"]
    assert s["rejected_events"] == 1
    assert s["total_alerts"] == 0


def test_full_chain_m2_engine_to_dashboard_payload():
    m = AlertManager()
    rows = [
        {"timestamp": 1760000000.0 + i, "can_id": 291, "dlc": 8,
         "data_bytes": [1, 2, 3, 4, 5, 6, 7, 8], "label": "dos",
         "is_alert": True, "severity": "high",
         "reasons": "CAN_ID_RATE_EXCEEDED"}
        for i in range(3)
    ]
    ingest_rows(m, rows)
    p = dashboard_payload(m)
    assert p["summary"]["total_alerts"] == 1          # deduped folds
    assert p["summary"]["by_severity"]["HIGH"] == 1
    assert p["recent"][0]["occurrences"] == 3
    assert p["recent"][0]["rule"] == "HIGH_FREQUENCY"
