# Day 08: Optional ML baseline

## Goal
Only if labels are available: train a simple Decision Tree/Random Forest baseline; keep it separate from rules.

## Do today
1. Confirm labels exist and mean the same thing across the dataset.
2. Split train/test by time or capture/session to reduce leakage.
3. Train a baseline using only training data; report metrics on held-out data.
4. Do not treat labels as detector input during inference.
5. Keep this as an optional experiment; the rule-based engine must still run without scikit-learn.

## Suggested commit
```bash
git add .
git commit -m "feat: add baseline CAN attack classifier"
```

**Commit only when the work is actually complete.** If the repository belongs to your company, use its approved branch and review process.

## Daily code file
`ml_baseline_notes.py` is the runnable example for this milestone. For scripts importing `can_ids`, copy/run it from `starter_project/` or set `PYTHONPATH` to that folder. The consolidated implementation is in `starter_project/`.
