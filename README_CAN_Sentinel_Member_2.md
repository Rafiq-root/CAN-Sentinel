# CAN-Sentinel: Automotive ECU Intrusion Detection System

**Project:** CAN-Sentinel  
**Internship domain:** Cyber Security  
**Organization:** Infotact Solutions  
**Contributor:** Sumit Pandey (`ingensumit`)  
**Branch:** `member-2`  
**Assigned area:** Data collection and intrusion detection engine

## 1. Project Overview

CAN-Sentinel is a project focused on detecting suspicious activity in Controller Area Network (CAN) traffic used by automotive Electronic Control Units (ECUs). This repository contains work for identifying potentially abnormal CAN records and producing structured alerts for review.

> This project is for learning, testing, and demonstration. Detection results depend on the dataset, configured rules, and thresholds; alerts should be validated before being treated as confirmed attacks.

## 2. Member 2 — Scope of Contribution

My assigned responsibility is **data collection and the intrusion detection engine**. The work in this area includes:

- Loading and preprocessing CAN traffic records for analysis.
- Applying baseline rule-based checks to identify suspicious traffic.
- Flagging CAN IDs that are outside the configured allowlist.
- Checking for unusually high message frequency.
- Identifying malformed or unexpected records where supported by the input data.
- Producing structured detection results with alert status, severity, and reasons.
- Testing the detector on normal and suspicious examples.
- Reviewing false positives and false negatives and documenting assumptions and limitations.

The exact checks and output fields depend on the implementation and configuration in the current branch.

## 3. Detection Output

The alert schema currently defines these fields:

| Field | Purpose |
|---|---|
| `timestamp` | Time associated with the record |
| `can_id` | CAN identifier |
| `dlc` | Data Length Code |
| `is_alert` | Whether the record was flagged |
| `severity` | Assigned alert severity |
| `reasons` | Reason or rule that triggered the alert |

An example alert reason used in the schema demonstration is `UNEXPECTED_CAN_ID`. Actual results depend on the input data and detector rules.

## 4. Repository Structure

The repository has been developed incrementally through day-wise milestones. Relevant modules and paths may include:

- `can_ids/` — CAN data-processing and detection code, where present.
- `data/` — sample or project data, where included.
- `tests/` — detector tests, where included.
- `day_11/alert_schema.py` — alert record field schema shown in the current working tree.
- `day_11/false_positive_review.py` — false-positive review work shown as modified in the current working tree.

Please check the current branch for the exact files and folders; this README does not imply that every example path is present in every checkout.

## 5. How to Run

Run commands from the repository directory and use the paths that exist in your checkout.

1. Open the project in VS Code.
2. Select the Python environment used by the project.
3. Install dependencies from the repository's dependency file if one is provided.
4. Run the project's existing test or evaluation script with the sample dataset.
5. Review the alert counts and reasons, and compare them with the expected behavior.

Example pattern from the project's detection workflow (adjust paths to match your checkout):

```python
from can_ids.preprocess import load_can_csv
from can_ids.engine import DetectionEngine

df = load_can_csv("data/sample_can.csv")
results = DetectionEngine().process_dataframe(df)
alerts = results[results["is_alert"]]

print("Total rows:", len(results))
print("Alert rows:", len(alerts))
print("Alert reason counts:\n", alerts["reasons"].value_counts())
```

This example assumes the referenced module and sample CSV exist in your current checkout. If they do not, use the actual module and dataset paths in the repository.

## 6. Testing and Evaluation

The development milestones shown on the `member-2` branch include:

- Day 05 — Configure baseline detection rules
- Day 06 — Build the core detection engine
- Day 07 — Add unit tests
- Day 08 — Optional ML baseline
- Day 09 — Evaluate the detector
- Day 10 — Review false positives/negatives

Evaluation should consider both normal and suspicious traffic. A high alert count alone does not prove good detection: false positives, false negatives, dataset quality, and rule thresholds also need review. Do not describe a metric as measured unless it has actually been calculated from the available test data.

## 7. Limitations

- Rule-based detection can flag legitimate unusual traffic as suspicious.
- Results depend on the quality and coverage of the input dataset.
- An allowlist must reflect the expected CAN IDs for the environment being tested.
- Thresholds should be documented and validated against known-normal and suspicious examples.
- This project should not be represented as production-ready automotive protection without further validation, safety review, and testing on appropriate systems.

## 8. Next Steps

- Verify the dataset and preprocessing assumptions.
- Expand tests for normal, suspicious, and malformed records.
- Record the thresholds and rationale for each detection rule.
- Measure false positives and false negatives on labelled test data, where available.
- Keep evaluation results and project documentation in sync with the code.

## 9. Acknowledgement

This work is part of the **CAN-Sentinel: Automotive ECU Intrusion Detection System** internship project. My contribution is focused on the Member 2 assignment described above.

---

**Maintainer / Contributor:** Sumit Pandey (`ingensumit`)  
**Branch:** `member-2`
