import csv
import io
import zipfile
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_PATH = PROJECT_ROOT / "data" / "raw" / "backblaze" / "data_Q1_2018.zip"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_PATH = REPORT_DIR / "q1_2018_date_mismatch_investigation.txt"

MAX_SAMPLES = 30


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
            "Rename or move it before rerunning to preserve the earlier result."
        )

    total_mismatches = 0
    mismatches_by_file = Counter()
    date_pairs = Counter()
    samples = []
    errors = []

    with zipfile.ZipFile(ARCHIVE_PATH) as archive:
        daily_files = sorted(
            name for name in archive.namelist()
            if is_daily_csv(name)
        )

        for member_name in daily_files:
            filename_date = Path(member_name).name[:10]

            try:
                with archive.open(member_name) as raw_file:
                    text_file = io.TextIOWrapper(
                        raw_file, encoding="utf-8-sig", newline=""
                    )
                    reader = csv.DictReader(text_file)

                    if not {"date", "serial_number"}.issubset(
                        set(reader.fieldnames or [])
                    ):
                        raise ValueError(
                            "Required date or serial_number column is missing"
                        )

                    for row in reader:
                        row_date = (row.get("date") or "").strip()

                        if row_date != filename_date:
                            total_mismatches += 1
                            mismatches_by_file[filename_date] += 1
                            date_pairs[(filename_date, row_date)] += 1

                            if len(samples) < MAX_SAMPLES:
                                samples.append({
                                    "file": Path(member_name).name,
                                    "filename_date": filename_date,
                                    "row_date": row_date or "<blank>",
                                    "serial_number": (
                                        row.get("serial_number") or ""
                                    ).strip(),
                                    "failure": (row.get("failure") or "").strip(),
                                    "model": (row.get("model") or "").strip(),
                                })

            except (UnicodeDecodeError, csv.Error, OSError, ValueError) as error:
                errors.append(
                    f"{member_name}: {type(error).__name__}: {error}"
                )

    report = [
        "Q1 2018 DATE MISMATCH INVESTIGATION",
        "=" * 40,
        f"Daily files discovered: {len(daily_files)}",
        f"Total rows with date/filename mismatch: {total_mismatches:,}",
        f"Files with at least one mismatch: {len(mismatches_by_file)}",
        f"Files with processing errors: {len(errors)}",
        "",
        "MOST COMMON FILENAME DATE -> ROW DATE PAIRS",
        "-" * 40,
    ]

    for (filename_date, row_date), count in date_pairs.most_common(20):
        report.append(
            f"{filename_date} -> {row_date or '<blank>'}: {count:,} rows"
        )

    report.extend([
        "",
        "FILES WITH THE MOST MISMATCHES",
        "-" * 40,
    ])

    for date, count in mismatches_by_file.most_common(20):
        report.append(f"{date}: {count:,} rows")

    report.extend([
        "",
        f"FIRST {len(samples)} MISMATCH EXAMPLES",
        "-" * 40,
    ])

    for sample in samples:
        report.extend([
            f"File: {sample['file']}",
            f"  Filename date: {sample['filename_date']}",
            f"  Row date: {sample['row_date']}",
            f"  Serial number: {sample['serial_number']}",
            f"  Failure: {sample['failure']}",
            f"  Model: {sample['model']}",
        ])

    if errors:
        report.extend(["", "PROCESSING ERRORS", "-" * 40])
        report.extend(errors)

    report.extend([
        "",
        "INTERPRETATION",
        "-" * 40,
        "This report identifies mismatches; it does not determine their cause.",
        "Inspect the date pairs and affected files before deciding whether",
        "the records should be accepted, quarantined, or handled differently.",
    ])

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_text = "\n".join(report) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    print(report_text)
    print(f"\nReport saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
