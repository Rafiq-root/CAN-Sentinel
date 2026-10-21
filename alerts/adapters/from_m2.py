"""Adapter: Member-2 DetectionEngine output -> Member-3 alert events.

M2 (member-2 branch) runs a rule-based offline engine over CAN DataFrames.
Each output row (DataFrame.to_dict("records")) carries:

    timestamp   float seconds (absolute epoch, or relative to capture start)
    can_id      int
    dlc         int
    data_bytes  list[int]
    label       optional dataset ground-truth string
    is_alert    bool
    severity    "high" | "medium" | "info"  (M2's hint - NOT trusted here)
    reasons     ";".join(rule strings), "" for clean frames

This module translates each alert row into one or more M3 event dicts:

    can_id      -> zero-padded hex string ("0x123") per M3 validation contract
    rule        -> mapped through RULE_ALIASES into the M3 vocabulary
    timestamp   -> ISO-8601 UTC string ending in "Z"
    severity    -> re-derived by M3 severity_rules (single source of truth,
                   includes CRITICAL_CAN_IDS escalation, which M2 lacks)

Clean rows are skipped. Unknown reason strings pass through verbatim and
classify MEDIUM - fail-open, same philosophy as validate_event. Malformed
rows (missing/invalid can_id or timestamp) are returned in a rejected list
with their index, never raised.

Integration glue (develop branch, after both modules merge):

    out = DetectionEngine().process_dataframe(df)
    ingest_rows(alert_manager, out.to_dict("records"))
"""

from __future__ import annotations

from datetime import datetime, timezone

# M2 reason string -> M3 rule name.
# DATASET_ATTACK_LABEL is deliberately NOT mapped: it is dataset ground
# truth rather than a live detection, so it passes through unchanged and
# classifies MEDIUM via the default rule.
RULE_ALIASES = {
    "CAN_ID_RATE_EXCEEDED": "HIGH_FREQUENCY",
    "GLOBAL_RATE_EXCEEDED": "HIGH_FREQUENCY",
    "UNEXPECTED_CAN_ID": "UNKNOWN_ID",
    "REPEATED_PAYLOAD_PATTERN": "ABNORMAL_ENTROPY",
}


def _iso_utc(epoch_seconds: float) -> str:
    dt = datetime.fromtimestamp(float(epoch_seconds), tz=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _hex_can_id(can_id) -> str:
    return "0x%03X" % int(can_id)   # 291 -> "0x123", 3 -> "0x003"


def translate_rows(rows, timestamp_base=None):
    """Translate M2 engine rows into M3 events.

    Returns (events, rejected): events is a list of M3 event dicts;
    rejected holds one trace dict per malformed row.

    timestamp_base: pass the epoch float of the capture start when M2
    timestamps are relative (start near zero); absolute epoch timestamps
    need no base.
    """
    events, rejected = [], []
    for index, row in enumerate(rows):
        try:
            if not bool(row.get("is_alert", False)):
                continue
            raw_reasons = str(row.get("reasons") or "")
            if not raw_reasons:
                continue
            can_id = _hex_can_id(row["can_id"])
            ts = float(row["timestamp"])
            if timestamp_base is not None:
                ts += float(timestamp_base)
            timestamp = _iso_utc(ts)
        except (AttributeError, KeyError, TypeError, ValueError, OverflowError) as exc:
            rejected.append({
                "row_index": index,
                "error": "%s: %s" % (type(exc).__name__, exc),
                "row": row if isinstance(row, dict) else repr(row),
            })
            continue
        details = {
            "source": "m2_detection_engine",
            "dlc": row.get("dlc"),
            "data_bytes": list(row.get("data_bytes") or []),
            "m2_reasons_raw": raw_reasons,
            "m2_severity": str(row.get("severity") or ""),
        }
        if row.get("label"):
            details["dataset_label"] = str(row["label"])
        for reason in [r for r in raw_reasons.split(";") if r]:
            events.append({
                "can_id": can_id,
                "rule": RULE_ALIASES.get(reason, reason),
                "timestamp": timestamp,
                "reason": "M2 engine: " + reason,
                "details": details,
            })
    return events, rejected


def ingest_rows(manager, rows, timestamp_base=None):
    """Translate M2 rows and feed every event to an AlertManager.

    Returns (n_events, n_rows_rejected, n_events_rejected_by_manager).
    """
    events, rejected = translate_rows(rows, timestamp_base=timestamp_base)
    manager_rejected = 0
    for event in events:
        if manager.process_event(event) is None:
            manager_rejected += 1
    return len(events), len(rejected), manager_rejected
