import sys
import pandas as pd
path = sys.argv[1] if len(sys.argv) > 1 else "../starter_project/data/sample_can.csv"
df = pd.read_csv(path)
print("Rows, columns:", df.shape)
print("Columns:", df.columns.tolist())
print("\nMissing values:\n", df.isna().sum())
print("\nFirst five rows:\n", df.head().to_string(index=False))
if "label" in df:
    print("\nLabel counts:\n", df["label"].value_counts(dropna=False))
