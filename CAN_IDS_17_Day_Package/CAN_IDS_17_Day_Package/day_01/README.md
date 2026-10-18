# Day 01: Initialize project and sample CSV

## Goal
Create folders, environment, README, and a tiny synthetic dataset.

## Do today
1. Read the root README.
2. Create/activate a virtual environment.
3. Install `../starter_project/requirements.txt`.
4. Inspect `../starter_project/data/sample_can.csv`.
5. Create your own repository branch according to team rules.

## Run
From `starter_project/`:
```bash
python -m pip install -r requirements.txt
python -m can_ids.cli --input data/sample_can.csv --output reports/alerts.csv
```

## Suggested commit
```bash
git add .
git commit -m "chore: initialize CAN IDS project structure"
```

**Commit only when the work is actually complete.** If the repository belongs to your company, use its approved branch and review process.

## Daily code file
`setup_check.py` is the runnable example for this milestone. For scripts importing `can_ids`, copy/run it from `starter_project/` or set `PYTHONPATH` to that folder. The consolidated implementation is in `starter_project/`.
