# Day 02: Inspect CSV schema and validate fields

## Goal
Inspect columns, count rows, labels, missing values, CAN ID format, DLC and payload examples.

## Do today
1. Open the sample CSV and inspect the header and first rows.
2. Run this small script against your own authorized CSV:
```python
import pandas as pd
df = pd.read_csv("YOUR_FILE.csv")
print("shape:", df.shape)
print("columns:", df.columns.tolist())
print(df.head(5).to_string())
print(df.isna().sum())
```
3. Never upload company-private data to a public repository.
4. Use `starter_project/can_ids/preprocess.py` to normalize supported fields.

## Suggested commit
```bash
git add .
git commit -m "data: add CAN dataset inspection and schema validation"
```

**Commit only when the work is actually complete.** If the repository belongs to your company, use its approved branch and review process.

## Daily code file
`inspect_csv.py` is the runnable example for this milestone. For scripts importing `can_ids`, copy/run it from `starter_project/` or set `PYTHONPATH` to that folder. The consolidated implementation is in `starter_project/`.
