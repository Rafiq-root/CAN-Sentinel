"""
CAN-Sentinel - Severity Rules (Member 3)

Maps detection events (from Member 2) to alert severities.

DOCUMENTED SEVERITY MODEL:
  HIGH   - Attacks on safety-critical systems (brakes/steering/engine/airbag),
           or message flooding / ID spoofing at abnormal rates.
  MEDIUM - Unknown CAN IDs outside the allowlist, abnormal message timing.
  LOW    - Malformed frames (bad DLC), isolated/cosmetic anomalies.

ESCALATION RULE: any event affecting a safety-critical CAN ID is
escalated to HIGH, regardless of its base rule severity.
"""

from .schema import Severity

# Safety-critical CAN IDs for our mock vehicle. Extend together with
# Member 1 once the shared CAN ID map is finalised.
CRITICAL_CAN_IDS = {
    "0x000",   # brake control (mock)
    "0x1A4",   # steering angle (mock)
    "0x0C8",   # engine RPM (mock)
    "0x0D2",   # airbag status (mock)
}

# Detection rule name (from Member 2) -> base severity.
# Keep these rule names in sync with the detection engine.
RULE_TO_SEVERITY = {
    "HIGH_FREQUENCY":   Severity.HIGH,    # message flooding / spoofing at high rate
    "SPOOFED_ID":       Severity.HIGH,    # known ID transmitted by unexpected source
    "UNKNOWN_ID":       Severity.MEDIUM,  # CAN ID outside the configured allowlist
    "ABNORMAL_TIMING":  Severity.MEDIUM,  # inter-arrival timing deviates from baseline
    "ABNORMAL_ENTROPY": Severity.MEDIUM,  # payload entropy deviates from baseline
    "MALFORMED_FRAME":  Severity.LOW,     # bad DLC / invalid field values
}


def canonical_can_id(can_id: str) -> str:
    """Normalise CAN ID strings to one form: '1a4' -> '0x1A4'."""
    can_id = str(can_id).strip()
    return f"0x{int(can_id, 16):03X}" if can_id else ""


def classify(event: dict) -> tuple[Severity, str]:
    """Return (severity, category) for one detection event.

    Escalates to HIGH when the affected CAN ID is safety-critical.
    """
    rule = str(event.get("rule", "UNKNOWN")).upper()
    severity = RULE_TO_SEVERITY.get(rule, Severity.MEDIUM)  # unknown rules default to MEDIUM

    can_id = canonical_can_id(event.get("can_id", ""))
    if can_id in CRITICAL_CAN_IDS:
        severity = Severity.HIGH

    category = rule.lower()  # e.g. HIGH_FREQUENCY -> "high_frequency"
    return severity, category
