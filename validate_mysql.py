import csv
import os
from dotenv import load_dotenv
import mysql.connector

import helper
from mpi_logging import *
import mpi_logging
from helper import get_table_data, FIDE_CSV_DIR, FIDE_CSV_DIR_2, find_optimal_split, initiate_conn


def initiate_conn(get_warnings=False):
    load_dotenv()
    host = os.environ.get("MYSQL_HOST")
    user = os.environ.get("MYSQL_USER")
    password = os.environ.get("MYSQL_PASSWORD")
    database = os.environ.get("MYSQL_DATABASE")
    
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        allow_local_infile=True,
        get_warnings=get_warnings
    )
    return conn


def find_broken_rows():
    conn = initiate_conn()
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        for (table, ) in cursor.fetchall():
            cursor.execute(f"SELECT * FROM {table} WHERE id<10;")
            rows = cursor.fetchall()
            if rows:
                print(table)
                for row in rows:
                    print(row)
    conn.close()


def validate_ids_mpi(month_names: list[dict[str, str]], rank):
    conn = initiate_conn()
    with conn.cursor() as cursor:
        for month_data in month_names:            
            with open(os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"]), "r") as f:
                reader = csv.reader(f, delimiter="*")
                next(reader)  # skip header
                csv_ids = set()
                for row in reader:
                    try:
                        csv_ids.add(int(row[0]))    
                    except ValueError as e:
                        print(f"Error reading CSV for {month_data['year']}-{month_data['month_digits']}: {e}")
                        print(row)
                        continue

            cursor.execute(f"SELECT id FROM {month_data['table_name']};")
            sql_ids = set(int(row[0]) for row in cursor.fetchall())
            
            overlap = len(csv_ids & sql_ids)
            only_csv = len(csv_ids - sql_ids)
            only_sql = len(sql_ids - csv_ids)
            total_diff = only_csv + only_sql
            mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: CSV IDs: {len(csv_ids):<6}, SQL IDs: {len(sql_ids):<6}, Overlap: {overlap:<6}, Only CSV: {only_csv:<6}, Only SQL: {only_sql:<6}, Total Diff: {total_diff:<6}")
    conn.close()
    

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
def validate_row_counts_mpi(month_names: list[dict[str, str]], rank):
    conn = initiate_conn()
    with conn.cursor() as cursor:
        for month_data in month_names:
            csv_path = os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"])     
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
            mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: CSV rows: {csv_rows:<6}, SQL rows: {sql_rows:<6}, Diff: {diff:<6}, Blank rows: {blank_rows:<6}")
    conn.close()


def get_distinct_titles_mpi(month_names: list[dict[str, str]], rank):
    conn = initiate_conn()
    with conn.cursor() as cursor:
        for month_data in month_names:            
            cursor.execute(f"SELECT distinct trim(title) FROM {month_data['table_name']};")
            titles = sorted([row[0] for row in cursor.fetchall()])
            mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: {titles}")
    conn.close()
    

def get_distinct_otitles_mpi(month_names: list[dict[str, str]], rank):
    conn = initiate_conn()
    month_names = helper.get_period_range(start_year=2012, start_month="sep", end_year=2026, end_month="dec", table_data=month_names)
    with conn.cursor() as cursor:
        for month_data in month_names:            
            cursor.execute(f"SELECT distinct otitle FROM {month_data['table_name']};")
            otitles = [row[0] for row in cursor.fetchall()]
            otitles = {item.strip() for string in otitles for item in string.split(",")}
            mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: {otitles}")
    conn.close()

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
    for month_data in month_names:
        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {month_data['table_name']} WHERE id=0;")
            conn.commit()
            # cursor.execute(f"SELECT * FROM {month_data['table_name']} WHERE id=0;")
            # head = cursor.fetchall()
            # if head:
            #     print(month_data['table_name'])
            #     print(head)
    conn.close()
    

def validate_long_names_mpi(month_names: list[dict[str, str]], rank):
    conn = initiate_conn()
    with conn.cursor() as cursor:
        for month_data in month_names:
            cursor.execute(f"SELECT MAX(CHAR_LENGTH(name)) FROM {month_data['table_name']};")
            max_length = cursor.fetchone()[0]
            cursor.execute(f"""SELECT id FROM {month_data['table_name']} WHERE CHAR_LENGTH(TRIM(name)) = {max_length};""")
            long_names = [row[0] for row in cursor.fetchall()]
            if long_names:
                mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: {max_length=}")
                mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: {long_names}")
    conn.close()
    

def get_titles_in_name_mpi(month_names: list[dict[str, str]], rank):
    """Certain titles in the early years are stored in the name column, so they have to be manually extracted.
    """    
    conn = initiate_conn()
    with conn.cursor() as cursor:
        for month_data in month_names:
            cursor.execute(f"SELECT id, name FROM {month_data['table_name']} WHERE name like '%(%)%';")
            output = cursor.fetchall()
            for row in output:
                mpi_log(rank, f"{month_data['year']}-{month_data['month_digits']}: {row[0]:>6} {row[1]}")
    conn.close()


# mpiexec -n 8 python -u validate.py
if __name__ == "__main__":
    # helper.mpi_main(get_titles_in_name_mpi, "get_titles_in_name", mpi_log_kwargs={ "format": "%(message)s"})
    helper.mpi_main(get_distinct_otitles_mpi, "distinct_otitles")
    # delete_null_rows(helper.get_period_range(start_year=2004, start_month="apr", end_year=2008, end_month="jan"))