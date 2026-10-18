# Day 09: Evaluate the detector

## Goal
Compute precision, recall, F1 and confusion matrix on held-out labeled data.

## Do today
Use the evaluation helper in `starter_project/can_ids/evaluate.py` after attaching ground-truth labels to the result dataframe. Report precision, recall and F1, plus TP/FP/FN/TN. If labels are unavailable, say evaluation is not yet possible instead of inventing metrics.

## Suggested commit
```bash
git add .
git commit -m "feat: add model evaluation metrics"
```

**Commit only when the work is actually complete.** If the repository belongs to your company, use its approved branch and review process.

## Daily code file
`evaluate_results.py` is the runnable example for this milestone. For scripts importing `can_ids`, copy/run it from `starter_project/` or set `PYTHONPATH` to that folder. The consolidated implementation is in `starter_project/`.
