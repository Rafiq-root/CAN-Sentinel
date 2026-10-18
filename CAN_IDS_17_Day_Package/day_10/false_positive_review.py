from can_ids.preprocess import load_can_csv
from can_ids.engine import DetectionEngine
df = load_can_csv("data/sample_can.csv")
results = DetectionEngine().process_dataframe(df)
alerts = results[results["is_alert"]]
print("Total rows:", len(results))
print("Alert rows:", len(alerts))
print("Alert reason counts:\n", alerts["reasons"].value_counts())
print("\nReview alerts against known-normal traffic before changing thresholds.")
