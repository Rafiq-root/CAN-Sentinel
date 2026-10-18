"""Explainable, configurable rule-based CAN IDS engine."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any
import pandas as pd
from .features import extract_features

@dataclass
class EngineConfig:
    """Tune only after examining your dataset's normal traffic."""
    window_seconds: float = 1.0
    max_messages_per_id_per_window: int = 100
    max_global_messages_per_window: int = 2000
    alert_unknown_can_id: bool = False
    allowed_can_ids: set[int] | None = None
    suspicious_payload_repeat_count: int = 30
    known_attack_labels: set[str] = field(default_factory=lambda: {"attack", "dos", "fuzzy", "spoofing", "replay"})

class DetectionEngine:
    """Offline analyzer; it never transmits frames to a vehicle or CAN network."""
    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig()

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        required = {"timestamp", "can_id", "dlc", "data_bytes"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"normalized dataframe missing columns: {sorted(missing)}")
        if df.empty:
            result = df.copy()
            for c, default in (("is_alert", False), ("severity", "info"), ("reasons", "")):
                result[c] = default
            return result
        out = extract_features(df, self.config.window_seconds)
        global_times = deque()
        id_times = defaultdict(deque)
        payload_counts = defaultdict(int)
        alerts, severities, reasons_list = [], [], []
        for _, row in out.iterrows():
            ts = float(row["timestamp"])
            can_id = int(row["can_id"])
            payload = tuple(row["data_bytes"]) if isinstance(row["data_bytes"], list) else tuple()
            reasons = []
            # Rolling rate checks, timestamps in seconds.
            while global_times and ts - global_times[0] > self.config.window_seconds:
                global_times.popleft()
            global_times.append(ts)
            per_id = id_times[can_id]
            while per_id and ts - per_id[0] > self.config.window_seconds:
                per_id.popleft()
            per_id.append(ts)
            if len(per_id) > self.config.max_messages_per_id_per_window:
                reasons.append("CAN_ID_RATE_EXCEEDED")
            if len(global_times) > self.config.max_global_messages_per_window:
                reasons.append("GLOBAL_RATE_EXCEEDED")
            if self.config.allowed_can_ids is not None and can_id not in self.config.allowed_can_ids:
                reasons.append("UNEXPECTED_CAN_ID")
            payload_counts[(can_id, payload)] += 1
            if payload and payload_counts[(can_id, payload)] > self.config.suspicious_payload_repeat_count:
                reasons.append("REPEATED_PAYLOAD_PATTERN")
            label = str(row.get("label", "unknown")).strip().lower()
            if label in self.config.known_attack_labels or label.startswith("attack_"):
                reasons.append("DATASET_ATTACK_LABEL")
            alerts.append(bool(reasons))
            severities.append("high" if any(r in reasons for r in ("CAN_ID_RATE_EXCEEDED", "GLOBAL_RATE_EXCEEDED", "DATASET_ATTACK_LABEL")) else ("medium" if reasons else "info"))
            reasons_list.append(";".join(dict.fromkeys(reasons)))
        out["is_alert"] = alerts
        out["severity"] = severities
        out["reasons"] = reasons_list
        return out
