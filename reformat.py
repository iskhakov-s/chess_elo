import logging
import os
import csv
from mpi4py import MPI
import numpy as np
import helper
from mpi_logging import mpi_log
from helper import FIDE_CSV_DIR, FIDE_CSV_DIR_2
import mpi_logging

""" Reformats the original files and writes them to FIDE_CSV_DIR_2. 
Specifically, it removes blank rows and removes the first two characters from each row of the CSV files where there is filler.

This is in place of reformat.R, which is no longer used because it's implementation was broken.
"""

# removes first two characters from each row of the csv files
# don't remove if it's a blank line
# don't run with mpi
def remove_first_two_chars():
    logging.basicConfig(
        filename=os.path.join("logs", f"remove_first_two_chars.log"),
        filemode='a',  # 'a' to append, 'w' to overwrite
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
    )
    for csv_name in "JAN01.csv", "APR01.csv", "JUL01.csv", "OCT01.csv", "JAN02.csv", "APR02.csv", "JUL02.csv":
        csv_path = os.path.join(FIDE_CSV_DIR_2, csv_name)
        error_rows = 0
        success_rows = 0
        with open(csv_path, "r") as f:
            lines = f.readlines()
        with open(csv_path, "w") as f:
            for line in lines:
                if line.strip() != "":
                    f.write(line[2:])
                    success_rows += 1
                else:
                    error_rows += 1
        logging.info(f"{csv_name}: Success rows: {success_rows}, Error rows: {error_rows}")
    
    logging.shutdown()

