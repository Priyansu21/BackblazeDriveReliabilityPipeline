import csv
import io
import zipfile
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "backblaze"
ARCHIVE_PATH = DATA_DIR / "data_Q1_2018.zip"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_PATH = REPORT_DIR / "q1_2018_data_quality.txt"


def is_daily_csv(member_name):
    name = Path(member_name).name
    return (
        len(name) == 14
        and name.endswith(".csv")
        and name[4] == "-"
        and name[7] == "-"
        and name[:10].count("-") == 2
        and "__macosx" not in member_name.lower()
        and not name.startswith("._")
    )


def main():
    if not ARCHIVE_PATH.exists():
        raise FileNotFoundError(f"Archive not found: {ARCHIVE_PATH}")

    if REPORT_PATH.exists():
        raise FileExistsError(
            f"Report already exists: {REPORT_PATH}\n"
            "Move or rename it before rerunning to preserve the old result."
        )

    total_rows = 0
    duplicate_keys = 0
    missing_date = 0
    missing_serial = 0
    filename_date_mismatches = 0
    failure_values = Counter()
    model_counts = Counter()
    serial_numbers = set()
    file_errors = []
    daily_counts = []

    with zipfile.ZipFile(ARCHIVE_PATH) as archive:
        daily_files = sorted(
            name for name in archive.namelist()
            if is_daily_csv(name)
        )

        for member_name in daily_files:
            filename_date = Path(member_name).name[:10]
            rows_in_file = 0
            seen_keys = set()

            try:
                with archive.open(member_name) as raw_file:
                    text_file = io.TextIOWrapper(
                        raw_file, encoding="utf-8-sig", newline=""
                    )
                    reader = csv.DictReader(text_file)

                    required = {"date", "serial_number", "failure", "model"}
                    available = set(reader.fieldnames or [])
                    missing_columns = required - available

                    if missing_columns:
                        raise ValueError(
                            f"Missing required columns: {sorted(missing_columns)}"
                        )

                    for row in reader:
                        rows_in_file += 1
                        total_rows += 1

                        date_value = (row.get("date") or "").strip()
                        serial = (row.get("serial_number") or "").strip()

                        if not date_value:
                            missing_date += 1
                        elif date_value != filename_date:
                            filename_date_mismatches += 1

                        if not serial:
                            missing_serial += 1

                        if date_value and serial:
                            key = (date_value, serial)
                            if key in seen_keys:
                                duplicate_keys += 1
                            else:
                                seen_keys.add(key)

                        if serial:
                            serial_numbers.add(serial)

                        model = (row.get("model") or "").strip()
                        if model:
                            model_counts[model] += 1

                        failure = (row.get("failure") or "").strip()
                        failure_values[failure or "<blank>"] += 1

                daily_counts.append((filename_date, rows_in_file))

            except (UnicodeDecodeError, csv.Error, OSError, ValueError) as error:
                file_errors.append(f"{member_name}: {type(error).__name__}: {error}")

    report = [
        "Q1 2018 DATA QUALITY PROFILE",
        "=" * 38,
        f"Archive: {ARCHIVE_PATH.name}",
        f"Daily CSV files discovered: {len(daily_files)}",
        f"Files processed successfully: {len(daily_counts)}",
        f"Files with errors: {len(file_errors)}",
        f"Total observations processed: {total_rows:,}",
        "",
        "KEY QUALITY CHECKS",
        "-" * 38,
        f"Duplicate (date, serial_number) keys: {duplicate_keys:,}",
        f"Rows with missing date: {missing_date:,}",
        f"Rows with missing serial_number: {missing_serial:,}",
        f"Rows whose date differs from filename: {filename_date_mismatches:,}",
        "",
        "PROFILE METRICS",
        "-" * 38,
        f"Distinct nonblank serial numbers: {len(serial_numbers):,}",
        f"Distinct nonblank models: {len(model_counts):,}",
        f"Failure values: {dict(sorted(failure_values.items()))}",
        f"Rows with failure=1: {failure_values.get('1', 0):,}",
    ]

    if daily_counts:
        report.extend([
            "",
            "DAILY OBSERVATION COUNTS",
            "-" * 38,
            f"First daily file: {daily_counts[0][0]} — {daily_counts[0][1]:,}",
            f"Last daily file: {daily_counts[-1][0]} — {daily_counts[-1][1]:,}",
            f"Minimum daily count: {min(count for _, count in daily_counts):,}",
            f"Maximum daily count: {max(count for _, count in daily_counts):,}",
        ])

    report.extend([
        "",
        "TOP 10 MODELS BY OBSERVATION COUNT",
        "-" * 38,
    ])
    report.extend(
        f"{model}: {count:,}"
        for model, count in model_counts.most_common(10)
    )

    if file_errors:
        report.extend(["", "FILE ERRORS", "-" * 38])
        report.extend(file_errors)

    report.extend([
        "",
        "INTERPRETATION",
        "-" * 38,
        "Failure=1 counts are observations marked as failures, not a failure rate.",
        "Model counts are observations, not distinct drives per model.",
        "Duplicate-key checks are within each daily file; a drive appearing",
        "on different dates is expected.",
    ])

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("\n".join(report))
    print(f"\nReport saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
