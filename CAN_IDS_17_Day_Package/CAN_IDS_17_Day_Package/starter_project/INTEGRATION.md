# Team integration contract

Your role is **data ingestion + intrusion detection engine**.

## Input
Normalized dataframe columns:
- `timestamp`: seconds, numeric
- `can_id`: integer CAN arbitration ID
- `dlc`: 0–8 for classic CAN
- `data_bytes`: list of integers 0–255
- `label`: optional dataset label (ground truth; should not be required at runtime)

## Output
Input fields plus:
- `inter_arrival_s`
- `can_id_rate_1s`
- `payload_sum`
- `payload_unique_bytes`
- `payload_nonzero_bytes`
- `is_alert`: boolean
- `severity`: info/medium/high
- `reasons`: semicolon-separated reason codes

## Team member boundaries
- Member 1: feature/parameter requirements; agree thresholds and allowed CAN IDs with engine owner.
- Engine owner (you): file ingestion, normalization, rules, alert output, tests, metrics.
- Other integration member(s): any additional system components; share interface contract before merge.
- Dashboard owner: consume result dataframe or exported CSV; display alert count, severity, reason and timestamp.

Do not assume every team's role is exactly this split; confirm responsibilities with your team lead. Keep module boundaries clean.