def remove_blank_lines(month_names: list[dict[str, str]], rank):
    for month_data in month_names:
        blank_rows = 0
        with open(os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"]), "r") as rf:
            with open(os.path.join("fide_historical_ratings_rereformatted", month_data["csv_name"]), "w") as wf:
                for line in rf:
                    if line.strip() != "":
                        wf.write(line)
                    else:
                        blank_rows += 1
        mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: Removed {blank_rows:<3} blank rows")


# only needed for apr04-jan08
def remove_x1a(month_names: list[dict[str, str]], rank):
    for month_data in month_names:
        removed_rows = 0
        with open(os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"]), "r") as rf:
            with open(os.path.join("fide_historical_ratings_rereformatted", month_data["csv_name"]), "w") as wf:
                for line in rf:
                    if '\x1a' in line:
                        removed_rows += 1
                    else:
                        wf.write(line)
        mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: Removed {removed_rows:<3} rows with \\x1a")


def remove_runs(lst):
    no_runs = []
    for i in range(len(lst)-1, -1, -1):
        if i == 0:
            if lst[0] != 0:
                no_runs.append(lst[0])
            break
        if lst[i] != lst[i-1] + 1:
            no_runs.append(lst[i])
    return no_runs[::-1]

def find_blank_columns(file_path: str) -> list[int]:
    """ find blank columns to insert the "commas" 

    Args:
        file_path

    Returns:
        list[int]: A list of indices representing the blank columns. 
    """    
    with open(file_path, "r", encoding="utf-8", errors="replace") as file:
        is_header = True
        blank_columns = []
        for line in file:
            if line.strip() == "":
                continue
            if is_header:
                is_header = False
                blank_columns = list(range(len(line)))
                continue
            new_blank_columns = blank_columns.copy()
            for i in blank_columns:
                if i >= len(line):
                    break
                if line[i].strip() != "":
                    new_blank_columns.remove(i)
            blank_columns = new_blank_columns
            if blank_columns == []:
                break
        
    return remove_runs(blank_columns)

def insert_asterisks(line: str, blank_columns: list[int]) -> str:
    char_list = list(line)
    for index in blank_columns:
        if index < len(char_list):
            char_list[index] = "*"
    return "".join(char_list)


def find_blank_columns_mpi(month_names: list[dict[str, str]], rank):
    for month_data in month_names:
        with open(os.path.join(helper.SRC_DIR, month_data["src_name"]), "r", encoding="utf-8", errors="replace") as f:
            blank_columns = find_blank_columns(os.path.join(helper.SRC_DIR, month_data["src_name"]))
            mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: {insert_asterisks(f.readline(), blank_columns)}")
            mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: {insert_asterisks(f.readline(), blank_columns)}")

def find_mostly_blank_columns_mpi(month_names: list[dict[str, str]], rank):
    for month_data in month_names:
        non_blank_counts = {}
        with open(os.path.join(helper.SRC_DIR, month_data["src_name"]), "r", encoding="utf-8", errors="replace") as f:
            is_header = True
            for line in f:
                if line.strip() == "":
                    continue
                if is_header:
                    is_header = False
                    non_blank_counts = [0] * len(line)
                    # mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: Num columns: {len(line)}")
                    continue
                for i in range(len(line)):
                    if line[i].strip() != "":
                        non_blank_counts[i] += 1
            f.seek(0)
            for _ in range(3):
                next(f)
            mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: {f.readline()}")
        output= "".join(["X" if count==0 else "x" if count < 100 else "_" for count in non_blank_counts])
        mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: {output}")
        


def check_blank_columns():
    mpi_logging.log_setup("otit_collisions_2016_2026", format="%(message)s")
    month_data = helper.get_period_range(2016, 9, 2026, 12)
    # col_str = "_________XXXXXX____________________________________________________________X___X_XXX___XX___XX______________x___X____XX__XX__X____XX__XXX"
    # columns = [i for i, s in enumerate(col_str) if s.upper() == "X"]
    
    columns = [14, 75, 79, 83, 88, 93, 108, 112, 118, 122, 125, 131]
    col_str = "".join(["X" if i in columns else "_" for i in range(132)])
    logging.info(f"Columns: {columns}")
    for month_data in month_data:
        count = 0
        logging.info(f"{month_data['year']}-{month_data['month']}:")
        with open(os.path.join("fide_historical_ratings", month_data["src_name"]), "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() == "":
                    continue
                for i in columns:
                    if i>=len(line):
                        break
                    if line[i].strip() != "":
                        logging.info(f"\t{line}")
                        logging.info(f"\t{col_str}")
                        count += 1
                        break
        logging.info(f"\t{count=}")
    
def find_broken_chars():
    month_data = helper.get_single_period(2004, "apr")
    with open(os.path.join("fide_historical_ratings", month_data["src_name"]), "r", encoding="latin1") as f:
        for line in f:
            if "1708228" in line:
                print(line, end="")


def reformat_mpi(month_names: list[dict[str, str]], rank):
    for month_data in month_names:
        with open(os.path.join(helper.SRC_DIR, month_data["src_name"]), "r", encoding="utf-8", errors="replace") as rf:
            with open(os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"]), "w", newline="", encoding="utf-8") as wf:
                # get columns to insert asterisks into
                blank_columns = find_blank_columns(os.path.join(helper.SRC_DIR, month_data["src_name"]))
                mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: Blank columns: {blank_columns}")
                rf.seek(0)
                
                # exclude asterisk if it's one of the last 5 chars (needed for apr08-aug16 due to ragged flag column)
                # caution when running on other files, may remove necessary value separators
                header_len = len(rf.readline())
                blank_columns = [i for i in blank_columns if i < header_len - 5]
                rf.seek(0)
                
                for line in rf:
                    if line.strip() == "" or "\x1a" in line:
                        continue
                    new_line = insert_asterisks(line, blank_columns)
                    if not new_line.endswith(("\n", "\r\n")):
                        new_line += "\n"
                    wf.write(new_line)
        # mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: Reformatted {month_data['csv_name']}")
        


def reformat_mpi_type_5(month_names: list[dict[str, str]], rank):
    # manually insert the type 5, ie 2016sep-present columns because otitle is broken in some of the files
    blank_columns = [14, 75, 79, 83, 88, 93, 108, 112, 118, 122, 125, 131]
    
    for month_data in month_names:
        with open(os.path.join(helper.SRC_DIR, month_data["src_name"]), "r", encoding="utf-8", errors="replace") as rf:
            with open(os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"]), "w", newline="", encoding="utf-8") as wf:
                mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: Blank columns: {blank_columns}")
                rf.seek(0)
                for line in rf:
                    if line.strip() == "":
                        continue
                    # if the 108th character is blank that means otitle is too long, skip the line and log it
                    if line[108].strip() != "":
                        mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: {line}")
                        continue
                    new_line = insert_asterisks(line, blank_columns)
                    if not new_line.endswith(("\n", "\r\n")):
                        new_line += "\n"
                    wf.write(new_line)
        # mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: Reformatted {month_data['csv_name']}")        



# mpiexec -n 8 python -u reformat.py
if __name__ == "__main__":
    # helper.mpi_main(reformat_mpi, "reformat2016_2026", get_period_range_kwargs={"start_year": 2016, "start_month": "sep", "end_year": 2026, "end_month": "aug"})
    # check_blank_columns()
    # print(remove_runs([0, 10, 44, 47, 54, 63, 68, 74]))
    helper.mpi_main(reformat_mpi, "reformat_ragged", get_period_range_kwargs={"start_year": 2008, "start_month": "apr", "end_year": 2016, "end_month": "aug"})