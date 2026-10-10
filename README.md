# CAN-Sentinel

**Automotive ECU Intrusion Detection System** — CAN-Sentinel simulates and analyzes
Controller Area Network (CAN) bus traffic, detects intrusions (spoofed IDs, abnormal
message frequency/entropy) using rule-based and machine-learning analysis, raises
severity-rated alerts, and displays live results on a local dashboard.

## Status
Week 1 — Implementation Phase 1 (in progress)

## Team & Module Ownership

| Module | Owner | Branch |
|---|---|---|
| CAN Data Collection & Simulation | Member 1 | `member-1` |
| Intrusion Detection Engine | Member 2 | `member-2` |
| Security Analysis & Alert Management | Member 3 | `member-3` |
| Dashboard & Integration | Member 4 | `member-4` |

## Branching Model
- `main` — final code only (merged after end review)
- `develop` — integration branch (Team Lead merges member branches here)
- `member-1` … `member-4` — individual working branches (each member commits to their own branch daily)
