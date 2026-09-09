import csv
import mysql.connector
from mysql.connector.connection import MySQLConnection
import os
import numpy as np

from mpi_logging import *
import mpi_logging
from helper import get_table_data, FIDE_CSV_DIR, FIDE_CSV_DIR_2, find_optimal_split


# TODO: store username and password in a config file, gitignore it, and read from it instead of prompting the user for input each time
def initiate_conn():
    # user = input("Enter MySQL username: ")
    # password = input("Enter MySQL password: ")
    user = "root"
    password = "password"
    
    conn = mysql.connector.connect(
        host="localhost",
        user=user,
        password=password,
        database="elo_db",
        allow_local_infile=True
    )
    return conn

def find_broken_rows(conn: MySQLConnection):
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        for (table, ) in cursor.fetchall():
            cursor.execute(f"SELECT * FROM {table} WHERE id<10;")
            rows = cursor.fetchall()
            if rows:
                print(table)
                for row in rows:
                    print(row)


def validate_ids_mpi(month_names: list[dict[str, str]], rank):
    conn = initiate_conn()
    with conn.cursor() as cursor:
        for month_data in month_names:            
            with open(os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"]), "r") as f:
                reader = csv.reader(f, delimiter="*")
                next(reader)  # skip header
                csv_ids = set(int(row[0]) for row in reader)

            cursor.execute(f"SELECT id FROM {month_data['table_name']};")
            sql_ids = set(int(row[0]) for row in cursor.fetchall())
            
            overlap = len(csv_ids & sql_ids)
            only_csv = len(csv_ids - sql_ids)
            only_sql = len(sql_ids - csv_ids)
            total_diff = only_csv + only_sql
            mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: CSV IDs: {len(csv_ids):<6}, SQL IDs: {len(sql_ids):<6}, Overlap: {overlap:<6}, Only CSV: {only_csv:<6}, Only SQL: {only_sql:<6}, Total Diff: {total_diff:<6}")
    conn.close()


def validate_ids_main():
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size
    
    mpi_log_setup(rank, "validate_ids")
    
    if rank == 0:
        month_names = get_table_data()
        bags, _ = find_optimal_split(month_names, size)
        print(f"Root: Completed reading {len(month_names)} SQL/CSV names.")
    else:
        month_names = None
        bags = None

    month_names = comm.bcast(month_names, root=0)
    bags = comm.bcast(bags, root=0)
    
    validate_ids_mpi([month_names[j] for j in bags[rank]], rank)
    
    comm.Barrier()
    mpi_combine_logs(rank, "validate_ids")
    

def validate_rows_mpi(month_names: list[dict[str, str]], rank):
    conn = initiate_conn()
    with conn.cursor() as cursor:
        for month_data in month_names:            
            with open(os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"]), "r") as f:
                reader = csv.reader(f, delimiter="*")
                next(reader)  # skip header
                csv_rows = list(row for row in reader)
            
            print(csv_rows[1])

            cursor.execute(f"SELECT * FROM {month_data['table_name']};")
            sql_rows = list(row for row in cursor.fetchall())
            
            print(sql_rows[1])
            
    conn.close()
        

def validate_rows_main():
    input = [get_table_data()[0]]
    print(input)
    validate_rows_mpi(input, 0)

# checks that the number of rows in the CSV and SQL table match
def validate_row_counts_mpi(month_names: list[dict[str, str]]):
    conn = initiate_conn()
    output = []
    with conn.cursor() as cursor:
        for month_data in month_names:
            csv_path = os.path.join(FIDE_CSV_DIR, month_data["csv_name"])     
            with open(csv_path, "r") as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                csv_rows = sum(1 for _ in reader)

                blank_rows = 0
                f.seek(0)
                for row in f:
                    if row.strip() == "":
                        blank_rows += 1

            cursor.execute(f"SELECT COUNT(*) FROM {month_data['table_name']};")
            sql_rows = cursor.fetchall()[0][0]
            diff = csv_rows - sql_rows
            output.append((month_data["year"], month_data["month_digits"], csv_rows, sql_rows, diff, blank_rows))
    conn.close()
    return np.array(output, dtype=int)

def validate_row_counts_mpi_main():
    comm = MPI.COMM_WORLD
    rank = comm.rank
    size = comm.size
    
    if rank == 0:
        month_names = get_table_data()
        print(f"Root: Completed reading {len(month_names)} SQL/CSV names.")
    else:
        month_names = None

    month_names = comm.bcast(month_names, root=0)
    
    start_idx = rank * len(month_names) // size
    end_idx = min((rank + 1) * len(month_names) // size, len(month_names))
    
    row_counts = validate_row_counts_mpi(month_names[start_idx:end_idx])
    gathered_row_counts = comm.gather(row_counts, root=0)
    
    if rank == 0:
        print("Root: Completed gathering row counts. Now sorting and outputting to CSV...")
        # convert to numpy
        gathered_row_counts = np.vstack(gathered_row_counts)
        
        # order by year, month
        indices = np.lexsort((gathered_row_counts[:, 1], gathered_row_counts[:, 0]))
        gathered_row_counts = gathered_row_counts[indices]

        # create 2 outputs, one for rows with diffs, one for those without
        indices = gathered_row_counts[:,4] == 0
        no_diff = gathered_row_counts[indices]
        diff = gathered_row_counts[~indices]
        
        # output to CSV
        np.savetxt("row_counts_no_diff.csv", no_diff, delimiter=",", fmt="%d", header="year,month,csv_rows,sql_rows,diff,blank_rows", comments="")
        np.savetxt("row_counts_diff.csv", diff, delimiter=",", fmt="%d", header="year,month,csv_rows,sql_rows,diff,blank_rows", comments="")

def output_heads():
    mpi_logging.log_setup("sql_staging_heads", format="%(message)s")
    
    table_names = get_table_data()
    conn = initiate_conn()
    for table in table_names:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(f"SELECT * FROM {table['table_name']} LIMIT 5;")
            head = cursor.fetchall()
            logging.info(f"Head of {table['table_name']}:")
            logging.info(head[0].keys())
            for row in head:
                logging.info(row.values())
    logging.shutdown()
    conn.close()

def delete_null_rows(month_names: list[dict[str, str]]):
    conn = initiate_conn()
    with conn.cursor() as cursor:
        for month_data in month_names:
            cursor.execute(f"SELECT * FROM {month_data['table_name']} WHERE id=0;")
            conn.commit()
            head = cursor.fetchall()
            if head:
                print(month_data['table_name'])
                print(head.fetchall())
    conn.close()

# mpiexec -n 8 python -u validate.py
if __name__ == "__main__":
    output_heads()
