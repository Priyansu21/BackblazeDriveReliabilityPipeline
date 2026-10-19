
import csv
import io
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data" / "raw" / "backblaze"
REFERENCE_FILE = (
    DATA_DIR / "reference" / "Drive_Stats_Schema_2018_Onward.csv"
)
BASELINE_FILE = DATA_DIR / "2016_Q1" / "2016-01-01.csv"
REPORT_FILE = PROJECT_ROOT / "reports" / "actual_schema_validation_2018_q1.txt"


def read_csv_header(file_path):
    """Read only the header from a daily CSV."""
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        return next(csv.reader(file))


def read_reference_schema(reference_file, target_quarter):
    """Find a quarter's column names in Backblaze's schema reference."""
    with reference_file.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        for row in csv.reader(file):
            if row and row[0].strip() == target_quarter:
                return [column.strip() for column in row[1:] if column.strip()]

    raise ValueError(f"{target_quarter} was not found in the schema reference.")


def main():
    if not BASELINE_FILE.exists():
        raise FileNotFoundError(f"Missing baseline file: {BASELINE_FILE}")

    if not REFERENCE_FILE.exists():
        raise FileNotFoundError(f"Missing schema reference: {REFERENCE_FILE}")

    archives = [
        path
        for path in DATA_DIR.glob("*.zip")
        if "2018" in path.name.lower()
        and ("q1" in path.name.lower() or "1" in path.name.lower())
    ]

    if len(archives) != 1:
        raise FileNotFoundError(
            "Expected exactly one Q1 2018 ZIP in "
            f"{DATA_DIR}. Found: {[p.name for p in archives]}"
        )

    archive_path = archives[0]

    with zipfile.ZipFile(archive_path) as archive:
        daily_csvs = [
            name for name in archive.namelist()
            if Path(name).name[:10].count("-") == 2
            and name.lower().endswith(".csv")
            and "__macosx" not in name.lower()
            and not Path(name).name.startswith("._")
        ]

        if not daily_csvs:
            raise ValueError("No daily CSV files found inside the ZIP.")

        # One representative daily file is sufficient for header inspection.
        sample_name = sorted(daily_csvs)[0]

        with archive.open(sample_name) as raw_file:
            text_file = io.TextIOWrapper(raw_file, encoding="utf-8-sig")
            actual_2018 = next(csv.reader(text_file))

    baseline_2016 = read_csv_header(BASELINE_FILE)
    documented_2018 = read_reference_schema(
        REFERENCE_FILE, "2018 Q1"
    )

    baseline_set = set(baseline_2016)
    actual_set = set(actual_2018)
    documented_set = set(documented_2018)

    report = [
        "BACKBLAZE ACTUAL SCHEMA VALIDATION",
        "=" * 40,
        f"Archive: {archive_path.name}",
        f"Sample CSV inside archive: {sample_name}",
        f"Daily CSV files in archive: {len(daily_csvs)}",
        "",
        f"Q1 2016 baseline columns: {len(baseline_2016)}",
        f"Actual Q1 2018 sample columns: {len(actual_2018)}",
        f"Documented Q1 2018 columns: {len(documented_2018)}",
        "",
        "ACTUAL Q1 2018 VS Q1 2016",
        f"Added: {len(actual_set - baseline_set)}",
        f"Removed: {len(baseline_set - actual_set)}",
        f"Added columns: {sorted(actual_set - baseline_set)}",
        f"Removed columns: {sorted(baseline_set - actual_set)}",
        "",
        "ACTUAL Q1 2018 VS DOCUMENTED Q1 2018",
        f"Actual-only columns: {sorted(actual_set - documented_set)}",
        f"Documented-only columns: {sorted(documented_set - actual_set)}",
        f"Exact ordered match: {actual_2018 == documented_2018}",
        f"Same columns, possibly different order: {actual_set == documented_set}",
    ]

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("\n".join(report))
    print(f"\nReport saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()
