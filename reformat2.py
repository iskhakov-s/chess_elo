import logging
import os
import csv
from mpi4py import MPI
import numpy as np
from mpi_logging import mpi_log, mpi_log_setup, mpi_combine_logs
from helper import get_table_names, FIDE_CSV_DIR, FIDE_CSV_DIR_2

""" Reformats the CSV files in FIDE_CSV_DIR and writes them to FIDE_CSV_DIR_2. 
This is intended to occur after running reformat.R.
Specifically, it removes blank rows and removes the first two characters from each row of the CSV files where there is filler.
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
        with open(os.path.join(FIDE_CSV_DIR, month_data["csv_name"]), "r") as rf:
            with open(os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"]), "w") as wf:
                for line in rf:
                    if line.strip() != "":
                        wf.write(line)
                    else:
                        blank_rows += 1
        mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: Removed {blank_rows:<3} blank rows")


def test():
    with open(os.path.join(FIDE_CSV_DIR, "JAN01.csv"), "r", encoding="utf-8") as f:
        for _ in range(3):
            print(repr(f.readline()))
  
  
def remove_blank_lines_main():
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size
    
    mpi_log_setup(rank, "remove_blank_lines")
    
    if rank == 0:
        month_names = get_table_names()
        print(f"Root: Completed reading {len(month_names)} SQL/CSV names.")
    else:
        month_names = None

    month_names = comm.bcast(month_names, root=0)
    start_idx = rank * len(month_names) // size
    end_idx = min((rank + 1) * len(month_names) // size, len(month_names))
    
    remove_blank_lines(month_names[start_idx:end_idx], rank)
    
    comm.Barrier()
    mpi_combine_logs(rank, "remove_blank_lines")

# mpiexec -n 8 python -u reformat2.py
if __name__ == "__main__":
    remove_first_two_chars()
    