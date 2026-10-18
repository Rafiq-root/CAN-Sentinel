from can_ids.preprocess import load_can_csv
from can_ids.engine import DetectionEngine
from can_ids.evaluate import evaluate_labeled_results
df = load_can_csv("data/sample_can.csv")
results = DetectionEngine().process_dataframe(df)
if "label" not in results:
    raise SystemExit("No labels: evaluation cannot be calculated.")
print(evaluate_labeled_results(results))
