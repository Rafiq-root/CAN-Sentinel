from pathlib import Path

from can_ids.preprocess import load_can_csv
from can_ids.engine import DetectionEngine

csv_path = Path("data/sample_can.csv")

if not csv_path.exists():
    raise FileNotFoundError(f"CSV file not found: {csv_path.resolve()}")

df = load_can_csv(str(csv_path))
results = DetectionEngine().process_dataframe(df)

if "is_alert" not in results.columns:
    raise KeyError("The results DataFrame has no 'is_alert' column.")

alerts = results[results["is_alert"]]

print("Total rows:", len(results))
print("Alert rows:", len(alerts))

if "reasons" in alerts.columns:
    print("Alert reason counts:\n", alerts["reasons"].value_counts())
else:
    print("The results DataFrame has no 'reasons' column.")

print("\nReview alerts against known-normal traffic before changing thresholds.")