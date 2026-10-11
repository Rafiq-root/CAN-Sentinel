"""Tests for severity classification rules (Member 3)."""
import json
from pathlib import Path

from alerts.schema import Severity
from alerts.severity_rules import canonical_can_id, classify

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "sample_detection_events.json"


def _events():
    return json.loads(SAMPLES.read_text())


def test_high_frequency_is_high():
    sev, cat = classify(_events()[0])
    assert sev is Severity.HIGH
    assert cat == "high_frequency"


def test_unknown_id_is_medium():
    sev, _ = classify(_events()[1])          # 0x7FF not safety-critical
    assert sev is Severity.MEDIUM


def test_malformed_frame_is_low():
    sev, _ = classify(_events()[2])
    assert sev is Severity.LOW


def test_critical_can_id_escalates_to_high():
    sev, _ = classify(_events()[3])          # UNKNOWN_ID on brakes -> HIGH
    assert sev is Severity.HIGH


def test_canonical_can_id():
    assert canonical_can_id("1a4") == "0x1A4"
    assert canonical_can_id("0x000") == "0x000"
    assert canonical_can_id("0X7ff") == "0x7FF"
