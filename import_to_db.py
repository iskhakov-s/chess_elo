import os
import mysql.connector
from mysql.connector.connection import MySQLConnection
import logging

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
        fed VARCHAR(255),
        elo INT,
        games INT,
        flag VARCHAR(255)
    );""",
    2: """CREATE TABLE {} (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        title VARCHAR(255),
        fed VARCHAR(255),
        elo INT,
        games INT,
        birthday VARCHAR(255),
        flag VARCHAR(255)
    );""",
    3: """CREATE TABLE {} (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        title VARCHAR(255),
        fed VARCHAR(255),
        elo INT,
        games INT,
        birthday VARCHAR(255),
        sex VARCHAR(255),
        flag VARCHAR(255)
    );""",
    4: """CREATE TABLE {} (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        fed VARCHAR(255),
        sex VARCHAR(255),
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
        fed VARCHAR(255),
        sex VARCHAR(255),
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


def import_csv():
    conn = initiate_conn()
    cursor = conn.cursor()
    
    mpi_logging.log_setup("import_csv_all")
    
    month_names = helper.get_table_data()
    type_dict = helper.get_type_dict(month_names)
    
    for month_data in month_names:
        try:
            # drop if exists
            logging.info(f"{month_data["year"]}-{month_data["month"]}: Dropping table if exists: {month_data['table_name']}")
            cursor.execute(f"DROP TABLE IF EXISTS {month_data['table_name']};")
            
            # load table
            logging.info(f"{month_data["year"]}-{month_data["month"]}: Initializing staging table...")
            create_table_string = CREATE_TABLE_STRINGS[type_dict[(month_data["year4"], month_data["month"])]]
            init_staging_fide_table(conn, create_table_string, month_data["table_name"])
            
            # load from file
            logging.info(f"{month_data["year"]}-{month_data["month"]}: Importing CSV")
            path = os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"])
            cursor.execute(f"LOAD DATA LOCAL INFILE %s INTO TABLE {month_data['table_name']} FIELDS TERMINATED BY '*' IGNORE 1 ROWS;", (path,))
            conn.commit()
        except Exception as e:
            logging.error(f"{month_data["year"]}-{month_data["month"]}: Error importing CSV for {month_data['month']} {month_data['year4']}: {e}")
    conn.close()


# mpi causes massive slowdowns, use
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

 
if __name__ == "__main__":
    # helper.mpi_main(import_csv_mpi, "import_csv_all")
    import_csv()
