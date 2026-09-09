import re
from pathlib import Path

SOURCE_DIR = Path("fide_historical_ratings")
from pathlib import Path


MONTH_ORDER = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}

FILE_NAME_PATTERN = re.compile(
    r"^(?:standard_)?(?P<month>[a-z]{3})(?P<year>\d{2})frl$",
    re.IGNORECASE,
)


def sort_key(path: Path) -> tuple[int, int, str]:
    match = FILE_NAME_PATTERN.match(path.stem)
    if match is None:
        return 9999, 99, path.name

    month_code = match.group("month").upper()
    year = 2000 + int(match.group("year"))
    month = MONTH_ORDER.get(month_code, 99)
    return year, month, path.name

    year = 2000 + int(year_code)
    month = MONTH_ORDER.get(month_code, 99)
    return year, month, path.name


def print_file_head(path: Path) -> None:
    print(path.name)
    with path.open(encoding="utf-8", errors="replace") as handle:
        with open("csv_heads_unformatted.txt", "a", encoding="utf-8") as output_file:
            output_file.write(f"{path.name}\n")
            for _ in range(3):
                line = handle.readline()
                if not line:
                    break
                output_file.write(f"{line.rstrip()}\n")



def main() -> None:
    source_files = sorted(
        [
            path
            for path in SOURCE_DIR.iterdir()
            if path.suffix.lower() in {".txt", ".csv"}
        ],
        key=sort_key,
    )
    for path in source_files:
        print_file_head(path)


if __name__ == "__main__":
    main()
