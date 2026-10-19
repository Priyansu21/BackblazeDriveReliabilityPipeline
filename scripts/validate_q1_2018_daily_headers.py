import csv
import io
import zipfile
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "backblaze"
REPORT_DIR = PROJECT_ROOT / "reports"

ARCHIVE_PATH = DATA_DIR / "data_Q1_2018.zip"
REPORT_PATH = REPORT_DIR / "q1_2018_daily_header_consistency.txt"


def is_daily_csv(member_name):
    """Identify daily CSVs named YYYY-MM-DD.csv inside the ZIP."""
    name = Path(member_name).name

    if "__macosx" in member_name.lower() or name.startswith("._"):
        return False

    if not name.lower().endswith(".csv"):
        return False

    try:
        date_part = name[:10]
        return (
            len(name) == 14
            and date_part[4] == "-"
            and date_part[7] == "-"
            and name[10:] == ".csv"
        )
    except IndexError:
        return False


def read_header(archive, member_name):
    """Read only the first CSV row without extracting the file."""
    with archive.open(member_name) as raw_file:
        text_file = io.TextIOWrapper(
            raw_file,
            encoding="utf-8-sig",
            newline=""
        )
        return next(csv.reader(text_file))


def main():
    if not ARCHIVE_PATH.exists():
        raise FileNotFoundError(
            f"Q1 2018 archive not found: {ARCHIVE_PATH}"
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(ARCHIVE_PATH) as archive:
        daily_files = sorted(
            name for name in archive.namelist()
            if is_daily_csv(name)
        )

        if not daily_files:
            raise ValueError("No daily CSV files found inside the ZIP.")

        reference_file = daily_files[0]
        reference_header = read_header(archive, reference_file)

        matching_files = []
        mismatches = []
        unreadable_files = []

        for member_name in daily_files:
            try:
                header = read_header(archive, member_name)

                if header == reference_header:
                    matching_files.append(member_name)
                else:
                    missing = sorted(
                        set(reference_header) - set(header)
                    )
                    additional = sorted(
                        set(header) - set(reference_header)
                    )

                    mismatches.append({
                        "file": member_name,
                        "column_count": len(header),
                        "missing": missing,
                        "additional": additional,
                        "same_columns_different_order":
                            set(header) == set(reference_header),
                    })

            except (
                UnicodeDecodeError,
                csv.Error,
                StopIteration,
                OSError,
            ) as error:
                unreadable_files.append(
                    f"{member_name}: {type(error).__name__}: {error}"
                )

    report = [
        "Q1 2018 DAILY HEADER CONSISTENCY REPORT",
        "=" * 42,
        f"Archive: {ARCHIVE_PATH.name}",
        f"Daily CSV files discovered: {len(daily_files)}",
        f"Reference header: {reference_file}",
        f"Reference column count: {len(reference_header)}",
        "",
        "RESULTS",
        "-" * 42,
        f"Files with matching ordered headers: {len(matching_files)}",
        f"Files with different headers: {len(mismatches)}",
        f"Files whose headers could not be read: {len(unreadable_files)}",
    ]

    if len(matching_files) == len(daily_files):
        report.extend([
            "",
            "OVERALL RESULT: PASS",
            "All daily CSV files have the same ordered header.",
        ])
    else:
        report.extend([
            "",
            "OVERALL RESULT: INVESTIGATION REQUIRED",
            "At least one file differs or could not be read.",
        ])

    if mismatches:
        report.extend(["", "HEADER MISMATCH DETAILS", "-" * 42])

        for item in mismatches:
            report.extend([
                f"File: {item['file']}",
                f"Column count: {item['column_count']}",
                f"Missing columns: {item['missing']}",
                f"Additional columns: {item['additional']}",
                "Same columns but different order: "
                f"{item['same_columns_different_order']}",
                "",
            ])

    if unreadable_files:
        report.extend(["", "UNREADABLE FILES", "-" * 42])
        report.extend(unreadable_files)

    report_text = "\n".join(report) + "\n"

    # Create a new report; never silently overwrite an earlier result.
    if REPORT_PATH.exists():
        raise FileExistsError(
            f"Report already exists: {REPORT_PATH}\n"
            "Rename or move the existing report before running again."
        )

    REPORT_PATH.write_text(report_text, encoding="utf-8")

    print(report_text)
    print(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
