from can_ids.preprocess import load_can_csv
from can_ids.features import extract_features
df = load_can_csv("data/sample_can.csv")
features = extract_features(df)
print(features[["timestamp","can_id","inter_arrival_s","can_id_rate_1s","payload_sum","payload_unique_bytes"]].head(10))
