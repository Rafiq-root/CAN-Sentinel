# Mid-Review Notes - Member 3: Security Analysis & Alert Management

## Module at a glance
- `alerts/` package: schema, validation, severity_rules, manager, storage,
  persistence, M2->M3 adapter, M3->M4 dashboard feed + 8 test files
- 76 tests, all green: `python3 -m pytest alerts -q`
- Pipeline position: M2 detection rows -> M3 events -> M4 dashboard payload

## Built in Weeks 1-2
1. Alert schema + forward-only lifecycle (NEW -> ACKNOWLEDGED ->
   RESOLVED / FALSE_POSITIVE, terminal states, audit trail per transition)
2. Severity engine: rule-based classification + CRITICAL_CAN_IDS escalation
   (0x000 brake, 0x1A4 steering, 0x0C8 engine, 0x0D2 airbag -> HIGH)
3. Boundary validation: reject-and-log, never raise
4. AlertManager: dedupe folding (same can_id+rule within 10s -> one alert,
   occurrences++), stats, filters, rejected-event tracking
5. Auto-persistence: history reload on startup, save on every change,
   corrupt-file recovery, pipeline survives disk errors
6. M2->M3 adapter: rule aliases, int->hex can_id, epoch->ISO timestamps,
   malformed rows rejected with trace
7. M3->M4 dashboard feed: render-ready payload (summary, critical triage
   panel, recent alerts) - flat rows, zero M3 internals exposed

## Viva talking points
- Reject-and-log over exceptions: one bad event must never kill the pipeline
- M3 owns severity: M2's severity column is advisory; critical-ID escalation
  happens here (demo: M2 says "medium" on 0x0D2 airbag -> M3 raises HIGH)
- Dedupe: a 10-event DoS burst becomes ONE alert with occurrences=10
- Acknowledged alerts cannot return to NEW; RESOLVED is terminal
- status_history/raw_details are JSON-only exports; CSV stays flat

## Demo commands (verify in tonight's drill)
    python3 -m pytest alerts -q
    python3 -m alerts.generate_samples
    python3 -m alerts.generate_scenarios
    python3 -c "
from alerts.manager import AlertManager
from alerts.dashboard_feed import dashboard_payload
m = AlertManager()
m.process_event({'can_id': '0x0D2', 'rule': 'SPOOFED_ID',
                 'timestamp': '2026-10-26T10:00:00Z'})
import json; print(json.dumps(dashboard_payload(m), indent=2))"

## Week 3-4 plan
- vcan0 live capture (M1 python-can) feeding M2 -> M3
- Isolation Forest ML baseline (M2) alongside rule engine
- M4 dashboard wired to dashboard_payload
