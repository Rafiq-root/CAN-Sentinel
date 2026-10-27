"""
CAN Bus Intrusion Detection System - software simulation
Virtual bus + 3 ECUs + simulated attacks + rule-based IDS + Isolation Forest.
Run:  python can_ids_sim.py
"""
import random
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score

random.seed(42)
np.random.seed(42)

CYCLES = 60          # total simulation cycles (1 cycle = 1 second)
LEARN = 20           # first cycles are clean traffic -> baseline learning phase


# ---------------------------------------------------------------- 1. TRAFFIC
def j():
    return random.uniform(-0.01, 0.01)  # small timing jitter


def build_traffic():
    rows = []

    def add(c, ts, can_id, data, label, kind):
        rows.append(dict(cycle=c, ts=ts, can_id=can_id, dlc=len(data),
                         data=data, label=label, kind=kind))

    for c in range(CYCLES):
        t = float(c)
        # --- normal ECUs ---
        rpm = random.randint(800, 4000)
        add(c, t + 0.00 + j(), 0x100, [rpm >> 8, rpm & 255, 0, 0], 0, "normal")  # Engine
        add(c, t + 0.10 + j(), 0x120, [random.randint(0, 1)], 0, "normal")        # Brake
        add(c, t + 0.20 + j(), 0x300, [random.randint(0, 3), random.randint(0, 255)], 0, "normal")  # Body

        if c < LEARN:
            continue  # no attacks during the learning phase

        # --- attacks on the simulated bus ---
        if c % 10 == 0:  # fuzzing: random unknown IDs
            add(c, t + 0.40, random.randint(0x400, 0x7FF),
                [random.randint(0, 255) for _ in range(5)], 1, "fuzzing")
        if c in (35, 36):  # DoS: flood of highest-priority frames
            for i in range(10):
                add(c, t + 0.30 + i * 0.01, 0x000, [0] * 8, 1, "dos")
        if c in (45, 50):  # injection: valid ID, forged out-of-range RPM
            add(c, t + 0.15, 0x100, [0x27, 0x0F, 0, 0], 1, "injection")  # RPM 9999

    df = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)
    df["delta"] = df.groupby("can_id")["ts"].diff().fillna(1.0)   # time since last same-ID frame
    df["b0"] = df.data.apply(lambda d: d[0])
    df["b1"] = df.data.apply(lambda d: d[1] if len(d) > 1 else 0)
    df["mean_byte"] = df.data.apply(np.mean)
    return df


# ------------------------------------------------------------- 2. RULE-BASED
def run_rules(df):
    learn = df[df.cycle < LEARN]
    known = set(learn.can_id)
    rng = learn.groupby("can_id").b0.agg(["min", "max"])
    period = learn.groupby("can_id").delta.median()
    base_load = learn.groupby("cycle").size().mean()
    load = df.groupby("cycle").size()

    alerts = []
    for i, r in df.iterrows():
        a = []
        if r.can_id not in known:
            a.append("ID_WHITELIST")
        else:
            lo, hi = rng.loc[r.can_id]
            tol = 0.2 * (hi - lo) + 1
            if r.b0 < lo - tol or r.b0 > hi + tol:
                a.append("PAYLOAD_RANGE")
            if r.delta < 0.5 * period.loc[r.can_id]:
                a.append("FREQUENCY")
        if load[r.cycle] > 2.5 * base_load:
            a.append("BUS_LOAD")
        alerts.append(",".join(a))
    return alerts


# ------------------------------------------------------------------ 3. ML
FEATURES = ["can_id", "dlc", "mean_byte", "delta", "b0", "b1"]


def run_ml(df):
    train = df[df.cycle < LEARN][FEATURES]
    scaler = StandardScaler().fit(train)
    model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
    model.fit(scaler.transform(train))
    X = scaler.transform(df[FEATURES])
    scores = model.decision_function(X)
    pred = (model.predict(X) == -1).astype(int)
    return pred, scores


# ----------------------------------------------------------------- 4. REPORT
def report(name, y, p):
    print(f"{name:<14} acc={accuracy_score(y, p):.3f}  "
          f"precision={precision_score(y, p, zero_division=0):.3f}  "
          f"recall={recall_score(y, p, zero_division=0):.3f}  "
          f"false_positives={int(((p == 1) & (y == 0)).sum())}")


if __name__ == "__main__":
    df = build_traffic()
    df["rule_alerts"] = run_rules(df)
    df["rule_pred"] = (df.rule_alerts != "").astype(int)
    df["ml_pred"], df["ml_score"] = run_ml(df)
    df["hybrid_pred"] = ((df.rule_pred == 1) | (df.ml_pred == 1)).astype(int)

    # only evaluate after the learning phase
    test = df[df.cycle >= LEARN]
    print(f"Total frames: {len(df)} | test frames: {len(test)} | "
          f"attack frames: {int(test.label.sum())}\n")
    for col, name in [("rule_pred", "Rules only"), ("ml_pred", "ML only"),
                      ("hybrid_pred", "Hybrid")]:
        report(name, test.label, test[col])

    print("\nDetections per attack type (hybrid):")
    print(test[test.label == 1].groupby("kind").hybrid_pred.agg(["sum", "count"])
          .rename(columns={"sum": "detected", "count": "total"}))

    out = df.drop(columns=["data"])
    out.to_csv("can_ids_results.csv", index=False)
    print("\nSaved all frames + alerts to can_ids_results.csv")
