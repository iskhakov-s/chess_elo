import os
import mysql.connector
from mysql.connector.connection import MySQLConnection

from helper import FIDE_CSV_DIR, FIDE_CSV_DIR_2, initiate_conn

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


def init_staging_fide_table_type_1(conn: MySQLConnection, month: str, year: int):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""CREATE TABLE staging_{year}_{month.lower()} IF NOT EXISTS (
                    id INT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    title VARCHAR(7),
                    fed CHAR(3) NOT NULL,
                    elo INT NOT NULL,
                    games INT NOT NULL,
                    flag VARCHAR(3)
            );"""
        )
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")
        raise
    
def init_staging_fide_table_type_2(conn: MySQLConnection, month: str, year: int):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""CREATE TABLE staging_{str(year)[-2:]}_{month.lower()} (
                id INT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                title VARCHAR(7),
                fed CHAR(3) NOT NULL,
                elo INT NOT NULL,
                games INT NOT NULL,
                birthday VARCHAR(15),
                flag VARCHAR(3)
            );"""
        )
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")
        raise
    
def init_staging_fide_table_type_3(conn: MySQLConnection, month: str, year: int):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""CREATE TABLE staging_{str(year)[-2:]}_{month.lower()} (
                id INT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                title VARCHAR(7),
                fed CHAR(3) NOT NULL,
                elo INT NOT NULL,
                games INT NOT NULL,
                birthday VARCHAR(15),
                sex CHAR(1),
                flag VARCHAR(3)
            );"""
        )
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")
        raise
    
def init_staging_fide_table_type_4(conn: MySQLConnection, month: str, year: int):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""CREATE TABLE staging_{str(year)[-2:]}_{month.lower()} (
                id INT PRIMARY KEY,
                name VARCHAR(255),
                fed CHAR(3),
                sex CHAR(1),
                title VARCHAR(7),
                wtitle VARCHAR(7),
                otitle VARCHAR(15),
                elo INT,
                games INT,
                k INT,
                birthday VARCHAR(5),
                flag VARCHAR(4)
            );"""
        )
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")
        raise
    
def init_staging_fide_table_type_5(conn: MySQLConnection, month: str, year: int):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""CREATE TABLE staging_{str(year)[-2:]}_{month.lower()} (
                    id INT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    fed CHAR(3) NOT NULL,
                    sex CHAR(1),
                    title VARCHAR(7),
                    wtitle VARCHAR(7),
                    otitle VARCHAR(15),
                    foa VARCHAR(3),
                    elo INT NOT NULL,
                    games INT NOT NULL,
                    k INT NOT NULL,
                    birthday VARCHAR(5),
                    flag VARCHAR(3)
            );"""
        )
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

def main():
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
                    init_staging_fide_table_type_4(conn, month, year)
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
    main()
