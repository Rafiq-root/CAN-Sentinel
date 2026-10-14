"""Safe data-collection/ingestion adapters for files and authorized lab captures.

This module intentionally does not open a physical CAN interface or transmit frames.
Connect an approved capture/export process by passing its CSV path here.
"""
from pathlib import Path
from .preprocess import load_can_csv, validate_can_dataframe

def collect_from_csv(path: str | Path):
    """Ingest a saved CAN CSV and return a normalized dataframe."""
    df = load_can_csv(path)
    issues = validate_can_dataframe(df)
    if issues:
        raise ValueError("Invalid CAN capture: " + "; ".join(issues))
    return df
