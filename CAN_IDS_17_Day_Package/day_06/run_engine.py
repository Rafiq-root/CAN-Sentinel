from can_ids.preprocess import load_can_csv
from can_ids.engine import DetectionEngine
df = load_can_csv("data/sample_can.csv")
result = DetectionEngine().process_dataframe(df)
print(result[["timestamp","can_id","is_alert","severity","reasons"]].to_string(index=False))
