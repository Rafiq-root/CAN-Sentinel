"""Basic evaluation helpers for datasets with ground-truth labels."""
from __future__ import annotations
import pandas as pd

def evaluate_labeled_results(df: pd.DataFrame, positive_labels=("attack", "dos", "fuzzy", "spoofing", "replay")):
    if "label" not in df or "is_alert" not in df:
        raise ValueError("Need label and is_alert columns")
    y_true = df["label"].astype(str).str.lower().isin(set(positive_labels))
    y_pred = df["is_alert"].astype(bool)
    tp = int((y_true & y_pred).sum())
    fp = int((~y_true & y_pred).sum())
    fn = int((y_true & ~y_pred).sum())
    tn = int((~y_true & ~y_pred).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall, "f1": f1}
