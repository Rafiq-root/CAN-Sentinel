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

# Safety-critical CAN IDs, per vehicle profile. The ACTIVE profile decides
# which IDs escalate to HIGH; swap with set_vehicle_critical_map().
#   mock_vehicle - our simulation profile (Weeks 1-2 behaviour, unchanged)
#   gem_e6       - the real GEM e6 platform: the labeled dataset's tampering
#                  targets ARE the safety-critical IDs (PACMod brake/steering)
VEHICLE_CRITICAL_MAPS = {
    "mock_vehicle": {
        "0x000",       # brake control (simulation profile)
        "0x1A4",       # steering angle (simulation profile)
        "0x0C8",       # engine RPM (simulation profile)
        "0x0D2",       # airbag status (simulation profile)
    },
    "gem_e6": {
        "0x18FF00F9",  # PACMod brake control (GEM e6 real-vehicle dataset)
        "0x18FF70F9",  # PACMod steering control (GEM e6 real-vehicle dataset)
    },
}

# The ACTIVE critical set - kept as the SAME object everyone imports:
# set_vehicle_critical_map() mutates it in place, so every existing import
# (classify, dashboard_feed, tests) sees the swap immediately.
CRITICAL_CAN_IDS = set(VEHICLE_CRITICAL_MAPS["mock_vehicle"])


def set_vehicle_critical_map(name: str) -> None:
    """Activate a vehicle profile's critical-ID set (in place).

    Unknown profile -> ValueError: a misconfigured vehicle name is a
    programmer error, not pipeline input - the one place we fail LOUD.
    """
    if name not in VEHICLE_CRITICAL_MAPS:
        raise ValueError("unknown vehicle profile %r - available: %s"
                         % (name, ", ".join(sorted(VEHICLE_CRITICAL_MAPS))))
    CRITICAL_CAN_IDS.clear()
    CRITICAL_CAN_IDS.update(VEHICLE_CRITICAL_MAPS[name])

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
