"""Run from starter_project/ to verify the final prototype."""
import subprocess, sys
subprocess.run([sys.executable, "-m", "can_ids.cli", "--input", "data/sample_can.csv",
                "--output", "reports/final_alerts.csv"], check=True)
subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], check=True)
print("Final smoke test complete.")
