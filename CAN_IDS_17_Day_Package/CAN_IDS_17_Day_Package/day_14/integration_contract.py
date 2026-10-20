"""Smoke-check the contract expected by dashboard and feature teammates."""
from can_ids.preprocess import load_can_csv
from can_ids.engine import DetectionEngine
df = load_can_csv("data/sample_can.csv")
result = DetectionEngine().process_dataframe(df)
required = {"timestamp", "can_id", "is_alert", "severity", "reasons"}
missing = required - set(result.columns)
if missing:
    raise SystemExit(f"Integration contract failed: missing {missing}")
print("Integration contract OK; rows:", len(result))
print("Share INTEGRATION.md with the team before merging.")
