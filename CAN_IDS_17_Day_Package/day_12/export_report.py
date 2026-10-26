from pathlib import Path

from can_ids.preprocess import load_can_csv
from can_ids.engine import DetectionEngine

# Project directory
BASE_DIR = Path(__file__).resolve().parent

# Input and output files
source = BASE_DIR / "data" / "sample_can.csv"
destination = BASE_DIR / "reports" / "alerts.csv"


def main():
    try:
        # Check whether the input file exists
        if not source.exists():
            print(f"Error: CSV file not found: {source}")
            return

        # Create reports folder if it doesn't exist
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Load and process CAN traffic
        dataframe = load_can_csv(str(source))
        results = DetectionEngine().process_dataframe(dataframe)

        # Save detection results
        results.to_csv(destination, index=False)

        print(f"Success! Saved {len(results)} rows to {destination}")

    except Exception as error:
        print(f"Error: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()