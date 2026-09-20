import os
import duckdb
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
    1: """CREATE OR REPLACE TABLE {} (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255),
        title VARCHAR(255),
        fed VARCHAR(255),
        elo INTEGER,
        games INTEGER DEFAULT 0,
        flag VARCHAR(255)
    );""",
    2: """CREATE OR REPLACE TABLE {} (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255),
        title VARCHAR(255),
        fed VARCHAR(255),
        elo INTEGER,
        games INTEGER DEFAULT 0,
        birthday VARCHAR(255),
        flag VARCHAR(255)
    );""",
    3: """CREATE OR REPLACE TABLE {} (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255),
        title VARCHAR(255),
        fed VARCHAR(255),
        elo INTEGER,
        games INTEGER DEFAULT 0,
        birthday VARCHAR(255),
        sex VARCHAR(255),
        flag VARCHAR(255)
    );""",
    4: """CREATE OR REPLACE TABLE {} (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255),
        fed VARCHAR(255),
        sex VARCHAR(255),
        title VARCHAR(255),
        wtitle VARCHAR(255),
        otitle VARCHAR(255),
        elo INTEGER,
        games INTEGER DEFAULT 0,
        k INTEGER,
        birthday VARCHAR(255),
        flag VARCHAR(255)
    );""",
    5: """CREATE OR REPLACE TABLE {} (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255),
        fed VARCHAR(255),
        sex VARCHAR(255),
        title VARCHAR(255),
        wtitle VARCHAR(255),
        otitle VARCHAR(255),
        foa VARCHAR(255),
        elo INTEGER,
        games INTEGER DEFAULT 0,
        k INTEGER,
        birthday VARCHAR(255),
        flag VARCHAR(255)
    );"""
}

def init_staging_fide_table(conn: duckdb.DuckDBPyConnection, create_table_string: str, table_name: str):
    try:
        conn.sql(create_table_string.format(table_name))
    except duckdb.Error as err:
        print(f"Error creating table: {err}")
        raise
    

def import_csv_upsert(conn: duckdb.DuckDBPyConnection, month_data: dict[str, str]):
    path = os.path.join(FIDE_CSV_DIR_2, month_data["csv_name"])
    conn.sql(f"""
        INSERT INTO {month_data['table_name']}
        SELECT * FROM read_csv('{path}', header=True, sep='*', store_rejects=TRUE)
        ON CONFLICT (id) DO UPDATE 
        SET (games, elo, flag) = (EXCLUDED.games, EXCLUDED.elo, EXCLUDED.flag) 
        WHERE {month_data['table_name']}.games < EXCLUDED.games;
    """)


def import_csv(month_names: list[dict[str, str]] = None):
    conn = duckdb.connect("fide_elo.duckdb")
    
    mpi_logging.log_setup("import_csv_all")
    
    if month_names is None:
        month_names = helper.get_table_data()
    type_dict = helper.get_type_dict(month_names)
    
    for month_data in month_names:
        try:
            # drop if exists
            logging.info(f"{month_data["year"]}-{month_data["month"]}: Dropping table if exists: {month_data['table_name']}")
            conn.sql(f"DROP TABLE IF EXISTS {month_data['table_name']};")
            
            # load table
            logging.info(f"{month_data["year"]}-{month_data["month"]}: Initializing staging table...")
            create_table_string = CREATE_TABLE_STRINGS[type_dict[(month_data["year4"], month_data["month"])]]
            init_staging_fide_table(conn, create_table_string, month_data["table_name"])
            
            # load from file
            logging.info(f"{month_data["year"]}-{month_data["month"]}: Importing CSV")
            try:
                import_csv_upsert(conn, month_data)
            except duckdb.BinderException as e:
                logging.info(f"{month_data["year"]}-{month_data["month"]}: Error importing CSV for {month_data['month']} {month_data['year4']}: {e}")
                # logging.warning(f"{month_data["year"]}-{month_data["month"]}: Attempting to add a temp column to the table and re-import the CSV")
                conn.sql(f"ALTER TABLE {month_data['table_name']} ADD COLUMN temp VARCHAR(255);")
                import_csv_upsert(conn, month_data)
            
            csv = conn.sql(f"SELECT * FROM reject_errors;").pl().write_csv()
            if csv.count("\n") > 1:
                logging.warning(csv[:1000])
        except Exception as e:
            logging.error(f"{month_data["year"]}-{month_data["month"]}: Error importing CSV for {month_data['month']} {month_data['year4']}: {e}")
    conn.close()

 
if __name__ == "__main__":
    # print(helper.get_single_period(year=2001, month="jan"))
    import_csv()
