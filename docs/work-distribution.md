# CAN-Sentinel — Team Work Distribution Document

**Program:** Infotact Advanced Cybersecurity Internship (Vol. II)
**Project 1:** CAN-Sentinel — Automotive ECU Intrusion Detection System
**Cycle:** Project 1, Month 1 (started 10 Oct 2026) | **Team size:** 4

## 1. Module Ownership (Final)

| Member | Module | Branch | Folder |
|---|---|---|---|
| Member 1 | CAN Simulation & Backend Integration | `member-1` | `simulation/` |
| Member 2 | CAN Data Collection & Intrusion Detection Engine | `member-2` | `detection/` |
| Member 3 (Team Lead) | Security Analysis & Alert Management | `member-3` | `alerts/` |
| Member 4 | Dashboard & UI | `member-4` | `dashboard/` |

## 2. Module Charters

**Member 1 — CAN Simulation & Backend Integration**
- Objective: provide realistic CAN traffic and integrate backend modules into a working pipeline.
- Tasks: CAN message research; simulator producing normal + labelled suspicious traffic; shared data format; pipeline wiring (sim → detection → alerts).
- Deliverables: traffic simulator, labelled CSV datasets, integration harness, README.
- Definition of done: simulated traffic flows end-to-end and produces detection events.

**Member 2 — CAN Data Collection & Intrusion Detection Engine**
- Objective: collect/normalize CAN data and flag suspicious patterns.
- Tasks: data loading & validation; configurable frequency rules; CAN ID allowlist; malformed-frame detection; documented thresholds.
- Deliverables: collector/normalizer, detection engine, rule config, unit tests, documentation.
- Definition of done: reads the agreed input format and emits detection events per the M2→M3 contract.

**Member 3 — Security Analysis & Alert Management (Team Lead)**
- Objective: turn detection events into consistent, traceable alerts.
- Tasks: documented Low/Medium/High severity rules incl. safety-critical escalation; alert records (timestamp, CAN ID, reason, severity, status); duplicate folding within a time window; JSON/CSV history.
- Deliverables: alert manager, severity config, sample logs, tests, README.
- Definition of done: detection events are converted into alerts the dashboard can display.

**Member 4 — Dashboard & UI**
- Objective: present traffic statistics and security alerts in a usable interface.
- Tasks: dashboard framework; messages processed, severity counts, recent alerts, traffic frequency; filters (CAN ID, severity, time); end-to-end integration.
- Deliverables: dashboard app, integration code, screenshots, tests, run instructions.
- Definition of done: dashboard displays live results from connected modules, not hard-coded demo values.

## 3. Data Contracts (agreed)

- **M1 → M2 (CSV):** `timestamp, can_id, dlc, payload(hex), label(normal/attack)`
- **M2 → M3 (JSON event):** `event_id, timestamp, can_id, rule, reason, details`
- **M3 → M4 (JSON alert):** `alert_id, timestamp, can_id, severity, category, reason, status, occurrences, first_seen, last_seen, source_rule, raw_details`

## 4. Week-wise Plan (Infotact 4-phase structure)

| Week | Member 1 | Member 2 | Member 3 | Member 4 |
|---|---|---|---|---|
| 1 | CAN research, simulator scaffold | Data format, loader/validation | Alert schema, severity rules, tests | Tech choice, UI wireframe |
| 2 | Normal + attack traffic generator | Detection rules live | AlertManager, history storage | Dashboard skeleton, stats views |
| 3 | Backend pipeline wiring | Threshold tuning, tests | Status lifecycle, query API | Live integration, filters |
| 4 | Labelled datasets, docs | Edge cases, docs | Full test coverage, docs | End-to-end demo, screenshots |

## 5. Git Workflow & Rules
- One shared repository; each member commits **daily** to their **own** branch only.
- `develop` = integration branch (Team Lead merges). `main` = final code, merged only after end review.
- Mid-review: Oct 27–30 (Weeks 1+2, ≥10 commit days in last 14). Final review: Weeks 3+4 (expected early–mid Nov, 20/20 commit days).
- Unresponsive >48h → reported to Infotact; remaining members continue without reduction in requirements.

## Integration Contracts (Oct 24)

### M2 -> M3 - detection events (alerts/adapters/from_m2.py)
- Input: M2 DetectionEngine output rows via to_dict("records")
- Rule aliases: CAN_ID_RATE_EXCEEDED / GLOBAL_RATE_EXCEEDED -> HIGH_FREQUENCY;
  UNEXPECTED_CAN_ID -> UNKNOWN_ID; REPEATED_PAYLOAD_PATTERN -> ABNORMAL_ENTROPY;
  DATASET_ATTACK_LABEL passes through unchanged (ground truth, not a live rule)
- can_id int -> "0x123" hex string; float epoch seconds -> ISO-8601 Z timestamp
- M2's severity column is advisory only - M3 severity_rules is the single
  source of truth (critical CAN IDs 0x000/0x1A4/0x0C8/0x0D2 escalate to HIGH)
- One event per reason string; malformed rows rejected with a trace, never crash

### M3 -> M4 - dashboard payload (alerts/dashboard_feed.py)
- dashboard_payload(manager) returns: generated_at, summary (totals,
  by-severity, by-status, rejected count), critical_active (active alerts on
  brake/steering/engine/airbag IDs - triage panel), recent (flat rows,
  newest first, default 25)
- Read-only and safe to poll; rows are flat strings/ints - the dashboard
  renders them with zero knowledge of M3 internals
