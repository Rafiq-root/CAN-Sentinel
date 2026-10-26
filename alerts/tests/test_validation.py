"""Tests for boundary input validation (Member 3).

Proves the documented hardening rule: invalid events are rejected and
logged, never crash the pipeline, and valid events keep flowing.
"""
import json
from pathlib import Path

from alerts.manager import AlertManager
from alerts.validation import validate_event

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
VALID = {"event_id": "v1", "timestamp": "2026-10-14T09:00:00Z",
         "can_id": "0x1A4", "rule": "HIGH_FREQUENCY", "reason": "ok", "details": {}}


def test_valid_event_passes():
    ok, err = validate_event(VALID)
    assert ok and err == ""


def test_non_dict_rejected():
    for bad in (None, "event", 42, [VALID]):
        ok, _ = validate_event(bad)
        assert not ok


def test_missing_can_id_rejected():
    ok, _ = validate_event({k: v for k, v in VALID.items() if k != "can_id"})
    assert not ok


def test_invalid_hex_can_id_rejected():
    for bad_id in ("0xZZZ", "banana", "0x1G4", ""):
        ok, _ = validate_event({**VALID, "can_id": bad_id})
        assert not ok, bad_id


def test_int_can_id_rejected():
    # contract says hex STRING - an int 420 would be read as hex 0x420, ambiguous
    ok, _ = validate_event({**VALID, "can_id": 420})
    assert not ok


def test_can_id_out_of_11bit_range_rejected():
    ok, _ = validate_event({**VALID, "can_id": "0x800"})    # one above max 0x7FF
    assert not ok


def test_can_id_boundary_7ff_accepted():
    ok, _ = validate_event({**VALID, "can_id": "0x7FF"})
    assert ok


def test_missing_or_empty_rule_rejected():
    assert not validate_event({k: v for k, v in VALID.items() if k != "rule"})[0]
    assert not validate_event({**VALID, "rule": "   "})[0]


def test_unknown_rule_name_is_valid():
    # unknown rule names are NOT invalid - they default to MEDIUM severity
    ok, _ = validate_event({**VALID, "rule": "NEW_RULE_FROM_MEMBER_2"})
    assert ok


def test_bad_timestamp_rejected():
    for bad_ts in ("not-a-time", "2026-13-45T99:99:99Z", 12345):
        ok, _ = validate_event({**VALID, "timestamp": bad_ts})
        assert not ok, bad_ts


def test_non_dict_details_rejected():
    ok, _ = validate_event({**VALID, "details": "payload"})
    assert not ok


def test_manager_rejects_and_continues():
    m = AlertManager()
    assert m.process_event({"junk": True}) is None          # rejected -> None
    assert "can_id" in m.rejected_events[0]["reason"]       # rejection logged
    a = m.process_event(VALID)                              # pipeline keeps working
    assert a is not None and a.can_id == "0x1A4"
    assert len(m.alerts) == 1


def test_stats_includes_rejected_count():
    m = AlertManager()
    m.process_event({"junk": True})
    m.process_event(VALID)
    assert m.stats()["rejected"] == 1


def test_all_sample_events_are_valid():
    # every sample we ship must pass the boundary - keeps docs and code honest
    events = json.loads((SAMPLES / "sample_detection_events.json").read_text())
    for e in events:
        ok, err = validate_event(e)
        assert ok, f"{e.get('event_id')}: {err}"
