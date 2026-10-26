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
| CAN Simulation & Backend Integration | Member 1 | `member-1` |
| CAN Data Collection & Intrusion Detection Engine | Member 2 | `member-2` |
| Security Analysis & Alert Management (Team Lead) | Member 3 | `member-3` |
| Dashboard & UI | Member 4 | `member-4` |

## Architecture / Data Flow
Member 1 (simulation) → Member 2 (detection) → Member 3 (alerts) → Member 4 (dashboard)

## Branching Model
- `main` — final code only (merged after end review)
- `develop` — integration branch (Team Lead merges member branches here)
- `member-1` … `member-4` — individual working branches (each member commits to their own branch daily)
