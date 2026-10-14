"""Load and normalize offline CAN CSV files."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any
import pandas as pd

ALIASES = {
    "timestamp": ("timestamp", "time", "ts", "time_stamp"),
    "can_id": ("can_id", "canid", "id", "arbitration_id"),
    "dlc": ("dlc", "length", "len"),
    "data": ("data", "payload", "bytes", "data_bytes"),
    "label": ("label", "class", "attack", "category"),
}

def _find_column(columns, canonical):
    lookup = {str(c).strip().lower(): c for c in columns}
    for alias in ALIASES.get(canonical, (canonical,)):
        if alias in lookup:
            return lookup[alias]
    return None

def parse_can_id(value: Any) -> int:
    """Parse integer or hex ID such as 0x123 or 123 (decimal)."""
    if pd.isna(value):
        raise ValueError("missing CAN ID")
    if isinstance(value, int):
        result = value
    elif isinstance(value, float) and value.is_integer():
        result = int(value)
    else:
        s = str(value).strip()
        result = int(s, 16) if s.lower().startswith("0x") else int(s, 10)
    if not 0 <= result <= 0x1FFFFFFF:
        raise ValueError(f"CAN ID out of range: {value!r}")
    return result

def parse_payload(value: Any) -> list[int]:
    """Parse payload strings like '11 22 33', '112233', or byte lists."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, (list, tuple)):
        parts = list(value)
        return [int(x) for x in parts]
    s = str(value).strip()
    if not s:
        return []
    s = s.replace("0x", "").replace("0X", "")
    if re.search(r"[\s,:-]", s):
        tokens = [x for x in re.split(r"[\s,:-]+", s) if x]
        result = [int(x, 16) for x in tokens]
    else:
        if len(s) % 2:
            raise ValueError(f"payload hex string must have even length: {value!r}")
        result = [int(s[i:i+2], 16) for i in range(0, len(s), 2)]
    if any(not 0 <= x <= 255 for x in result):
        raise ValueError("payload byte outside 0..255")
    return result

def load_can_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV and normalize common CAN fields to a consistent schema."""
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("CSV contains no records")
    source_cols = {name: _find_column(df.columns, name) for name in ("timestamp", "can_id", "dlc", "data", "label")}
    byte_cols = []
    for i in range(8):
        match = _find_column(df.columns, f"data{i}")
        if match is None:
            # Support common uppercase D0..D7 or byte0..byte7 names.
            lookup = {str(c).strip().lower(): c for c in df.columns}
            match = lookup.get(f"d{i}") or lookup.get(f"byte{i}")
        byte_cols.append(match)

    if source_cols["timestamp"] is None or source_cols["can_id"] is None:
        raise ValueError("CSV must contain timestamp/time and can_id/ID columns")

    out = pd.DataFrame()
    out["timestamp"] = pd.to_numeric(df[source_cols["timestamp"]], errors="coerce")
    if out["timestamp"].isna().any():
        # Try parsing date/time strings if numeric conversion failed.
        parsed = pd.to_datetime(df[source_cols["timestamp"]], errors="coerce", utc=True)
        if parsed.isna().any():
            raise ValueError("timestamp contains values that are neither numeric nor parseable datetime")
        out["timestamp"] = parsed.astype("int64") / 1e9

    out["can_id"] = df[source_cols["can_id"]].map(parse_can_id)
    if source_cols["dlc"] is not None:
        out["dlc"] = pd.to_numeric(df[source_cols["dlc"]], errors="coerce")
    else:
        out["dlc"] = 0

    payloads = []
    for idx, row in df.iterrows():
        if source_cols["data"] is not None:
            payload = parse_payload(row[source_cols["data"]])
        elif any(c is not None for c in byte_cols):
            payload = []
            for c in byte_cols:
                if c is None or pd.isna(row[c]):
                    continue
                value = row[c]
                payload.append(int(str(value), 16) if isinstance(value, str) and str(value).lower().startswith("0x") else int(value))
        else:
            payload = []
        if any(not 0 <= b <= 255 for b in payload):
            raise ValueError(f"invalid data byte on row {idx}")
        payloads.append(payload[:8])
    out["data_bytes"] = payloads
    inferred_dlc = out["data_bytes"].map(len)
    out["dlc"] = out["dlc"].fillna(inferred_dlc).astype(int)
    if ((out["dlc"] < 0) | (out["dlc"] > 8)).any():
        raise ValueError("DLC must be between 0 and 8 for classic CAN")
    out["label"] = df[source_cols["label"]].astype(str) if source_cols["label"] is not None else "unknown"
    out = out.sort_values("timestamp", kind="stable").reset_index(drop=True)
    return out

def validate_can_dataframe(df: pd.DataFrame) -> list[str]:
    """Return validation issues; empty list means core fields look valid."""
    issues = []
    required = {"timestamp", "can_id", "dlc", "data_bytes"}
    missing = required - set(df.columns)
    if missing:
        return [f"missing required normalized columns: {sorted(missing)}"]
    if df.empty:
        issues.append("dataframe is empty")
    if pd.to_numeric(df["timestamp"], errors="coerce").isna().any():
        issues.append("timestamp has invalid values")
    if pd.to_numeric(df["can_id"], errors="coerce").isna().any():
        issues.append("CAN ID has invalid values")
    if ((pd.to_numeric(df["dlc"], errors="coerce") < 0) | (pd.to_numeric(df["dlc"], errors="coerce") > 8)).any():
        issues.append("DLC outside 0..8")
    return issues
