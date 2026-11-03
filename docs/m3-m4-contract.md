# M3 -> M4 Dashboard Contract (v2 - frozen 2026-11-03)

The dashboard gets ALL of its alert data from one function:

    from alerts.dashboard_feed import dashboard_payload

    payload = dashboard_payload(manager)   # manager = alerts.manager.AlertManager

Top level: `generated_at` (ISO-8601 UTC, ends with Z), `summary`, `critical_active`, `recent`.

- `summary`: `total_alerts`, `active_alerts`, `rejected_events` (ints);
  `by_severity` = {HIGH, MEDIUM, LOW}; `by_status` = {NEW, ACKNOWLEDGED,
  RESOLVED, FALSE_POSITIVE} - all ints, all keys ALWAYS present, even at zero.
- `critical_active` (triage panel): one row per attacked system, most severe
  first. Row: `can_id`, `alert_count`, `total_occurrences`, `highest_severity`,
  `top_rule`, `first_seen`, `last_seen`. Active alerts only.
- `recent`: flat alert rows, newest first, default 25 (`recent_limit=`).
  Row: `alert_id`, `timestamp`, `can_id`, `rule`, `severity`, `status`,
  `occurrences`, `first_seen`, `last_seen`, `reason`.

Rules of the seam:

1. The payload is JSON-serializable as-is - `json.dumps(payload)` / `jsonify(payload)` are safe.
2. Every key is always present, including the empty state - render zeros directly.
3. Do NOT parse `alerts/samples/*.csv` or storage internals - this call is the
   only seam. If something you need is missing, ask member-3; do not scrape.
4. Severity depends on the active vehicle profile (default `mock_vehicle`;
   GEM replays use `gem_e6`). The dashboard displays severity, never computes it.
5. Treat `alert_id` and `reason` as opaque strings.

The schema is pinned by `alerts/tests/test_m3_m4_contract.py` (exact key sets -
a shape change fails the suite, not your app). Committed example payload:
`alerts/samples/dashboard_payload_v2_example.json`
(regenerate: `python -m alerts.generate_dashboard_example`).
