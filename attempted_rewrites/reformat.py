from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
import os
from typing import Iterable

SRC_DIR = "fide_historical_ratings"
DEST_DIR = "fide_historical_ratings_formatted"

HEADER_COLUMNS = (
    "ID_NUMBER NAME                            TITLE FED  RATING GM  Bday      Flag "
)


def reformat(file_csv: str, lines: list[str]) -> list[str]:
    basename = os.path.basename(file_csv)

    if basename == "OCT02FRL.TXT":
        lines[0] = (
            lines[0]
            .replace("COUNTRY", "  Fed ")
            .replace("GAMES", "Gms")
            .replace("BIRTHDAY", " BIRTHDAY")
        )
    elif basename == "APR03FRL.TXT":
        lines[0] = (
            lines[0]
            .replace("   CODE  ", "ID_NUMBER")
            .replace("COUNTRY", "  FED  ")
            .replace(" APR03", "APR03 ")
            .replace(" GAMES", "GMS   ")
            .replace("  BIRTHDAY", "BIRTHDAY  ")
            .replace(" FLAG", "FLAG ")
        )
    elif basename in {
        "APR04FRL.TXT",
        "JUL04FRL.TXT",
        "OCT04FRL.TXT",
        "JAN05FRL.TXT",
        "JUL05FRL.TXT",
    }:
        lines[0] = (
            lines[0]
            .replace("COUNTRY", "   FED ")
            .replace("GAMES", "GAME ")
            .replace(" BIRTHDAY", "BIRTHDAY")
        )
    elif basename == "JAN06FRL.TXT":
        if len(lines) > 1:
            del lines[1]
    elif _needs_later_header_fix(basename):
        lines[0] = (
            lines[0]
            .replace("Titl", "Tit ")
            .replace("Games", "Game ")
            .replace("July", "Jul")
        )

    lines[0] = (
        lines[0].replace("ID Number", "ID_NUMBER").replace("ID number", "ID_NUMBER")
    )
    return lines


def _needs_later_header_fix(basename: str) -> bool:
    if basename in {"APR06FRL.TXT", "JUL06FRL.TXT", "OCT06FRL.TXT"}:
        return True

    upper = basename.upper()
    if len(upper) < 10:
        return False

    month_code = upper[:3]
    year_code = upper[3:5]
    suffix = upper[5:]
    if month_code not in {
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
    }:
        return False
    if suffix != "FRL.TXT":
        return False

    if year_code in {"07", "08", "09", "10", "11"}:
        return True
    if year_code == "12" and month_code in {"JAN", "FEB", "MAR", "APR", "MAY"}:
        return True
    return False


def indexes(lines: list[str]) -> list[int]:
    column_vector = lines[0]
    indexed: list[int] = []

    for position in range(len(column_vector) - 1):
        if column_vector[position].isspace() and column_vector[position + 1].isalpha():
            indexed.append(position)

    return indexed


def utf_func(text: str, indexed: Iterable[int]) -> str:
    chars = list(text)
    for position in indexed:
        if 0 <= position < len(chars):
            chars[position] = "*"
    return "".join(chars)


def filenamer(year_num: str) -> str:
    token = year_num[-12:-7].upper()
    return os.path.join(DEST_DIR, f"{token}.csv")


def write_csv(filename: str, lines: Iterable[str]) -> None:
    if os.path.exists(filename):
        os.unlink(filename)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")


def all_files_fwrite(year_num: str) -> None:
    source_name = os.path.basename(year_num)
    with open(year_num, encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()

    if source_name in [
        "jul03frl.txt",
        "OCT03FRL.TXT",
        "JAN04FRL.TXT",
        "APR05FRL.TXT",
        "jan03frl.txt"
    ]:
        if lines and lines[0].strip():
            lines.insert(0, "")
        if lines:
            lines[0] = HEADER_COLUMNS
    lines = reformat(source_name, lines)

    indexed = indexes(lines)
    transformed = [utf_func(line, indexed) for line in lines]
    write_csv(filenamer(source_name), transformed)


def multi_processing(year_vector: Iterable[str]) -> None:
    files = list(year_vector)
    if not files:
        return

    workers = max(1, cpu_count())
    with ProcessPoolExecutor(max_workers=workers) as executor:
        list(executor.map(all_files_fwrite, files))


def main() -> None:
    year_num = [
        os.path.join(SRC_DIR, name)
        for name in os.listdir(SRC_DIR)
        if name.lower().endswith("frl.txt")
    ]
    multi_processing(year_num)
    print([name for name in os.listdir(DEST_DIR) if name.lower().endswith(".csv")][:5])


if __name__ == "__main__":
    main()
