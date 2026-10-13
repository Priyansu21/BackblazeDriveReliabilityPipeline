from pathlib import Path
import csv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REFERENCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "backblaze"
    / "reference"
    / "Drive_Stats_Schema_2018_Onward.csv"
)


def main():
    if not REFERENCE_FILE.is_file():
        raise FileNotFoundError(
            f"Schema reference not found: {REFERENCE_FILE}"
        )

    # Try common text encodings without loading the whole file.
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with REFERENCE_FILE.open(
                "r", encoding=encoding, newline=""
            ) as file:
                reader = csv.reader(file)

                header = next(reader, None)
                if header is None:
                    raise ValueError("Reference file is empty.")

                print(f"File: {REFERENCE_FILE.name}")
                print(f"Encoding: {encoding}")
                print(f"Reference columns: {len(header)}")
                print("\nColumn names:")

                for index, column in enumerate(header, start=1):
                    print(f"  {index}. {column}")

                print("\nFirst 10 data rows:")
                for row_number, row in enumerate(reader, start=1):
                    print(f"  {row_number}: {row}")

                    if row_number == 10:
                        break

            return

        except UnicodeDecodeError:
            continue

    raise UnicodeError(
        "Could not decode the schema reference file."
    )


if __name__ == "__main__":
    main()
