"""Command-line entry point."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from .preprocess import load_can_csv, validate_can_dataframe
from .engine import DetectionEngine, EngineConfig

def main():
    parser = argparse.ArgumentParser(description="Offline CAN Bus IDS CSV analyzer")
    parser.add_argument("--input", required=True, help="Path to authorized CAN CSV")
    parser.add_argument("--output", default="reports/alerts.csv", help="Output CSV path")
    parser.add_argument("--max-id-rate", type=int, default=100, help="Alert threshold per CAN ID per window")
    parser.add_argument("--max-global-rate", type=int, default=2000, help="Alert threshold for all messages per window")
    args = parser.parse_args()
    df = load_can_csv(args.input)
    issues = validate_can_dataframe(df)
    if issues:
        raise SystemExit("Data validation failed: " + "; ".join(issues))
    engine = DetectionEngine(EngineConfig(
        max_messages_per_id_per_window=args.max_id_rate,
        max_global_messages_per_window=args.max_global_rate,
    ))
    results = engine.process_dataframe(df)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    count = int(results["is_alert"].sum())
    print(f"Analyzed {len(results)} CAN messages; alerts={count}; report={output}")
    print("Note: rule thresholds are defaults; tune against a labeled/known-normal validation set.")

if __name__ == "__main__":
    main()
