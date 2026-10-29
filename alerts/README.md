CAN-Sentinel — Security Analysis & Alert Management

Member 3 (Team Lead) | Branch: member-3

CAN-Sentinel converts raw detection events from the Intrusion Detection Engine into structured, severity-rated alerts. It prevents alert storms through duplicate folding, validates untrusted inputs, and maintains persistent alert history for dashboard integration.

Features
Severity rating: Assigns LOW, MEDIUM, or HIGH severity based on detection rules.
Safety escalation: Automatically raises alerts involving safety-critical CAN IDs to HIGH.
Duplicate folding: Groups repeated events within a configurable time window.
Input validation: Rejects malformed events without crashing the pipeline.
Persistent history: Stores alerts in JSON and exports CSV reports.
Dashboard integration: Supports alert filtering and statistics.
Pipeline
text
Member 2                 Member 3                 Member 4
Detection Engine  ────►  CAN-Sentinel  ────────►  Dashboard
                         Validate
                         Rate severity
                         Fold duplicates
                         Store history

Requirements
Python 3.10+
Python standard library
pytest for testing
Quick Start

Run from the repository root:

bash
# Run all tests
python3 -m pytest alerts -v

# Generate sample alert logs (JSON + CSV)
python3 -m alerts.generate_samples

# Run attack scenarios
python3 -m alerts.generate_scenarios

Usage
python
from alerts.manager import AlertManager

mgr = AlertManager(dedupe_window_seconds=10)

alert = mgr.process_event({
    "event_id": "e1",
    "timestamp": "2026-10-15T09:00:00Z",
    "can_id": "0x1A4",
    "rule": "HIGH_FREQUENCY",
    "reason": "142 msgs/s (threshold 50/s)",
    "details": {"frequency": 142},
})

# Query alerts
alerts = mgr.get_alerts(severity="HIGH", limit=20)

# Get statistics
stats = mgr.stats()


Invalid events return None and are recorded in mgr.rejected_events.

Severity Model
Detection Rule	Base Severity
HIGH_FREQUENCY	HIGH
SPOOFED_ID	HIGH
UNKNOWN_ID	MEDIUM
ABNORMAL_TIMING	MEDIUM
ABNORMAL_ENTROPY	MEDIUM
MALFORMED_FRAME	LOW
Unknown rule	MEDIUM

Safety-critical CAN IDs: 0x000 (brake), 0x1A4 (steering), 0x0C8 (engine RPM), 0x0D2 (airbag).

Any event involving these IDs is escalated to HIGH, regardless of its base severity.

Validation and Duplicate Folding
Input Validation

Events are rejected if they contain:

Missing or invalid CAN IDs outside 0x000–0x7FF.
Missing or empty detection rules.
Invalid timestamps, when supplied.
Incorrect types for reason or details.
A non-dictionary event.

Rejected events are logged, and processing continues without raising an exception through the event-processing interface.

Duplicate Folding
Same CAN ID + rule within 10 seconds: Update the existing alert.
Same key outside the window: Create a new alert.
Different CAN ID or rule: Create a separate alert.
Unparseable timestamps: Prefer folding to reduce alert spam.

Folded events increment occurrences and update last_seen when possible.

Persistence
python
from alerts.manager import AlertManager
from alerts.storage import (
    save_alerts_json,
    load_alerts_json,
    export_alerts_csv,
)

# Automatic persistence
mgr = AlertManager(history_path="alert_history.json")

# Manual export
save_alerts_json(mgr.get_alerts(), "history.json")
export_alerts_csv(mgr.get_alerts(), "history.csv")

# Load saved history
alerts = load_alerts_json("history.json")


JSON preserves full alert details, including raw_details. CSV provides a flattened format for review. Missing history files return an empty list.

In persistent mode, history is loaded at startup and updates are saved automatically. Corrupt history should not crash initialization; the manager records persistence errors and starts fresh.

Attack Scenarios

Run the scenarios using python3 -m alerts.generate_scenarios.

Scenario	Expected Result
DoS flood: 10 events on 0x000 in 0.9 s	One HIGH alert, 10 occurrences
Spoofing: UNKNOWN_ID on 0x0D2 and 0x123	HIGH for 0x0D2, MEDIUM for 0x123
Replay: two bursts on 0x7FF, more than 10 s apart	Two alerts, two occurrences each
Testing

Run the test suite:

bash
python3 -m pytest alerts -v

Test Suite	Tests	Coverage
test_severity.py	5	Severity mapping and escalation
test_manager.py	7	Folding, filters, statistics
test_scenarios.py	3	Attack scenarios
test_storage.py	3	JSON and CSV
test_validation.py	14	Input validation and rejection
Total	32	
Project Structure
text
alerts/
├── schema.py
├── severity_rules.py
├── validation.py
├── manager.py
├── storage.py
├── generate_samples.py
├── generate_scenarios.py
├── samples/
└── tests/
    ├── test_severity.py
    ├── test_manager.py
    ├── test_scenarios.py
    ├── test_storage.py
    └── test_validation.py

Roadmap
Week 2: Status lifecycle, persisted transitions, additional dashboard queries.
Week 3: Live simulator and detection engine integration.
Week 4: Performance improvements, edge-case testing, final documentation.

Pipeline: Member 2 → CAN-Sentinel (Member 3) → Member 4
