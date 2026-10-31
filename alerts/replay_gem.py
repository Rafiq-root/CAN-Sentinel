"""Ground-truth replay driver: GEM CAN dataset -> M3 alert pipeline.

    python3 -m alerts.replay_gem <gem.csv | ->  [--base EPOCH]

HONESTY CLAUSE - what this is and is not:
  The GEM dataset (real-vehicle capture, GEM e6 platform) carries ground
  truth: every row is labeled Normal or an Attack_Type. This driver
  replays that ground truth - the LABEL acts as the detector. What is
  exercised end-to-end is the alerting pipeline itself: 29-bit ID
  validation, severity classification, critical-ID escalation, dedupe
  folding, persistence. Live label-free detection on this data is the
  Week 3 ML track, not this driver.

  Rows are converted to Member-2 engine row format and fed through the
  existing M2->M3 adapter - one adapter for every input source. This
  driver never talks to the AlertManager directly.

GROUND TRUTH -> RULE MAP (single documented place):
  DoS                -> CAN_ID_RATE_EXCEEDED (adapter: HIGH_FREQUENCY, HIGH)
                        GEM DoS is an arbitration-id-0 flood: ID 0 is the
                        highest-priority ID on any CAN bus - classic
                        starvation DoS. It also lands in CRITICAL_CAN_IDS,
                        so it escalates HIGH twice over.
  Brake Tampering    -> SPOOFED_ID (HIGH) - replayed valid PACMod brake
                        commands, the software-compromise class. M2's live
                        engine has no tampering rule yet, so the M3 rule
                        name is emitted and the adapter passes it through.
  Steering Tampering -> SPOOFED_ID (HIGH) - same class, steering ID 18FF70F9.
  Normal / label 0 / missing Attack_Type column -> skipped (clean by
  definition - the normal-driving file has no Attack_Type column at all).

TIMESTAMPS: GEM clocks are capture-relative (attack file ~8s, normal file
~127,876s - separate captures). --base anchors them to a real epoch so
reports read like a session; dedupe is unaffected (offsets cancel within
a file).
"""

from __future__ import annotations

import argparse
import csv
import sys

from .adapters.from_m2 import ingest_rows
from .manager import AlertManager
from .report import build_report
from .severity_rules import set_vehicle_critical_map

ATTACK_RULES = {
    "DoS": "CAN_ID_RATE_EXCEEDED",
    "Brake Tampering": "SPOOFED_ID",
    "Steering Tampering": "SPOOFED_ID",
}


def _clean(value):
    return str(value or "").strip()   # strips the \r from CRLF files


def gem_row_to_m2(raw):
    """Convert one GEM CSV row into one M2 engine-format row.

    Unparseable rows get can_id=None / timestamp=None so the ADAPTER
    rejects them with a trace - reject-and-log stays in one place;
    this driver never raises.
    """
    aid = _clean(raw.get("arbitration_id"))
    try:
        can_id = int(aid, 16)          # '0' -> 0, '18FF00F9' -> 419,430,649
    except ValueError:
        can_id = None                   # adapter will reject with trace
    try:
        dlc = int(_clean(raw.get("dlc")))
    except ValueError:
        dlc = None
    data = [_clean(raw.get("data%d" % i)) for i in range(8)]
    attack_type = _clean(raw.get("Attack_Type"))
    reasons = ATTACK_RULES.get(attack_type, "")
    return {
        "timestamp": _clean(raw.get("timestamp")) or None,
        "can_id": can_id,
        "dlc": dlc,
        "data_bytes": data,
        "label": attack_type or "Normal",
        "is_alert": bool(reasons),
        "severity": "",                 # M2 severity column; M3 owns severity
        "reasons": reasons,
    }


def iter_gem_rows(stream):
    """Yield M2-format rows from a GEM CSV stream (file or stdin)."""
    for raw in csv.DictReader(stream):
        if raw is None:
            continue
        yield gem_row_to_m2(raw)


def replay(stream, timestamp_base=None, manager=None):
    """Replay a GEM CSV stream through the full alert pipeline.

    Returns (manager, events_fed, rows_rejected, events_rejected_by_manager).
    """
    manager = manager or AlertManager()
    rows = list(iter_gem_rows(stream))
    return (manager,) + ingest_rows(manager, rows, timestamp_base=timestamp_base)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Replay a labeled GEM CAN CSV through the alert pipeline")
    parser.add_argument("csv", help="path to GEM CSV, or '-' for stdin")
    parser.add_argument("--base", type=float, default=None,
                        help="epoch seconds anchoring the capture-relative "
                             "clock (1793318400 = 2026-10-30T00:00:00Z)")
    parser.add_argument("--vehicle", default="mock_vehicle",
                        help="critical-ID profile to activate for this run "
                             "(mock_vehicle | gem_e6); see severity_rules.py")
    args = parser.parse_args(argv)

    # every CLI run declares its vehicle profile - deterministic regardless
    # of what an earlier run left active. Unknown name -> ValueError (loud).
    set_vehicle_critical_map(args.vehicle)

    source = sys.stdin if args.csv == "-" else open(args.csv, newline="")
    try:
        manager, fed, row_rej, mgr_rej = replay(source,
                                                timestamp_base=args.base)
    finally:
        if source is not sys.stdin:
            source.close()

    print("replayed: events=%d row-rejected=%d manager-rejected=%d alerts=%d"
          % (fed, row_rej, mgr_rej, len(manager.get_alerts())))
    print()
    print(build_report(manager,
                       title="GEM Dataset Replay - Alert Session Report"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
