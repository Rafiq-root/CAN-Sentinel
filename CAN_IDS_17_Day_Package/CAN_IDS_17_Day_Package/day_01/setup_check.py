from pathlib import Path
root = Path(__file__).resolve().parents[1] / "starter_project"
for item in ["can_ids", "data/sample_can.csv", "tests", "requirements.txt"]:
    p = root / item
    print(("OK " if p.exists() else "MISSING ") + str(p))
