from pathlib import Path
required = ["README.md", "INTEGRATION.md", "requirements.txt", "can_ids/engine.py"]
missing = [name for name in required if not (Path(name)).exists()]
if missing:
    raise SystemExit(f"Missing documentation/code files: {missing}")
print("Core documentation and engine files are present.")
