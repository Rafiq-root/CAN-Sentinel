"""
CAN-Sentinel - Input Validation (Member 3)

Boundary validation for detection events entering the alert pipeline.
Rule: nothing crosses into the AlertManager without passing validate_event().

DOCUMENTED VALIDATION RULES:
  1. event    - must be a dict
  2. can_id   - required; hex STRING (e.g. '0x1A4'); standard 11-bit range
                0x000-0x7FF (set CAN_ID_MAX to 0x1FFFFFFF for 29-bit extended)
  3. rule     - required; non-empty string. Unknown rule NAMES are accepted -
                they default to MEDIUM severity (see severity_rules.py) - only
                a missing/empty rule is invalid.
  4. timestamp- optional; if present, must be a parseable ISO-8601 string
  5. reason   - optional; if present, must be a string
  6. details  - optional; if present, must be a dict

Rejections are RETURNED, never raised: one malformed event must not crash
the alerting pipeline - especially during an active attack.
"""

from __future__ import annotations

from datetime import datetime

CAN_ID_MAX = 0x7FF  # 11-bit standard CAN identifier


def validate_event(event) -> tuple[bool, str]:
    """Validate one detection event. Returns (True, "") or (False, reason)."""
    if not isinstance(event, dict):
        return False, f"event must be a dict, got {type(event).__name__}"

    # --- can_id ---
    raw_id = event.get("can_id")
    if raw_id is None or (isinstance(raw_id, str) and not raw_id.strip()):
        return False, "can_id is required"
    if not isinstance(raw_id, str):
        return False, f"can_id must be a hex string (e.g. '0x1A4'), got {type(raw_id).__name__}"
    try:
        value = int(raw_id.strip(), 16)
    except ValueError:
        return False, f"can_id '{raw_id}' is not valid hex"
    if not (0 <= value <= CAN_ID_MAX):
        return False, f"can_id 0x{value:X} outside 11-bit range (0x000-0x{CAN_ID_MAX:03X})"

    # --- rule ---
    rule = event.get("rule")
    if not isinstance(rule, str) or not rule.strip():
        return False, "rule is required (non-empty string)"

    # --- timestamp ---
    ts = event.get("timestamp")
    if ts is not None:
        if not isinstance(ts, str):
            return False, f"timestamp must be an ISO-8601 string, got {type(ts).__name__}"
        try:
            datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return False, f"timestamp '{ts}' is not valid ISO-8601"

    # --- reason ---
    reason = event.get("reason")
    if reason is not None and not isinstance(reason, str):
        return False, f"reason must be a string, got {type(reason).__name__}"

    # --- details ---
    details = event.get("details")
    if details is not None and not isinstance(details, dict):
        return False, f"details must be a dict, got {type(details).__name__}"

    return True, ""
