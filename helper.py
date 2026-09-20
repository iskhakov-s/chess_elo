"""Useful constants and functions used in multiple files.
"""

import csv
import os
from mpi4py import MPI

import mpi_logging

FIDE_CSV_DIR = "fide_historical_ratings_formatted"
# secondary directory used to make edits and formatting changes to the CSV files without affecting the original files in FIDE_CSV_DIR
FIDE_CSV_DIR_2 = "fide_historical_ratings_reformatted"
SRC_DIR = "fide_historical_ratings"

MONTH_INT2STR = {
    1: "jan",
    2: "feb",
    3: "mar",
    4: "apr",
    5: "may",
    6: "jun",
    7: "jul",
    8: "aug",
    9: "sep",
    10: "oct",
    11: "nov",
    12: "dec"
}

MONTH_STR2INT = {v: k for k, v in MONTH_INT2STR.items()}


def get_table_data() -> list[dict[str, str]]:
    """returns the contents of months_with_data.csv as a list of dicts, sorted by year then month (table_name, csv_name, year4, month_digits, num_rows)

    Returns:
        list[dict[str, str]]: list of dictionaries, where each dictionary stores data for a month as strings:
            - "table_name": the name of the SQL table corresponding to the month
            - "csv_name": the name of the CSV file for the month
            - "year": year, two-digit format
            - "month": month, three-letter format
            - "year4": year, four-digit format
            - "month_digits": month, two-digit format (i.e., "01" for January)
            - "num_rows": the number of rows in the CSV file for the month, excluding the header row
    """    
    output = []
    with open(os.path.join("logs", "months_with_data.csv"), "r") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            csv_name, src_name, year, month, year4, month_digits, num_rows = row
            table_name = f"staging_{year}_{month.lower()}"
            output.append({"table_name": table_name, 
                           "csv_name": csv_name, 
                           "src_name": src_name,   
                           "year": year, 
                           "month": month, 
                           "year4": year4,
                           "month_digits": month_digits,
                           "num_rows": num_rows,
                           })
    
    output.sort(key=lambda x: (x["year4"], x["month_digits"]))
    return output

def get_single_period(year: int, month: int | str, table_data=None) -> dict[str, str]:
    if table_data is None:
        table_data = get_table_data()
        
    if isinstance(month, str):
        month = MONTH_STR2INT[month.lower()]

    for month_data in table_data:
        if int(month_data["year4"]) == year and int(month_data["month_digits"]) == month:
            return month_data

    raise ValueError(f"No data found for year {year} and month {month}.")

def get_period_range(start_year: int, start_month: int | str, end_year: int, end_month: int | str, table_data=None) -> list[dict[str, str]]:
    if table_data is None:
        table_data = get_table_data()
        
    if isinstance(start_month, str):
        start_month = MONTH_STR2INT[start_month.lower()]
    if isinstance(end_month, str):
        end_month = MONTH_STR2INT[end_month.lower()]

    output = []
    for month in table_data:
        if int(month["year4"]) > start_year or (int(month["year4"]) == start_year and int(month["month_digits"]) >= start_month):
            if int(month["year4"]) < end_year or (int(month["year4"]) == end_year and int(month["month_digits"]) <= end_month):
                output.append(month)

    return output



def get_type_dict(table_data: list[dict[str, str]]=None) -> dict[tuple[str, str], int]:
    """Returns a mapping from the month to the table columns type. Mainly used for table import into MySQL.

    Args:
        table_data (list[dict[str, str]]): output of get_table_data(), if not provided it will be called to get the data

    Returns:
        dict[tuple[int, int], int]: a tuple of (year, month) mapped to the type of the table (1-5)
    """
    if table_data is None:
        table_data = get_table_data()
    
    type_dict = {
        ("2001", "JAN"): 1,
        ("2001", "APR"): 2,
        ("2002", "JAN"): 2,
        ("2001", "JUL"): 3,
        ("2001", "OCT"): 3,
        ("2002", "APR"): 3,
    }
    
    for month_data in get_period_range(2002, "JUL", 2012, "AUG", table_data=table_data):
        type_dict[(month_data["year4"], month_data["month"])] = 2
    for month_data in get_period_range(2012, "SEP", 2016, "AUG", table_data=table_data):
        type_dict[(month_data["year4"], month_data["month"])] = 4
    for month_data in get_period_range(2016, "SEP", 2026, "APR", table_data=table_data):
        type_dict[(month_data["year4"], month_data["month"])] = 5

    return type_dict


def find_optimal_split(month_names: list[dict[str, str]], size: int) -> tuple[int, int]:
    """
    finds the optimal split of the month_names list for MPI distribution, based on the number of rows in each CSV file. The goal is to balance the workload across MPI processes. assumes O(n) time complexity for each processor's computation over the rows for a given month. (calculation would be different for O(n^2) or O(n log n) time complexity. but, for simplicity we assume O(n) here because it lets us split on the number of rows. this is also generally accurate.)
    Use `[month_names[j] for j in bags[rank]]` to get the slice of month_names for a given rank.

    Args:
        month_names (list[dict[str, str]]): list of dictionaries containing month data
        size (int): number of MPI processes

    Returns:
        tuple[int, int]: tuple containing the start and end indices for the current process
    """
    row_counts = [int(month_data["num_rows"]) for month_data in month_names]
    items = sorted(enumerate(row_counts), key=lambda x: x[1], reverse=True)

    bags = [[] for _ in range(size)]
    sums = [0] * size

    for index, value in items:
        # Find bag with smallest current sum
        bag = min(range(size), key=lambda i: sums[i])

        bags[bag].append(index)
        sums[bag] += value

    return bags, sums

def mpi_main(function: callable, log_name: str, get_period_range_kwargs=None, mpi_log_kwargs=None):
    """calls a function on each csv/sql table independently and produces a sorted output log

    Args:
        function (callable): the function that the processors run on each csv/sql table. the function must take two arguments: a list of month_names and the rank of the processor. the function should log its output using mpi_log(rank, message)
        log_name (str): the name of the log file. 
    """    
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size
    
    mpi_logging.mpi_log_setup(rank, log_name, **(mpi_log_kwargs or {}))
    
    if rank == 0:
        month_names = get_table_data()
        if get_period_range_kwargs is not None:
            month_names = get_period_range(**get_period_range_kwargs, table_data=month_names)
        bags, _ = find_optimal_split(month_names, size)
        # print(f"Root: Completed reading {len(month_names)} SQL/CSV names.")
    else:
        month_names = None
        bags = None

    month_names = comm.bcast(month_names, root=0)
    bags = comm.bcast(bags, root=0)
    
    if len(month_names) != 0:
        function([month_names[j] for j in bags[rank]], rank)
    
    comm.Barrier()
    mpi_logging.mpi_combine_logs(rank, log_name)
    
    
if __name__ == "__main__":
    print(get_type_dict())