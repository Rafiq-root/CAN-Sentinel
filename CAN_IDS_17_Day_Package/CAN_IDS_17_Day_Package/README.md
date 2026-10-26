# CAN-IDS: Data Collection + Intrusion Detection Engine

**Owner's scope:** data collection/ingestion and the intrusion-detection engine.  
**Project window:** 10 November–10 December (30 calendar days, deadline unchanged).  
**This package:** a 17-day implementation plan with daily code milestones. The other 13 days remain available for integration, reviews, fixes, testing, and final handover; do not move the deadline.

## Important scope boundaries

- This is a defensive, offline prototype for analyzing CAN traffic files or authorized lab captures.
- It does not connect to a vehicle, transmit CAN frames, or perform attacks.
- Use only public datasets, synthetic examples, or data you are authorized to process.
- Do not commit confidential company data, credentials, or private code to a public repository.
- Detection quality depends on the dataset, labels, and thresholds. Do not claim production-grade or 100% detection.

## Project structure

Each `day_XX/` folder is a small, runnable milestone. The later days build on the same shared `can_ids/` package. The `starter_project/` folder contains the consolidated version intended for integration with the team's dashboard and feature/parameter modules.

## Requirements

Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r starter_project/requirements.txt
```

No machine-learning dependencies are required for the rule-based engine. Scikit-learn is optional for Day 8–9.

## Quick start: consolidated project

From `starter_project/`:

```bash
python -m pip install -r requirements.txt
python -m can_ids.cli --input data/sample_can.csv --output reports/alerts.csv
python -m unittest discover -s tests -v
```

The sample file is synthetic and safe. It contains timestamp, CAN ID, DLC, and eight data-byte columns.

## Expected CSV schema

Required:
- `timestamp`: numeric seconds or a parseable timestamp string
- `can_id`: hexadecimal such as `0x123`, or an integer
- `dlc`: data length from 0 to 8 for classic CAN
- `data`: optional compact hex string such as `1122334455667788`, **or** byte columns `data0`…`data7`
- `label`: optional ground-truth label; not used by the rule-based detector

Column aliases such as `time`, `ID`, `canid`, `length`, and `payload` are accepted by preprocessing. Review `can_ids/preprocess.py` if your dataset uses another schema.

## Integration contract for teammates

- Data collector / ingestion module: provide a CSV path or an iterable of row dictionaries.
- Detection engine: `DetectionEngine(config).process_dataframe(df)` returns a dataframe with `is_alert`, `severity`, and `reasons`.
- Teammate 1's parameter/feature module can supply `FeatureConfig` values and/or computed features; coordinate field names before merging.
- Dashboard teammate should read `reports/alerts.csv` or call the engine and display the alert fields. Avoid importing the dashboard into the engine.
- Use a shared interface and a pull request rather than editing another member's branch directly.

## 17-day work plan

Day 1 setup and sample data; Day 2 inspect/validate data; Day 3 normalize records; Day 4 feature extraction; Day 5 rule configuration; Day 6 engine; Day 7 tests; Day 8 optional ML baseline; Day 9 evaluation; Day 10 false-positive review; Day 11 alert format; Day 12 report export; Day 13 CLI; Day 14 integration; Day 15 performance; Day 16 docs; Day 17 final smoke test.

Suggested commit messages are listed in each `day_XX/README.md`. Commit only after running the listed checks and reviewing the diff.
