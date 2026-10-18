import sys
from pathlib import Path
from can_ids.preprocess import load_can_csv, validate_can_dataframe
path = sys.argv[1] if len(sys.argv) > 1 else "data/sample_can.csv"
df = load_can_csv(path)
print(df.head().to_string(index=False))
print("Validation issues:", validate_can_dataframe(df) or "none")
