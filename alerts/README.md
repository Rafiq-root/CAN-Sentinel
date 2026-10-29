# CAN-Sentinel — Security Analysis & Alert Management

**Member 3 (Team Lead) | Branch: `member-3`**

CAN-Sentinel converts raw detection events from the Intrusion Detection Engine into structured, severity-rated alerts. It prevents alert storms through duplicate folding, validates untrusted inputs, and maintains persistent alert history for dashboard integration.

## Features

- **Severity rating:** Assigns `LOW`, `MEDIUM`, or `HIGH` severity based on detection rules.
- **Safety escalation:** Raises alerts involving safety-critical CAN IDs to `HIGH`.
- **Duplicate folding:** Groups repeated events within a configurable time window.
- **Input validation:** Rejects malformed events without crashing the pipeline.
- **Persistent history:** Stores alerts in JSON and exports CSV reports.
- **Dashboard integration:** Supports alert filtering and statistics.

## Pipeline

```text
Member 2                  Member 3                    Member 4
Detection Engine  -------> CAN-Sentinel ------------> Dashboard
                              |
                              |-- Validate events
                              |-- Rate severity
                              |-- Fold duplicates
                              `-- Store alert history
```

## Requirements

- Python 3.10+
- Python standard library
- `pytest` for testing

## Quick Start

Run these commands from the repository root.

**Run all tests**

```bash
python3 -m pytest alerts -v
```

**Generate sample alert logs (JSON + CSV)**

```bash
python3 -m alerts.generate_samples
```

**Run attack scenarios**

```bash
python3 -m alerts.generate_scenarios
```

## Usage

### Process a Detection Event

```python
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
```

Invalid events return `None` and are recorded in `mgr.rejected_events`.

### Query Alerts and Statistics

```python
# Get HIGH-severity alerts
alerts = mgr.get_alerts(severity="HIGH", limit=20)

# Filter by CAN ID and status
new_alerts = mgr.get_alerts(can_id="0x1A4", status="NEW")

# Get aggregate statistics
stats = mgr.stats()
```

## Severity Model

| Detection Rule | Base Severity |
|---|---|
| `HIGH_FREQUENCY` | HIGH |
| `SPOOFED_ID` | HIGH |
| `UNKNOWN_ID` | MEDIUM |
| `ABNORMAL_TIMING` | MEDIUM |
| `ABNORMAL_ENTROPY` | MEDIUM |
| `MALFORMED_FRAME` | LOW |
| Unknown rule | MEDIUM |

### Safety-Critical CAN IDs

| CAN ID | System |
|---|---|
| `0x000` | Brake control |
| `0x1A4` | Steering angle |
| `0x0C8` | Engine RPM |
| `0x0D2` | Airbag status |

**Escalation rule:** Events involving safety-critical CAN IDs are assigned `HIGH` severity, regardless of their base severity.

## Validation and Duplicate Folding

### Input Validation

Events are rejected if:

- The event is not a dictionary.
- The CAN ID is missing, invalid, or outside `0x000`–`0x7FF`.
- The detection rule is missing, not a string, or empty.
- A supplied timestamp is invalid.
- `reason` is not a string.
- `details` is not a dictionary.

Rejected events are logged, and processing continues without raising an exception through the event-processing interface.

### Duplicate Folding

| Condition | Behavior |
|---|---|
| Same CAN ID and rule within 10 seconds | Update existing alert |
| Same key outside the window | Create a new alert |
| Different CAN ID or rule | Create a separate alert |
| Unparseable timestamps | Prefer folding to reduce alert spam |

Folded events increment `occurrences` and update `last_seen` when possible.

## Persistence

### Automatic Persistence

```python
from alerts.manager import AlertManager

mgr = AlertManager(history_path="alert_history.json")
```

Existing history is loaded at startup, and changes are saved automatically when persistent mode is enabled.

### JSON History

```python
from alerts.storage import save_alerts_json, load_alerts_json

save_alerts_json(mgr.get_alerts(), "history.json")
alerts = load_alerts_json("history.json")
```

### CSV Export

```python
from alerts.storage import export_alerts_csv

export_alerts_csv(mgr.get_alerts(), "history.csv")
```

- **JSON:** Preserves complete alert details, including `raw_details`.
- **CSV:** Provides a flattened format for review.
- **Missing history:** Returns an empty list when loading a nonexistent file.
- **Corrupt history:** The manager should start fresh and record the problem in `mgr.persistence_errors`, rather than crash.

## Attack Scenarios

Run all scenarios:

```bash
python3 -m alerts.generate_scenarios
```

| Scenario | Expected Result |
|---|---|
| DoS flood: 10 events on `0x000` in 0.9 seconds | One HIGH alert, 10 occurrences |
| Spoofing: `UNKNOWN_ID` on `0x0D2` and `0x123` | HIGH for `0x0D2`; MEDIUM for `0x123` |
| Replay: Two bursts on `0x7FF`, more than 10 seconds apart | Two alerts, each with two occurrences |

## Testing

```bash
python3 -m pytest alerts -v
```

| Test Suite | Tests | Coverage |
|---|---:|---|
| `test_severity.py` | 5 | Severity mapping and escalation |
| `test_manager.py` | 7 | Folding, filters, statistics |
| `test_scenarios.py` | 3 | Attack scenarios |
| `test_storage.py` | 3 | JSON and CSV |
| `test_validation.py` | 14 | Input validation and rejection |
| **Total** | **32** | |

## Project Structure

```text
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
```

## Roadmap

- **Week 2:** Status lifecycle, persisted transitions, and dashboard queries.
- **Week 3:** Live simulator and detection engine integration.
- **Week 4:** Performance improvements, edge-case testing, and final documentation.

---

**Pipeline:** Member 2 → CAN-Sentinel (Member 3) → Member 4
