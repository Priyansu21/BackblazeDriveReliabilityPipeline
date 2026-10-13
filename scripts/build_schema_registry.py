from pathlib import Path
import csv
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BASELINE_DIR = (
    PROJECT_ROOT / "data" / "raw" / "backblaze" / "2016_Q1"
)

REFERENCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "backblaze"
    / "reference"
    / "Drive_Stats_Schema_2018_Onward.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "reports"
OUTPUT_FILE = OUTPUT_DIR / "schema_registry.csv"

QUARTER_PATTERN = re.compile(r"^(\d{4})\s+Q([1-4])$")


def read_header(file_path):
    with file_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        return [
            name.strip()
            for name in next(csv.reader(file))
            if name.strip()
        ]


def read_reference_schemas():
    schemas = {}

    with REFERENCE_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        for row in csv.reader(file):
            if not row:
                continue

            period = row[0].strip()

            if not QUARTER_PATTERN.fullmatch(period):
                continue

            columns = [
                value.strip()
                for value in row[1:]
                if value.strip()
            ]

            if not columns:
                raise ValueError(
                    f"No columns found for {period}"
                )

            if len(columns) != len(set(columns)):
                raise ValueError(
                    f"Duplicate columns found in {period}"
                )

            schemas[period] = columns

    return dict(
        sorted(
            schemas.items(),
            key=lambda item: (
                int(QUARTER_PATTERN.fullmatch(item[0]).group(1)),
                int(QUARTER_PATTERN.fullmatch(item[0]).group(2)),
            ),
        )
    )


def main():
    if not REFERENCE_FILE.is_file():
        raise FileNotFoundError(REFERENCE_FILE)

    baseline_files = sorted(
        path for path in BASELINE_DIR.glob("*.csv")
        if not path.name.startswith("._")
    )

    if not baseline_files:
        raise FileNotFoundError(
            f"No baseline CSV found in {BASELINE_DIR}"
        )

    baseline_columns = read_header(baseline_files[0])
    schemas = {"Q1 2016": baseline_columns}
    schemas.update(read_reference_schemas())

    # Record the periods in which each column is present.
    column_periods = {}

    for period, columns in schemas.items():
        for column in columns:
            column_periods.setdefault(column, []).append(period)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "column_name",
        "present_in_q1_2016",
        "first_observed_period",
        "last_observed_period",
        "periods_present_count",
        "periods_observed_count",
        "observed_periods",
    ]

    with OUTPUT_FILE.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for column, periods in sorted(column_periods.items()):
            writer.writerow({
                "column_name": column,
                "present_in_q1_2016": (
                    "true" if column in baseline_columns else "false"
                ),
                "first_observed_period": periods[0],
                "last_observed_period": periods[-1],
                "periods_present_count": len(periods),
                "periods_observed_count": len(schemas),
                "observed_periods": "; ".join(periods),
            })

    print("Initial schema registry created.")
    print(f"Periods examined: {len(schemas)}")
    print(f"Unique column names: {len(column_periods)}")
    print(f"Output: {OUTPUT_FILE}")
    print(
        "Note: first_observed_period means first seen in "
        "the periods examined, not necessarily when introduced."
    )


if __name__ == "__main__":
    main()
