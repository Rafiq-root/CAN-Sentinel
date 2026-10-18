CAN-Sentinel — Security Analysis & Alert Management (Member 3)
Turns raw detection events from the Intrusion Detection Engine intoconsistent, traceable, severity-rated alerts — with duplicate folding(no alert storms during an attack), boundary input validation (nothingmalformed ever crashes the pipeline), and persistent history (JSON + CSV)queryable by the dashboard.

Owner: Member 3 (Team Lead) · Branch: member-3 · Pipeline position: Member 2 → this module → Member 4

Quick Start
Requirements: Python 3.10+ (stdlib only) and pytest for the test suite.

python3 -m pytest alerts -v            # run all 32 testspython3 -m alerts.generate_samples     # regenerate sample alert logs (JSON + CSV)python3 -m alerts.generate_scenarios   # run the three attack scenarios
Usage
Processing detection events
from alerts.manager import AlertManagermgr = AlertManager(dedupe_window_seconds=10)alert = mgr.process_event({    "event_id": "e1",    "timestamp": "2026-10-15T09:00:00Z",    "can_id": "0x1A4",    "rule": "HIGH_FREQUENCY",    "reason": "142 msgs/s (threshold 50/s)",    "details": {"frequency": 142},})# Invalid events return None and are logged in mgr.rejected_events - never raise.
Querying for the dashboard (Member 4)
mgr.get_alerts()                          # all alerts, newest firstmgr.get_alerts(severity="HIGH", limit=20) # filteredmgr.get_alerts(can_id="0x1A4", status="NEW")mgr.stats()                               # total, by_severity, by_status, rejected
Persisting history
from alerts.storage import save_alerts_json, load_alerts_json, export_alerts_csvsave_alerts_json(mgr.get_alerts(), "history.json")   # full fidelity (incl. raw_details)export_alerts_csv(mgr.get_alerts(), "history.csv")   # flat export for reviewalerts = load_alerts_json("history.json")            # missing file -> [] (fresh start)
Data Contracts
Input: detection event (Member 2 → Member 3)
Field	Required	Type	Notes
event_id	recommended	str	caller's event reference
timestamp	optional	str	ISO-8601 UTC; generated if omitted
can_id	yes	str	hex, e.g. "0x1A4"; 11-bit range 0x000-0x7FF
rule	yes	str	non-empty; unknown names allowed (default MEDIUM)
reason	optional	str	human-readable explanation
details	optional	dict	passthrough metadata
Output: alert (Member 3 → Member 4)
Field	Type	Notes
alert_id	str	ALR-YYYYMMDD-XXXXXX, unique
timestamp	str	when the alert was raised
can_id	str	canonical 0x### form
severity	str	LOW / MEDIUM / HIGH
category	str	lowercase rule name
reason	str	from the triggering event
status	str	NEW / ACKNOWLEDGED / RESOLVED / FALSE_POSITIVE
occurrences	int	events folded into this alert
first_seen / last_seen	str	window covered by the alert
source_rule	str	rule that fired
raw_details	dict	passthrough (JSON store only)
Severity Model
Detection rule	Base severity	Escalates to HIGH on safety-critical ID?
HIGH_FREQUENCY	HIGH	(already HIGH)
SPOOFED_ID	HIGH	(already HIGH)
UNKNOWN_ID	MEDIUM	yes
ABNORMAL_TIMING	MEDIUM	yes
ABNORMAL_ENTROPY	MEDIUM	yes
MALFORMED_FRAME	LOW	yes
unknown rule name	MEDIUM	yes
Escalation rule: any event on a safety-critical CAN ID becomes HIGH.

Safety-critical CAN ID	System
0x000	brake control
0x1A4	steering angle
0x0C8	engine RPM
0x0D2	airbag status
Duplicate Folding Rules
Same (can_id, rule) within the dedupe window (default 10 s) → folds: occurrences += 1, last_seen updated, no new alert.
Same key, outside the window → new alert.
Different can_id or rule → always separate alerts.
Unparseable timestamps → prefer folding (fail-safe against alert spam).
Rationale: during a DoS flood producing 100+ detection events/second, thedashboard must show ONE escalating alert, not a thousand.

Input Validation Rules
Every event passes validate_event() at the boundary. Invalid events arerejected and logged, never raised — one malformed event must not kill thealerting service during an active attack.

Check	Rejection condition
event	not a dict
can_id	missing / not a string / invalid hex / outside 0x000-0x7FF
rule	missing / not a string / empty
timestamp	present but not a string / not parseable ISO-8601
reason	present but not a string
details	present but not a dict
Rejections appear in mgr.rejected_events and in stats()["rejected"].

Attack Scenarios (samples/scenarios/)
Scenario	Input	Expected behaviour
DoS flood (brake 0x000)	10 events in 0.9 s	1 HIGH alert, occurrences=10
Critical-ID spoof (airbag 0x0D2 vs benign 0x123)	2 UNKNOWN_ID events	airbag HIGH, 0x123 MEDIUM
Replay bursts (0x7FF)	2 bursts >10 s apart	2 alerts, occurrences=2 each
Run: python3 -m alerts.generate_scenarios

Testing
python3 -m pytest alerts -v      # 32 tests, 5 suites
Suite	Covers
test_severity.py (5)	severity mapping, escalation, canonicalization
test_manager.py (7)	folding windows, key separation, filters, stats
test_scenarios.py (3)	attack patterns end-to-end
test_storage.py (3)	JSON round-trip, CSV shape
test_validation.py (14)	boundary rules, reject-and-continue
Module Layout
alerts/├── schema.py             # Alert dataclass, enums, helpers├── severity_rules.py     # rule->severity mapping, escalation├── validation.py         # boundary validation├── manager.py            # AlertManager (folding, rejection log, queries, stats)├── storage.py            # JSON/CSV persistence├── generate_samples.py   # sample events -> alert logs├── generate_scenarios.py # attack scenario runner├── samples/              # events, logs, scenarios└── tests/                # 5 pytest suites
Roadmap
Week 2: status lifecycle methods + persisted transitions, auto-persistence, extra dashboard queries
Week 3: live integration with real simulator + detection engine
Week 4: performance pass, edge cases, final docs

## Persistent Mode (auto-persistence)

    from alerts.manager import AlertManager

    mgr = AlertManager(history_path="alert_history.json")

History loads at startup and every change (new alert, folded duplicate,
status transition) is written back immediately - the dashboard can restart
mid-demo without losing alerts. Without history_path the manager stays
purely in-memory (backward compatible). File format: JSON list of alert
dicts, oldest first. A corrupt history file never crashes the manager:
it starts fresh and records the problem in mgr.persistence_errors.
