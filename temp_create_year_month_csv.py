from __future__ import annotations

import csv
import re
from pathlib import Path

MONTH_TO_NUMBER = {
    "JAN": "01",
    "FEB": "02",
    "MAR": "03",
    "APR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AUG": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DEC": "12",
}


def extract_date_parts(filename: str):
    match = re.fullmatch(r"(?P<month3>[A-Za-z]{3})(?P<year2>\d{2})", filename)
    if not match:
        return None
    return (
        match.group("month3"),
        match.group("year2"),
    )


def find_source_file(source_dir: Path, csv_stem: str) -> Path:
    matching_files = [
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.name.lower().endswith(f"{csv_stem.lower()}frl.txt")
    ]
    if not matching_files:
        raise ValueError(
            f"Expected at least one source file for {csv_stem!r}, found 0"
        )

    longest_name_length = max(len(path.name) for path in matching_files)
    longest_matching_files = [
        path for path in matching_files if len(path.name) == longest_name_length
    ]
    if len(longest_matching_files) != 1:
        raise ValueError(
            f"Expected a single longest source file for {csv_stem!r}, found {len(longest_matching_files)}: "
            + ", ".join(path.name for path in longest_matching_files)
        )
    return longest_matching_files[0]


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    source_dir = base_dir / "fide_historical_ratings_formatted"
    raw_source_dir = base_dir / "fide_historical_ratings"
    output_file = base_dir / "months_with_data.csv"

    rows = []
    i = 0
    for csv_path in sorted(source_dir.glob("*.csv")):
        parts = extract_date_parts(csv_path.stem)
        if parts is None:
            continue

        month3, year2 = parts
        year4 = f"20{year2}"
        month2 = MONTH_TO_NUMBER.get(month3.upper())
        if month2 is None:
            continue
        src_path = find_source_file(raw_source_dir, csv_path.stem)
        with open(csv_path, "r") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            csv_rows = sum(1 for _ in reader)

            blank_rows = 0
            f.seek(0)
            for row in f:
                if row.strip() == "":
                    blank_rows += 1
        rows.append(
            {
                "csv_name": csv_path.name,
                "src_name": src_path.name,
                "year_2": year2,
                "month_3": month3,
                "year_4": year4,
                "month_2": month2,
                "num_rows": csv_rows - blank_rows,
            }
        )
        print(
            f"{i}/218; {csv_path.name} -> {src_path.name}: "
            f"{csv_rows} rows, {blank_rows} blank rows, {csv_rows - blank_rows} valid rows"
        )
        i += 1

    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "csv_name",
                "src_name",
                "year_2",
                "month_3",
                "year_4",
                "month_2",
                "num_rows",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
