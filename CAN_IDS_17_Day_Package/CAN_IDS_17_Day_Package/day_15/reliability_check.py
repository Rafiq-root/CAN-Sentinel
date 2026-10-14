from can_ids.preprocess import load_can_csv, validate_can_dataframe
from can_ids.engine import DetectionEngine
df = load_can_csv("data/sample_can.csv")
issues = validate_can_dataframe(df)
if issues:
    raise SystemExit("; ".join(issues))
result = DetectionEngine().process_dataframe(df)
assert len(result) == len(df), "Row count changed unexpectedly"
assert result["is_alert"].notna().all()
print("Reliability smoke check passed.")
