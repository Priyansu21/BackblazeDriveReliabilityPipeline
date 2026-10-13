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

OUTPUT_DIR = PROJECT_ROOT / "reports"
OUTPUT_FILE = OUTPUT_DIR / "schema_drift_summary.csv"

QUARTER_PATTERN = re.compile(r"^(\d{4})\s+Q([1-4])$")


def read_quarter_schemas():
    """Read quarter labels and their corresponding column names."""
    schemas = {}

    with REFERENCE_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        for row in csv.reader(file):
            if not row:
                continue

            match = QUARTER_PATTERN.fullmatch(row[0].strip())
            if not match:
                continue

            quarter = row[0].strip()
            columns = [
                value.strip()
                for value in row[1:]
                if value.strip()
            ]

            if not columns:
                raise ValueError(
                    f"No columns found for {quarter}"
                )

            if len(columns) != len(set(columns)):
                raise ValueError(
                    f"Duplicate column names found in {quarter}"
                )

            schemas[quarter] = columns

    # Sort chronologically, rather than relying on file row order.
    return dict(
        sorted(
            schemas.items(),
            key=lambda item: (
                int(QUARTER_PATTERN.fullmatch(item[0]).group(1)),
                int(QUARTER_PATTERN.fullmatch(item[0]).group(2)),
            ),
        )
    )


def make_summary(previous_name, previous_columns,
                 current_name, current_columns):
    previous_set = set(previous_columns)
    current_set = set(current_columns)

    added = sorted(current_set - previous_set)
    removed = sorted(previous_set - current_set)

    return {
        "comparison": f"{previous_name} -> {current_name}",
        "quarter": current_name,
        "previous_column_count": len(previous_columns),
        "current_column_count": len(current_columns),
        "added_count": len(added),
        "removed_count": len(removed),
        "added_columns": "; ".join(added),
        "removed_columns": "; ".join(removed),
    }


def main():
    if not REFERENCE_FILE.is_file():
        raise FileNotFoundError(
            f"Reference file not found: {REFERENCE_FILE}"
        )

    schemas = read_quarter_schemas()

    if not schemas:
        raise ValueError("No quarterly schemas found.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    quarters = list(schemas.items())

    # Compare Q1 2016 with the first available reference quarter.
    baseline_file = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / "backblaze"
        / "2016_Q1"
    )

    daily_files = sorted(
        path for path in baseline_file.glob("*.csv")
        if not path.name.startswith("._")
    )

    if not daily_files:
        raise FileNotFoundError(
            f"No baseline CSV found in {baseline_file}"
        )

    with daily_files[0].open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        baseline_columns = next(csv.reader(file))

    first_quarter, first_columns = quarters[0]

    rows.append(
        make_summary(
            "Q1 2016",
            baseline_columns,
            first_quarter,
            first_columns,
        )
    )

    # Compare each quarter with the immediately preceding quarter.
    for index in range(1, len(quarters)):
        previous_name, previous_columns = quarters[index - 1]
        current_name, current_columns = quarters[index]

        rows.append(
            make_summary(
                previous_name,
                previous_columns,
                current_name,
                current_columns,
            )
        )

    fieldnames = [
        "comparison",
        "quarter",
        "previous_column_count",
        "current_column_count",
        "added_count",
        "removed_count",
        "added_columns",
        "removed_columns",
    ]

    with OUTPUT_FILE.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=fieldnames
        )
        writer.writeheader()
        writer.writerows(rows)

    print("Schema drift summary created.")
    print(f"Quarters analyzed: {len(schemas)}")
    print(f"Comparisons written: {len(rows)}")
    print(f"Output: {OUTPUT_FILE}")
    print("\nLargest additions between consecutive quarters:")

    largest_changes = sorted(
        rows[1:],
        key=lambda row: row["added_count"],
        reverse=True,
    )[:5]

    for row in largest_changes:
        print(
            f"{row['comparison']}: "
            f"+{row['added_count']} columns, "
            f"-{row['removed_count']} columns"
        )


if __name__ == "__main__":
    main()
