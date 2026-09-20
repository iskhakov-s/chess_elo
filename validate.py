import duckdb
import os
import csv
import logging

from helper import FIDE_CSV_DIR, FIDE_CSV_DIR_2
import helper
from mpi_logging import log_setup

def validate_row_counts(month_names: list[dict[str, str]] = None):
    log_setup("validate_row_counts")
    conn = duckdb.connect("fide_elo.duckdb")
    
    if month_names is None:
        month_names = helper.get_table_data()
    
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

        sql_rows = conn.sql(f"SELECT COUNT(*) FROM {month_data['table_name']};").fetchall()[0][0]
        diff = csv_rows - sql_rows
        logging.info(f"{month_data['year']}-{month_data['month']}: CSV rows: {csv_rows:<6}, SQL rows: {sql_rows:<6}, Diff: {diff:<6}, Blank rows: {blank_rows:<6}")
    conn.close()
    

def get_distinct_categories(category="title", month_names: list[dict[str, str]] = None):
    log_setup(f"get_distinct_{category}")
    conn = duckdb.connect("fide_elo.duckdb")
    
    if month_names is None:
        month_names = helper.get_table_data()
    
    for month_data in month_names:
        try:     
            sql_out = conn.sql(f"SELECT distinct trim({category}) FROM {month_data['table_name']};")
        except duckdb.BinderException as e:
            logging.info(f"{month_data['year']}-{month_data['month']}: Error getting distinct {category} for {month_data['month']} {month_data['year4']}: {e}")
            continue
        categories = sorted([row[0] for row in sql_out.fetchall()])
        logging.info(f"{month_data['year']}-{month_data['month']}: {categories}")
    conn.close()
    

def get_distinct_otitles(month_names: list[dict[str, str]]=None):
    log_setup("get_distinct_otitles")
    conn = duckdb.connect("fide_elo.duckdb")
    
    if month_names is None:
        month_names = helper.get_table_data()
    month_names = helper.get_period_range(start_year=2012, start_month="sep", end_year=2026, end_month="dec", table_data=month_names)
    
    with conn.cursor() as cursor:
        for month_data in month_names:            
            cursor.execute(f"SELECT distinct otitle FROM {month_data['table_name']};")
            otitles = [row[0] for row in cursor.fetchall()]
            otitles = {item.strip() for string in otitles for item in string.split(",")}
            logging.info(f"{month_data['year']}-{month_data['month']}: {otitles}")
    conn.close()
    

def find_null_rows(delete=False, month_names: list[dict[str, str]]=None):
    # log_setup("null_rows")
    conn = duckdb.connect("fide_elo.duckdb")
    
    if month_names is None:
        month_names = helper.get_table_data()
    
    for month_data in month_names:
        if delete:
            conn.sql(f"DELETE FROM {month_data['table_name']} WHERE id=0;")
            continue
        cursor = conn.sql(f"SELECT * FROM {month_data['table_name']} WHERE id=0;")
        head = cursor.fetchall()
        if head:
            print(month_data['table_name'])
            print(head)
    conn.close()
    

def get_titles_in_name(month_names: list[dict[str, str]]=None):
    """Certain titles in the early years are stored in the name column, so they have to be manually extracted.
    """   
    log_setup("titles_in_name")
    conn = duckdb.connect("fide_elo.duckdb")
    
    if month_names is None:
        month_names = helper.get_table_data() 

    for month_data in month_names:
        cursor = conn.sql(f"SELECT id, name FROM {month_data['table_name']} WHERE name like '%(%)%';")
        output = cursor.fetchall()
        for row in output:
            logging.info(f"{month_data['year']}-{month_data['month_digits']}: {row[0]:>6} {row[1]}")
    conn.close()
    
    
if __name__ == "__main__":
    get_distinct_categories(category="flag")
    