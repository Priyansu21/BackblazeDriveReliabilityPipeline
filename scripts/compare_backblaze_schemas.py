from pathlib import Path
import csv
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REFERENCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "backblaze"
    / "reference"
    / "Drive_Stats_Schema_2018_Onward.csv"
)

Q1_2016_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "backblaze"
    / "2016_Q1"
)

QUARTER_PATTERN = re.compile(r"^\d{4}\s+Q[1-4]$")


def read_csv_header(file_path):
    """Read the column names from a daily CSV file."""
    with file_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        return next(csv.reader(file))


def read_schema_reference(file_path):
    """Extract each quarter's schema from the reference CSV."""
    schemas = {}

    with file_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.reader(file)

        for row in reader:
            if not row:
                continue

            quarter = row[0].strip()

            # Only process rows whose first cell is a quarter label.
            if not QUARTER_PATTERN.fullmatch(quarter):
                continue

            # The remaining nonblank cells are that quarter's columns.
            columns = [
                value.strip()
                for value in row[1:]
                if value.strip()
            ]

            schemas[quarter] = columns

    return schemas


def compare_schemas(baseline_name, baseline, comparison_name, comparison):
    baseline_set = set(baseline)
    comparison_set = set(comparison)

    added = sorted(comparison_set - baseline_set)
    removed = sorted(baseline_set - comparison_set)

    print(f"\n{'=' * 60}")
    print(f"{baseline_name} -> {comparison_name}")
    print(f"{'=' * 60}")
    print(f"Baseline column count: {len(baseline)}")
    print(f"Comparison column count: {len(comparison)}")
    print(f"Columns added: {len(added)}")
    for column in added:
        print(f"  + {column}")

    print(f"Columns removed: {len(removed)}")
    for column in removed:
        print(f"  - {column}")

    if not added and not removed:
        print("No column additions or removals detected.")

    # A set comparison ignores column order.
    if baseline != comparison and not added and not removed:
        print("Column order changed, but the column names are the same.")


def main():
    if not REFERENCE_FILE.is_file():
        raise FileNotFoundError(
            f"Schema reference not found: {REFERENCE_FILE}"
        )

    daily_files = sorted(
        path
        for path in Q1_2016_DIR.glob("*.csv")
        if not path.name.startswith("._")
    )

    if not daily_files:
        raise FileNotFoundError(
            f"No daily CSV files found in {Q1_2016_DIR}"
        )

    baseline = read_csv_header(daily_files[0])
    schemas = read_schema_reference(REFERENCE_FILE)

    if not schemas:
        raise ValueError(
            "No quarter schemas were found in the reference file."
        )

    print("BACKBLAZE SCHEMA COMPARISON")
    print(f"2016 baseline file: {daily_files[0].name}")
    print(f"2016 baseline columns: {len(baseline)}")
    print(f"Quarter schemas found: {len(schemas)}")
    print("Quarters:", ", ".join(schemas.keys()))

    # Compare the 2016 baseline with each available reference quarter.
    for quarter, columns in schemas.items():
        compare_schemas(
            "Q1 2016",
            baseline,
            quarter,
            columns,
        )

    # Also compare consecutive quarters within the reference.
    quarters = list(schemas.items())

    for index in range(1, len(quarters)):
        previous_name, previous_columns = quarters[index - 1]
        current_name, current_columns = quarters[index]

        compare_schemas(
            previous_name,
            previous_columns,
            current_name,
            current_columns,
        )


if __name__ == "__main__":
    main()
