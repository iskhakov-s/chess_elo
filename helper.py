"""Useful constants and functions used in multiple files.
"""

import csv
import os

FIDE_CSV_DIR = "fide_historical_ratings_formatted"
# secondary directory used to make edits and formatting changes to the CSV files without affecting the original files in FIDE_CSV_DIR
FIDE_CSV_DIR_2 = "fide_historical_ratings_reformatted"

def get_table_data() -> list[dict[str, str]]:
    """returns the contents of months_with_data.csv as a list of dicts, sorted by year then month (table_name, csv_name, year4, month_digits, num_rows)

    Returns:
        list[dict[str, str]]: list of dictionaries, where each dictionary stores data for a month as strings:
            - "table_name": the name of the SQL table corresponding to the month
            - "csv_name": the name of the CSV file for the month
            - "year": the year of the data
            - "month": the month of the data
            - "year4": the year in four-digit format
            - "month_digits": the month in two-digit format (e.g., "01" for January)
            - "num_rows": the number of rows in the CSV file for the month, excluding the header row
    """    
    output = []
    with open(os.path.join("logs", "months_with_data.csv"), "r") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            csv_name, year, month, year4, month_digits, num_rows = row
            table_name = f"staging_{year}_{month.lower()}"
            output.append({"table_name": table_name, 
                           "csv_name": csv_name, 
                           "year": year, 
                           "month": month, 
                           "year4": year4,
                           "month_digits": month_digits,
                           "num_rows": num_rows,
                           })
    
    output.sort(key=lambda x: (x["year4"], x["month_digits"]))
    return output


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

if __name__ == "__main__":
    months = get_table_data()
    bags, sums = find_optimal_split(months, 8)
    # for i, (bag, total) in enumerate(zip(bags, sums)):
    #     # names = [months[j]["csv_name"][:-4] for j in bag]
    #     print(f"Process {i}: num_months {months[bags[i]]}, total rows {total}")
    print([months[j] for j in bags[0]])