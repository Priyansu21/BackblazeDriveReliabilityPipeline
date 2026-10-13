from pathlib import Path
import csv

# Project root is the parent of the scripts folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "backblaze"
    / "2016_Q1"
)

# Find daily CSV files, including files inside nested folders.
# csv_files = sorted(DATA_DIR.rglob("*.csv"))
csv_files = sorted(
    path
    for path in DATA_DIR.rglob("*.csv")
    if "__MACOSX" not in path.parts
    and not path.name.startswith("._")
)

if not csv_files:
    raise FileNotFoundError(
        f"No CSV files found under: {DATA_DIR}"
    )

print(f"Dataset folder: {DATA_DIR}")
print(f"CSV files found: {len(csv_files)}")

# The first CSV is our baseline schema.
with csv_files[0].open(
    "r", encoding="utf-8-sig", newline=""
) as file:
    baseline_columns = next(csv.reader(file))

baseline_columns = [
    column.strip() for column in baseline_columns
]

print(f"\nBaseline file: {csv_files[0].name}")
print(f"Baseline column count: {len(baseline_columns)}")

matching_files = 0
different_files = 0

# for csv_file in csv_files:
#     with csv_file.open(
#         "r", encoding="utf-8-sig", newline=""
#     ) as file:
#         columns = next(csv.reader(file))

for csv_file in csv_files:
    try:
        with csv_file.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            columns = next(csv.reader(file))

    except (UnicodeDecodeError, StopIteration) as error:
        print(f"\nCould not inspect: {csv_file.name}")
        print(f"Reason: {error}")
        continue

    columns = [column.strip() for column in columns]

    added = sorted(set(columns) - set(baseline_columns))
    removed = sorted(set(baseline_columns) - set(columns))

    if columns == baseline_columns:
        matching_files += 1
    else:
        different_files += 1
        print(f"\nSchema difference: {csv_file.name}")
        print(f"  Added columns: {added}")
        print(f"  Removed columns: {removed}")

print("\n--- SUMMARY ---")
print(f"Matching schemas: {matching_files}")
print(f"Different schemas: {different_files}")
