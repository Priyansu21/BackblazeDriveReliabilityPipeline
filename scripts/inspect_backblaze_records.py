from pathlib import Path
import csv
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "backblaze"
    / "2016_Q1"
)


def get_daily_csv_files():
    """Return actual daily CSVs, excluding macOS metadata."""
    return sorted(
        path
        for path in DATA_DIR.rglob("*.csv")
        if "__MACOSX" not in path.parts
        and not path.name.startswith("._")
    )


def inspect_file(csv_path):
    """Inspect row counts, dates, and duplicate natural keys."""

    # UTF-8 is attempted first; Windows-1252 is a fallback
    # for files that cannot be decoded as UTF-8.
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with csv_path.open(
                "r", encoding=encoding, newline=""
            ) as file:
                reader = csv.reader(file)
                header = next(reader, None)

                if not header:
                    return {
                        "error": "Empty file or missing header"
                    }

                header = [column.strip() for column in header]

                required = {"date", "serial_number"}
                missing = required - set(header)

                if missing:
                    return {
                        "error": f"Missing required columns: {sorted(missing)}"
                    }

                date_idx = header.index("date")
                serial_idx = header.index("serial_number")

                row_count = 0
                duplicate_keys = 0
                missing_keys = 0
                date_mismatches = 0
                observed_dates = set()
                seen_keys = set()

                expected_date = date.fromisoformat(
                    csv_path.stem
                )

                for row in reader:
                    row_count += 1

                    if len(row) <= max(date_idx, serial_idx):
                        missing_keys += 1
                        continue

                    row_date = row[date_idx].strip()
                    serial = row[serial_idx].strip()

                    if not row_date or not serial:
                        missing_keys += 1
                        continue

                    observed_dates.add(row_date)

                    if row_date != expected_date.isoformat():
                        date_mismatches += 1

                    key = (row_date, serial)

                    if key in seen_keys:
                        duplicate_keys += 1
                    else:
                        seen_keys.add(key)

                return {
                    "rows": row_count,
                    "duplicates": duplicate_keys,
                    "missing_keys": missing_keys,
                    "date_mismatches": date_mismatches,
                    "observed_dates": sorted(observed_dates),
                    "encoding": encoding,
                }

        except UnicodeDecodeError:
            # Retry from the beginning using the fallback encoding.
            continue
        except (OSError, csv.Error, ValueError) as error:
            return {"error": str(error)}

    return {"error": "Could not decode file using supported encodings"}


def main():
    if not DATA_DIR.is_dir():
        raise FileNotFoundError(
            f"Dataset folder does not exist: {DATA_DIR}"
        )

    files = get_daily_csv_files()

    if not files:
        raise FileNotFoundError(
            f"No daily CSV files found under: {DATA_DIR}"
        )

    total_rows = 0
    total_duplicates = 0
    total_missing_keys = 0
    total_date_mismatches = 0
    error_count = 0
    fallback_count = 0

    print(f"Dataset folder: {DATA_DIR}")
    print(f"Daily CSV files found: {len(files)}")
    print("\n--- PER-FILE RESULTS ---")

    for csv_path in files:
        result = inspect_file(csv_path)

        if "error" in result:
            error_count += 1
            print(f"{csv_path.name}: ERROR - {result['error']}")
            continue

        total_rows += result["rows"]
        total_duplicates += result["duplicates"]
        total_missing_keys += result["missing_keys"]
        total_date_mismatches += result["date_mismatches"]

        if result["encoding"] != "utf-8-sig":
            fallback_count += 1

        print(
            f"{csv_path.name}: "
            f"rows={result['rows']:,}, "
            f"duplicates={result['duplicates']}, "
            f"missing_keys={result['missing_keys']}, "
            f"date_mismatches={result['date_mismatches']}"
        )

    print("\n--- DATASET SUMMARY ---")
    print(f"Files discovered: {len(files)}")
    print(f"Files with errors: {error_count}")
    print(f"Files using fallback encoding: {fallback_count}")
    print(f"Total rows: {total_rows:,}")
    print(f"Duplicate (date, serial_number) pairs: {total_duplicates:,}")
    print(f"Rows with missing date/serial number: {total_missing_keys:,}")
    print(f"Rows whose date differs from filename: {total_date_mismatches:,}")


if __name__ == "__main__":
    main()
