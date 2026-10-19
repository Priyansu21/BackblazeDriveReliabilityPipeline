
import csv
import io
import zipfile
from datetime import datetime
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_PATH = (
    PROJECT_ROOT / "data" / "raw" / "backblaze" / "data_Q1_2018.zip"
)
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_PATH = REPORT_DIR / "q1_2018_date_format_validation.txt"

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%y")


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


def parse_date(value):
    """Parse supported date formats into a date object."""
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), date_format).date()
        except ValueError:
            continue
    return None


def main():
    if not ARCHIVE_PATH.exists():
        raise FileNotFoundError(f"Archive not found: {ARCHIVE_PATH}")

    if REPORT_PATH.exists():
        raise FileExistsError(
            f"Report already exists: {REPORT_PATH}\n"
            "Rename or move the report before rerunning."
        )

    total_rows = 0
    parse_failures = 0
    dates_not_matching_filename = 0
    formats = Counter()
    examples = []

    with zipfile.ZipFile(ARCHIVE_PATH) as archive:
        daily_files = sorted(
            name for name in archive.namelist()
            if is_daily_csv(name)
        )

        for member_name in daily_files:
            filename_date = datetime.strptime(
                Path(member_name).name[:10], "%Y-%m-%d"
            ).date()

            with archive.open(member_name) as raw_file:
                text_file = io.TextIOWrapper(
                    raw_file, encoding="utf-8-sig", newline=""
                )
                reader = csv.DictReader(text_file)

                for row in reader:
                    total_rows += 1
                    raw_date = (row.get("date") or "").strip()

                    if not raw_date:
                        formats["<blank>"] += 1
                        parse_failures += 1
                        continue

                    formats[raw_date] += 1
                    parsed_date = parse_date(raw_date)

                    if parsed_date is None:
                        parse_failures += 1
                        if len(examples) < 20:
                            examples.append(
                                f"Unparseable date: file={member_name}, "
                                f"value={raw_date!r}"
                            )
                        continue

                    if parsed_date != filename_date:
                        dates_not_matching_filename += 1
                        if len(examples) < 20:
                            examples.append(
                                f"Date mismatch: file={member_name}, "
                                f"value={raw_date!r}, parsed={parsed_date}"
                            )

    report = [
        "Q1 2018 DATE FORMAT VALIDATION",
        "=" * 38,
        f"Daily files inspected: {len(daily_files)}",
        f"Total rows inspected: {total_rows:,}",
        f"Rows with unparseable or blank dates: {parse_failures:,}",
        f"Parsed dates differing from filename date: "
        f"{dates_not_matching_filename:,}",
        "",
        "DATE FORMAT / VALUE FREQUENCIES",
        "-" * 38,
    ]

    # Summarize by representation, rather than printing millions of dates.
    format_summary = Counter()
    for value, count in formats.items():
        if value == "<blank>":
            label = "<blank>"
        elif parse_date(value) is None:
            label = "<unrecognized format>"
        elif "/" in value:
            label = "M/D/YY"
        else:
            label = "YYYY-MM-DD"
        format_summary[label] += count

    report.extend(
        f"{label}: {count:,} rows"
        for label, count in sorted(format_summary.items())
    )

    if examples:
        report.extend(["", "EXAMPLES", "-" * 38])
        report.extend(examples)

    if parse_failures == 0 and dates_not_matching_filename == 0:
        report.extend([
            "",
            "OVERALL RESULT: PASS",
            "All row dates parse and match their filename dates.",
        ])
    else:
        report.extend([
            "",
            "OVERALL RESULT: INVESTIGATION REQUIRED",
            "Some dates could not be parsed or did not match filenames.",
        ])

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_text = "\n".join(report) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    print(report_text)
    print(f"\nReport saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
