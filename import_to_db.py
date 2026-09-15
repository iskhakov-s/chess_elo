import os
import mysql.connector
from mysql.connector.connection import MySQLConnection

from helper import FIDE_CSV_DIR, FIDE_CSV_DIR_2, initiate_conn
import helper
import mpi_logging

MONTHS = {
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

CREATE_TABLE_STRINGS = {
    1: """CREATE TABLE {} (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        title VARCHAR(255),
        fed CHAR(3),
        elo INT,
        games INT,
        flag VARCHAR(255)
    );""",
    2: """CREATE TABLE {} (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        title VARCHAR(255),
        fed CHAR(3),
        elo INT,
        games INT,
        birthday VARCHAR(255),
        flag VARCHAR(255)
    );""",
    3: """CREATE TABLE {} (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        title VARCHAR(255),
        fed CHAR(3),
        elo INT,
        games INT,
        birthday VARCHAR(255),
        sex CHAR(1),
        flag VARCHAR(255)
    );""",
    4: """CREATE TABLE {} (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        fed CHAR(3),
        sex CHAR(1),
        title VARCHAR(255),
        wtitle VARCHAR(255),
        otitle VARCHAR(255),
        elo INT,
        games INT,
        k INT,
        birthday VARCHAR(255),
        flag VARCHAR(255)
    );""",
    5: """CREATE TABLE {} (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        fed CHAR(3),
        sex CHAR(1),
        title VARCHAR(255),
        wtitle VARCHAR(255),
        otitle VARCHAR(255),
        foa VARCHAR(255),
        elo INT,
        games INT,
        k INT,
        birthday VARCHAR(255),
        flag VARCHAR(255)
    );"""
}

def init_staging_fide_table(conn: MySQLConnection, create_table_string: str, table_name: str):
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_string.format(table_name))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")
        raise


def import_into_staging_fide_table(conn: MySQLConnection):
    cursor = conn.cursor()
    for filename in os.listdir(FIDE_CSV_DIR):
        cursor.execute(
            "LOAD DATA LOCAL INFILE '%s' INTO TABLE staging_fide FIELDS TERMINATED BY '*' IGNORE 1 ROWS;",
            (os.path.join(FIDE_CSV_DIR, filename),)
        )
    conn.commit()
    
def import_csv(conn: MySQLConnection, month:str, year:int):
    cursor = conn.cursor()
    year_str = str(year)[-2:]
    filename = f"{month.upper()}{year_str}.csv"
    table_name = f"staging_{year_str}_{month.lower()}"
        
    path = os.path.join(FIDE_CSV_DIR_2, filename)
    cursor.execute(f"LOAD DATA LOCAL INFILE %s INTO TABLE {table_name} FIELDS TERMINATED BY '*' IGNORE 1 ROWS;", (path,))
    conn.commit()
    
def import_csv_mpi(month_names: list[dict[str, str]], rank):
    conn = initiate_conn()
    cursor = conn.cursor()
    
    type_dict = helper.get_type_dict(month_names)
    for month_data in month_names:
        try:
            # drop if exists
            mpi_logging.mpi_log(rank, f"{month_data["year"]}-{month_data["month"]}: Dropping table if exists: {month_data['table_name']}")
            cursor.execute(f"DROP TABLE IF EXISTS {month_data['table_name']};")
            
            # load table
            mpi_logging.mpi_log(rank, f"{month_data["year"]}-{month_data["month"]}: Initializing staging table...")
            create_table_string = CREATE_TABLE_STRINGS[type_dict[(month_data["year4"], month_data["month"])]]
            init_staging_fide_table(conn, create_table_string, month_data["table_name"])
            
            # load from file
            mpi_logging.mpi_log(rank, f"{month_data["year"]}-{month_data["month"]}: Importing CSV")
            path = os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"])
            cursor.execute(f"LOAD DATA LOCAL INFILE %s INTO TABLE {month_data['table_name']} FIELDS TERMINATED BY '*' IGNORE 1 ROWS;", (path,))
            conn.commit()
        except Exception as e:
            mpi_logging.mpi_log(rank, f"{month_data["year"]}-{month_data["month"]}: Error importing CSV for {month_data['month']} {month_data['year4']}: {e}")
    conn.close()

def main_old():
    conn = initiate_conn()
    
    start_year = 2012
    start_month = 9
    end_year = 2016
    end_month = 8 
    
    for year in range(start_year, end_year + 1):
        m = start_month if year == start_year else 1
        while m <= 12:
            if year == end_year and m > end_month:
                break
            month = MONTHS[m]
            filename = f"{month.upper()}{str(year)[-2:]}.csv"
            if filename in os.listdir(FIDE_CSV_DIR_2):
                print(f"Initializing staging table for {month.upper()} {year}...")
                try:
                    print("dropping table if exists...")
                    cursor = conn.cursor()
                    cursor.execute(f"DROP TABLE IF EXISTS staging_{str(year)[-2:]}_{month.lower()};")
                    conn.commit()
                    print("initializing...")
                    init_staging_fide_table(conn, create_table_string, f"staging_{str(year)[-2:]}_{month.lower()}")
                    print("importing CSV...")
                    import_csv(conn, month, year)
                except mysql.connector.Error as err:
                    print(f"Error importing CSV for {month.upper()} {year}: {err}")
                    print(err)
                # cursor = conn.cursor()
                # cursor.execute(f"DROP TABLE staging_{str(year)[-2:]}_{month.lower()};")
                # conn.commit()
            m += 1

    # init_staging_fide_table(conn)
    # import_csv(conn)
    conn.close()
    
def temp():
    conn = initiate_conn()
    import_csv(conn, "jul", 2001)
    import_csv(conn, "oct", 2001)
    import_csv(conn, "jan", 2002)
    import_csv(conn, "apr", 2002)
    import_csv(conn, "jul", 2002)
    conn.close()
    
if __name__ == "__main__":
    helper.mpi_main(import_csv_mpi, "import_csv_2016_2026", get_period_range_kwargs={"start_year": 2016, "start_month": 9, "end_year": 2026, "end_month": 12})
