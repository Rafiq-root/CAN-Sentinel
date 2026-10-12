# GEM-CAN Dataset

**Real-Vehicle Controller Area Network (CAN) Intrusion Detection Dataset**

This repository contains the **GEM-CAN** dataset, a labeled Controller Area Network (CAN) dataset collected from an autonomous GEM e6 electric vehicle under normal operation and controlled cyber-attack scenarios. The dataset supports research on in-vehicle network security, intrusion detection systems, and autonomous vehicle cybersecurity.

---

## Repository Contents

### CSV Data Files

| File | Records | Description |
|------|---------|-------------|

| **GEM_Normal_Driving_Raw_labeled.csv** | ~100,000 | Labeled baseline traffic (all frames: label=0, normal operation) |
| **GEM_Attack_Scenario_Raw_Labeled.csv** | 43,443 | Fully labeled attack scenarios with binary labels (0/1) and attack type classification |

### Supporting Files

- **GEM_CAN_metadata.json** – Experimental metadata including attack specifications, injection parameters, and bus-load measurements
- **data_preprocessing.py** – Example preprocessing script with data cleaning, feature engineering, and train-test splitting utilities
- **README.md** – This file
### Raw PCAN Files
- **PCAN_Files/** – Folder containing raw PCAN capture files
  - **GEM_Attack_Scenario_Raw.trc** – Raw PCAN trace file for attack scenario
  - **GEM_Normal_Driving_Raw.json** – Raw PCAN export for normal driving scenario
---
## Repository Structure
```
GEM_CAN_IDS_Dataset/
├── GEM_Normal_Driving_Raw_labeled.csv
├── GEM_Attack_Scenario_Raw_Labeled.csv
├── data_preprocessing.py
├── README.md
├── GEM_CAN_metadata.json
└── PCAN_Files/
    ├── GEM_Attack_Scenario_Raw.trc
    └── GEM_Normal_Driving_Raw.json
```
## Dataset Structure

### Common Fields (All CSV Files)
- `timestamp` – Message timestamp in seconds (microsecond resolution)
- `arbitration_id` – CAN identifier in hexadecimal (11-bit standard or 29-bit extended)
- `dlc` – Data Length Code (0–8 bytes)
- `data0` to `data7` – CAN payload bytes in hexadecimal format (00–FF)

### Labeled Files Only
- `label` – Binary ground-truth classification: **0 = Normal**, **1 = Attack**
- `Attack_Type` – Attack category: **Normal**, **DoS**, **Brake Tampering**, **Steering Tampering** (only in GEM_Attack_Scenario_Raw_Labeled.csv)

---

## Attack Scenarios

| Attack Type | CAN ID | Payload (Hex) | Frames | Duration | Injection Interval | Effect |
|-------------|--------|---------------|--------|----------|-------------------|--------|
| **DoS Flooding** | 0x00000000 | 00 00 00 00 00 00 00 00 | 41,080 | 16.1 s | 1.10 ± 0.55 ms | 100% bus saturation, 21.7s steering delay |
| **Brake Tampering** | 0x18FF00F9 | 05 00 64 5B 0A 00 FF 00 | 663 | ~89 s | 11.1 ± 0.1 s | Spoofed brake control commands |
| **Steering Tampering** | 0x18FF70F9 | 05 00 C5 85 FA FF 7A 00 | 662 | ~89 s | 11.1 ± 0.3 s | Spoofed steering control commands |

**Attack Execution:**
- DoS attacks injected using PCAN-View v5.3.0's cyclic transmit feature
- Tampering attacks generated through Autoware's drive-by-wire control system (PACMod)
- Vehicle remained stationary in autonomous mode for safety
- DoS attack window: 5.666–21.782 seconds
- Tampering attacks concurrent with legitimate traffic throughout session

---

## Key Findings

### DoS Attack Impact (Quantified from CAN Logs)
- **Bus load**: 20% baseline → 100% saturation (Figure 5 in manuscript)
- **Steering communication disruption**: 21.7-second gap between last pre-DoS message (5.659s) and first post-DoS message (27.371s)
- **Attack self-interference**: DoS saturation blocked even the attacker's own tampering injections
- **Safety implication**: In operational vehicle, steering would be unresponsive for >20 seconds

---

## Quick Start

### Load Dataset
```python
import pandas as pd

# Load labeled attack scenarios
df = pd.read_csv('GEM_Attack_Scenario_Raw_Labeled.csv')

# Check label distribution
print(df['label'].value_counts())
# 0 (Normal):  1,038 frames
# 1 (Attack): 42,405 frames

# Check attack types
print(df['Attack_Type'].value_counts())
# DoS:              41,080
# Brake Tampering:     663
# Steering Tampering:  662
# Normal:            1,038
```

### Preprocessing Example
```python
# Use provided preprocessing script
from data_preprocessing import load_gem_can_data, clean_can_data, add_temporal_features

df = load_gem_can_data('GEM_Attack_Scenario_Raw_Labeled.csv')
df = clean_can_data(df)
df = add_temporal_features(df)  # Adds inter-arrival time, message frequency, etc.
```

### Reproduce Steering Delay Calculation
```python
import pandas as pd

# Load labeled attack data
df = pd.read_csv('GEM_Attack_Scenario_Raw_Labeled.csv')

# Filter steering messages
steering = df[df['arbitration_id'] == '18FF70F9'].sort_values('timestamp')

# Find messages around DoS window (5.666-21.782 s)
pre_dos = steering[steering['timestamp'] < 5.666]
post_dos = steering[steering['timestamp'] > 21.782]

if len(pre_dos) > 0 and len(post_dos) > 0:
    last_before = pre_dos['timestamp'].iloc[-1]
    first_after = post_dos['timestamp'].iloc[0]
    delay = first_after - last_before
    print(f"Steering delay: {delay:.3f} seconds")
    # Output: Steering delay: 21.712 seconds
```

---

## Data Collection Details

- **Vehicle Platform**: GEM e6 autonomous electric vehicle
- **CAN Bitrate**: 250 kbps
- **Location**: North Carolina A&T State University, North Campus closed-loop track (36.085°N, 79.771°W)
- **Hardware**: PCAN-USB Pro dual-channel CAN/LIN interface
- **Logging Software**: PCAN-View v5.3.0 (microsecond-level timestamps)
- **Attack Injection**: PCAN-View v5.3.0's cyclic transmit feature (DoS), Autoware/PACMod (tampering)
- **Preprocessing**: Python 3 with pandas, numpy, scikit-learn

---

## Labeling Policy

- Attack windows defined using synchronized PCAN injection logs
- 100 ms conservative transition buffer applied at attack onset/termination to account for CAN arbitration delays
- Binary encoding: **0 = Normal** (benign ECU traffic), **1 = Attack** (injected malicious frames)
- Multi-class encoding: **Normal**, **DoS**, **Brake Tampering**, **Steering Tampering**
- Labels validated through cross-referencing with injection logs and bus-load measurements

---

## Notes

- Raw PCAN capture files (.trc for attacks, .json for normal driving) are included in the PCAN_Files folder
- All CSV files were derived from these raw files through format conversion while preserving all message-level information
- Legacy PCAN timestamp field unified as `timestamp` during preprocessing (values unchanged)
- All attack specifications, injection timing, and experimental conditions documented in **GEM_CAN_metadata.json**
- DoS attack timing analysis (21.7s delay) fully reproducible from GEM_Attack_Scenario_Raw_Labeled.csv timestamps

---

## Citation

If you use this dataset, please cite:

**Dataset:**
```
GEM-CAN Dataset, Zenodo, https://doi.org/10.5281/zenodo.17834776
```

**Related Paper:**
```
Tavasoli, M., et al. (2025). "Trust-Aware Federated Defense Against Data Poisoning 
in ML-Driven IDS For CAVs." IEEE PST 2025.
```

---

## Contact

For questions or issues, please contact the corresponding author or open an issue in the repository.
