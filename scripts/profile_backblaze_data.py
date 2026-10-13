from pathlib import Path
import csv
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "backblaze"
    / "2016_Q1"
)

KEY_FIELDS = [
    "date",
    "serial_number",
    "model",
    "capacity_bytes",
    "failure",
]


def get_daily_csv_files():
    return sorted(
        path
        for path in DATA_DIR.rglob("*.csv")
        if "__MACOSX" not in path.parts
        and not path.name.startswith("._")
    )


def main():
    files = get_daily_csv_files()

    if not files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

    total_rows = 0
    failed_rows = 0
    failure_values = Counter()
    model_counts = Counter()
    daily_rows = Counter()
    daily_failed = Counter()
    unique_serials = set()
    missing_counts = Counter()
    capacity_values = set()
    encoding_fallback_files = []

    print(f"Inspecting {len(files)} daily files...")

    for csv_path in files:
        opened = False

        for encoding in ("utf-8-sig", "cp1252"):
            try:
                with csv_path.open(
                    "r", encoding=encoding, newline=""
                ) as file:
                    reader = csv.DictReader(file)

                    if not reader.fieldnames:
                        raise ValueError("Missing CSV header")

                    # Remove accidental whitespace from header names.
                    reader.fieldnames = [
                        name.strip() for name in reader.fieldnames
                    ]

                    file_rows = 0

                    for row in reader:
                        # Normalize keys and values for inspection.
                        row = {
                            (key.strip() if key else key):
                            (value.strip() if value else "")
                            for key, value in row.items()
                        }

                        total_rows += 1
                        file_rows += 1

                        for field in KEY_FIELDS:
                            if not row.get(field):
                                missing_counts[field] += 1

                        serial = row.get("serial_number", "")
                        model = row.get("model", "")
                        capacity = row.get("capacity_bytes", "")
                        failure = row.get("failure", "")
                        observation_date = row.get("date", "")

                        if serial:
                            unique_serials.add(serial)

                        if model:
                            model_counts[model] += 1

                        if capacity:
                            capacity_values.add(capacity)

                        failure_values[failure or "<blank>"] += 1

                        if failure == "1":
                            failed_rows += 1
                            daily_failed[observation_date] += 1

                        daily_rows[observation_date] += 1

                    if encoding != "utf-8-sig":
                        encoding_fallback_files.append(csv_path.name)

                    opened = True
                    break

            except UnicodeDecodeError:
                continue

        if not opened:
            raise UnicodeError(
                f"Could not decode file: {csv_path.name}"
            )

        print(f"Processed {csv_path.name}: {file_rows:,} rows")

    print("\n========== DATA PROFILE ==========")
    print(f"Files processed: {len(files)}")
    print(f"Total rows: {total_rows:,}")
    print(f"Distinct serial numbers across quarter: {len(unique_serials):,}")
    print(f"Distinct models: {len(model_counts):,}")
    print(f"Distinct nonblank capacity values: {len(capacity_values):,}")
    print(f"Rows where failure = 1: {failed_rows:,}")

    print("\nFailure column value counts:")
    for value, count in sorted(failure_values.items()):
        print(f"  {value}: {count:,}")

    print("\nMissing values in key fields:")
    for field in KEY_FIELDS:
        count = missing_counts[field]
        percentage = (count / total_rows * 100) if total_rows else 0
        print(f"  {field}: {count:,} ({percentage:.4f}%)")

    print("\nTop 10 models by observation count:")
    for model, count in model_counts.most_common(10):
        print(f"  {model}: {count:,}")

    if daily_rows:
        first_date = min(daily_rows)
        last_date = max(daily_rows)

        print("\nDaily observation range:")
        print(f"  First date: {first_date} ({daily_rows[first_date]:,} rows)")
        print(f"  Last date:  {last_date} ({daily_rows[last_date]:,} rows)")

        print("\nFirst 5 dates with failure = 1:")
        dates_with_failures = sorted(
            date for date, count in daily_failed.items() if count > 0
        )

        if dates_with_failures:
            for observation_date in dates_with_failures[:5]:
                print(
                    f"  {observation_date}: "
                    f"{daily_failed[observation_date]:,}"
                )
        else:
            print("  No rows with failure = 1 found.")

    print(
        "\nFiles requiring fallback encoding: "
        f"{len(encoding_fallback_files)}"
    )


if __name__ == "__main__":
    main()
