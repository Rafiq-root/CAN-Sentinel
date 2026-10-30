"""Tests for the M2 -> M3 input adapter (alerts/adapters/from_m2.py)."""
from datetime import datetime

from alerts.adapters.from_m2 import ingest_rows, translate_rows
from alerts.manager import AlertManager


def _row(can_id=291, timestamp=1760000000.0, reasons="UNEXPECTED_CAN_ID",
         is_alert=True, severity="medium", label=None):
    return {
        "timestamp": timestamp,
        "can_id": can_id,
        "dlc": 8,
        "data_bytes": [1, 2, 3, 4, 5, 6, 7, 8],
        "label": label,
        "is_alert": is_alert,
        "severity": severity,
        "reasons": reasons,
    }


def _sev(alert):
    return alert["severity"]


def _iso_to_epoch(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def test_clean_rows_produce_no_events():
    events, rejected = translate_rows([_row(is_alert=False, reasons="")])
    assert events == []
    assert rejected == []


def test_reasons_without_alert_flag_are_skipped():
    events, _ = translate_rows([_row(is_alert=False, reasons="UNEXPECTED_CAN_ID")])
    assert events == []


def test_alert_flag_without_reasons_is_skipped():
    events, _ = translate_rows([_row(is_alert=True, reasons="")])
    assert events == []


def test_int_can_id_becomes_padded_hex_string():
    events, _ = translate_rows([_row(can_id=291)])
    assert events[0]["can_id"] == "0x123"
    events, _ = translate_rows([_row(can_id=3)])
    assert events[0]["can_id"] == "0x003"


def test_reasons_map_to_m3_rule_vocabulary():
    events, _ = translate_rows([_row(reasons="CAN_ID_RATE_EXCEEDED")])
    assert events[0]["rule"] == "HIGH_FREQUENCY"
    events, _ = translate_rows([_row(reasons="REPEATED_PAYLOAD_PATTERN")])
    assert events[0]["rule"] == "ABNORMAL_ENTROPY"


def test_multiple_reasons_split_into_separate_events():
    row = _row(reasons="CAN_ID_RATE_EXCEEDED;GLOBAL_RATE_EXCEEDED")
    events, _ = translate_rows([row])
    assert len(events) == 2
    assert [e["rule"] for e in events] == ["HIGH_FREQUENCY", "HIGH_FREQUENCY"]


def test_unknown_reason_passes_through_unchanged():
    events, _ = translate_rows([_row(reasons="DATASET_ATTACK_LABEL")])
    assert events[0]["rule"] == "DATASET_ATTACK_LABEL"


def test_timestamp_becomes_iso8601_utc_z():
    events, _ = translate_rows([_row(timestamp=1760000000.0)])
    ts = events[0]["timestamp"]
    assert ts.endswith("Z")
    assert _iso_to_epoch(ts) == 1760000000.0


def test_timestamp_base_offsets_relative_times():
    events, _ = translate_rows([_row(timestamp=5.0)], timestamp_base=1760000000.0)
    assert _iso_to_epoch(events[0]["timestamp"]) == 1760000005.0


def test_details_carry_traceability():
    events, _ = translate_rows([_row(label="spoofing", severity="high")])
    d = events[0]["details"]
    assert d["source"] == "m2_detection_engine"
    assert d["dlc"] == 8
    assert d["data_bytes"] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert d["m2_reasons_raw"] == "UNEXPECTED_CAN_ID"
    assert d["m2_severity"] == "high"
    assert d["dataset_label"] == "spoofing"


def test_malformed_row_is_rejected_with_trace():
    bad = _row()
    del bad["can_id"]
    events, rejected = translate_rows([bad])
    assert events == []
    assert rejected[0]["row_index"] == 0
    assert "error" in rejected[0]


def test_missing_timestamp_is_rejected():
    bad = _row()
    del bad["timestamp"]
    events, rejected = translate_rows([bad])
    assert events == []
    assert len(rejected) == 1


def test_m2_severity_is_not_trusted_m3_reclassifies():
    m = AlertManager()
    ingest_rows(m, [_row(reasons="UNEXPECTED_CAN_ID", severity="high")])
    assert _sev(m.get_alerts()[0]) == "MEDIUM"   # M2 said high; M3 owns severity


def test_rate_exceeded_classifies_high():
    m = AlertManager()
    ingest_rows(m, [_row(reasons="CAN_ID_RATE_EXCEEDED")])
    assert _sev(m.get_alerts()[0]) == "HIGH"


def test_critical_can_id_escalates_beyond_m2_severity():
    m = AlertManager()
    # 0x0D2 airbag: M2 says medium, M3 critical-ID rule says HIGH
    ingest_rows(m, [_row(can_id=0x0D2, reasons="UNEXPECTED_CAN_ID", severity="medium")])
    assert _sev(m.get_alerts()[0]) == "HIGH"


def test_extended_29bit_id_now_accepted():
    # contract widened Oct 30 for the GEM dataset: 29-bit IDs are valid;
    # only values above 0x1FFFFFFF are rejected now
    m = AlertManager()
    fed, row_rej, mgr_rej = ingest_rows(m, [_row(can_id=0x1FFFFFFF)])
    assert (fed, row_rej, mgr_rej) == (1, 0, 0)
    assert len(m.rejected_events) == 0
    assert m.get_alerts()[0]["can_id"] == "0x1FFFFFFF"


def test_ingest_end_to_end_dedupe_folds_repeats():
    m = AlertManager()
    rows = [_row(reasons="CAN_ID_RATE_EXCEEDED") for _ in range(3)]
    fed, row_rej, mgr_rej = ingest_rows(m, rows)
    assert (fed, row_rej, mgr_rej) == (3, 0, 0)
    alerts = m.get_alerts()
    assert len(alerts) == 1
    assert alerts[0]["occurrences"] == 3
