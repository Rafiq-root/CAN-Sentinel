# TRC to CSV Converter - GEM-CAN labeling (dual-source)
# Time column in TRC is milliseconds -> convert to seconds
# DoS can be Tx (PCAN injection), but brake/steer tampering can be Rx (Autoware/PACMod)

from google.colab import files
import pandas as pd

print("Upload your .trc file:")
uploaded = files.upload()
trc_file = list(uploaded.keys())[0]

data = []
with open(trc_file, "r") as f:
    for line in f:
        if line.startswith(";") or not line.strip():
            continue

        parts = line.split()
        # Expected (PCAN TRC classic):
        # N  Time[ms]  Type  ID  Rx/Tx  DLC  d0 d1 d2 d3 d4 d5 d6 d7
        if len(parts) < 7:
            continue

        try:
            t_ms = float(parts[1])                 # TRC is ms
            can_id = parts[3].upper().replace("H","")
            direction = parts[4]                   # Rx or Tx
            dlc = int(parts[5])

            payload = parts[6:14]                  # up to 8 bytes
            payload += ["00"] * (8 - len(payload)) # pad to 8 bytes

            data.append({
                "timestamp": t_ms / 1000.0,        # seconds
                "arbitration_id": can_id,
                "dlc": dlc,
                "data0": payload[0],
                "data1": payload[1],
                "data2": payload[2],
                "data3": payload[3],
                "data4": payload[4],
                "data5": payload[5],
                "data6": payload[6],
                "data7": payload[7],
                "direction": direction
            })
        except:
            continue

df = pd.DataFrame(data)

# Default labels
df["label"] = 0
df["Attack_Type"] = "Normal"

# Helper: full payload string
df["payload8"] = (
    df["data0"].str.upper() + " " + df["data1"].str.upper() + " " +
    df["data2"].str.upper() + " " + df["data3"].str.upper() + " " +
    df["data4"].str.upper() + " " + df["data5"].str.upper() + " " +
    df["data6"].str.upper() + " " + df["data7"].str.upper()
)

# --- DoS Flooding (PCAN transmit injection) ---
dos_mask = (
    df["arbitration_id"].isin(["0000", "00000000"]) &
    (df["payload8"] == "00 00 00 00 00 00 00 00")
)
df.loc[dos_mask, ["label", "Attack_Type"]] = [1, "DoS"]

# --- Brake Tampering (Autoware/PACMod generated -> may appear as Rx) ---
brake_mask = (
    (df["arbitration_id"] == "18FF00F9") &
    (df["payload8"] == "05 00 64 5B 0A 00 FF 00")
)
df.loc[brake_mask, ["label", "Attack_Type"]] = [1, "Brake Tampering"]

# --- Steering Tampering (Autoware/PACMod generated -> may appear as Rx) ---
steer_mask = (
    (df["arbitration_id"] == "18FF70F9") &
    (df["payload8"] == "05 00 C5 85 FA FF 7A 00")
)
df.loc[steer_mask, ["label", "Attack_Type"]] = [1, "Steering Tampering"]

# Drop helper col
df = df.drop(columns=["payload8"])

# Save outputs
base_name = trc_file.replace(".trc", "")
unlabeled_file = f"{base_name}_Raw.csv"
labeled_file = f"{base_name}_Raw_Labeled.csv"

df.drop(["label", "Attack_Type"], axis=1).to_csv(unlabeled_file, index=False)
df.to_csv(labeled_file, index=False)

print(f"\n✓ Converted {len(df)} messages")
print("\nLabel distribution:")
print(df["label"].value_counts().to_string())
print("\nAttack types:")
print(df["Attack_Type"].value_counts().to_string())

files.download(unlabeled_file)
files.download(labeled_file)
