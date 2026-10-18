from pathlib import Path
from can_ids.preprocess import load_can_csv
from can_ids.engine import DetectionEngine
source = "data/sample_can.csv"
destination = Path("reports/alerts.csv")
destination.parent.mkdir(parents=True, exist_ok=True)
results = DetectionEngine().process_dataframe(load_can_csv(source))
results.to_csv(destination, index=False)
print(f"Saved {len(results)} rows to {destination}")
