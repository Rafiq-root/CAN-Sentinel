ALERT_FIELDS = ["timestamp", "can_id", "dlc", "is_alert", "severity", "reasons"]

def alert_record(row):
    return {field: row.get(field) for field in ALERT_FIELDS}

if __name__ == "__main__":
    example = {"timestamp": 1.2, "can_id": 291, "dlc": 8,
               "is_alert": True, "severity": "medium", "reasons": "UNEXPECTED_CAN_ID"}
    print(alert_record(example))
