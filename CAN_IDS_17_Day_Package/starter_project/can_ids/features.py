"""Feature extraction for offline CAN traffic."""
from __future__ import annotations
import pandas as pd

def extract_features(df: pd.DataFrame, window_seconds: float = 1.0) -> pd.DataFrame:
    """
    Adds message interval, per-ID rolling frequency, and payload summary features.
    Assumes rows are in timestamp order and timestamp is in seconds.
    """
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    out = df.copy().sort_values("timestamp", kind="stable").reset_index(drop=True)
    out["inter_arrival_s"] = out["timestamp"].diff().fillna(0).clip(lower=0)
    out["payload_sum"] = out["data_bytes"].map(lambda b: sum(b) if isinstance(b, list) else 0)
    out["payload_unique_bytes"] = out["data_bytes"].map(lambda b: len(set(b)) if isinstance(b, list) else 0)
    out["payload_nonzero_bytes"] = out["data_bytes"].map(lambda b: sum(x != 0 for x in b) if isinstance(b, list) else 0)
    # Approximate trailing frequency per ID, using a time-based window.
    out["_row"] = 1
    frequencies = []
    for can_id, group in out.groupby("can_id", sort=False):
        counts = group.set_index(pd.to_timedelta(group["timestamp"], unit="s"))["_row"]
        rolling = counts.rolling(f"{window_seconds}s", closed="both").sum()
        frequencies.extend(zip(group.index.tolist(), rolling.astype(float).tolist()))
    freq_map = dict(frequencies)
    out["can_id_rate_1s"] = [freq_map.get(i, 1.0) for i in out.index]
    out.drop(columns=["_row"], inplace=True)
    return out
