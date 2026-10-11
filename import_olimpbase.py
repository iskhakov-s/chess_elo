import os
import duckdb
import logging
from datetime import date

import mpi_logging

OLIMPBASE_PATH = os.path.join("olimpbase_records", "elo1967-2001", "all.csv")
OLIMPBASE_PATH_2 = os.path.join("olimpbase_records", "elo1967-2001", "all2.csv")


# fixes utf-8 encoding issues in the CSV file
def fix_olimpbase_csv():
    with open(OLIMPBASE_PATH, "r", encoding="utf-8", errors="replace") as rf:
        with open(OLIMPBASE_PATH_2, "w", encoding="utf-8") as wf:
            for line in rf:
                wf.write(line)


def import_csv():
    conn = duckdb.connect("fide_elo.duckdb")
    mpi_logging.log_setup("import_olimpbase")

    conn.sql("DROP TABLE IF EXISTS staging_olimpbase;")
    conn.sql("""
        CREATE TABLE staging_olimpbase (
        temp1 VARCHAR(255),
        name VARCHAR(255) NOT NULL,
        standard_name VARCHAR(255) NOT NULL,
        yyyymm VARCHAR(6),
        id INTEGER,
        birthday VARCHAR(255),
        title VARCHAR(7),
        fed CHAR(3),
        elo INTEGER,
        elo_change INTEGER, -- not needed
        games INTEGER,
        flag VARCHAR(255),
        comments VARCHAR(255),
        fed2 CHAR(3),
        temp2 VARCHAR(255)
    );""")
    conn.sql(f"""
        INSERT INTO staging_olimpbase
        SELECT * FROM read_csv('{OLIMPBASE_PATH_2}', header=False, sep=';', store_rejects=TRUE);
    """)

    csv = conn.sql(f"SELECT * FROM reject_errors;").pl().write_csv()
    if csv.count("\n") > 1:
        logging.warning(csv[:1000])

    conn.close()


def fix_yyyymm():
    conn = duckdb.connect("fide_elo.duckdb")
    conn.sql("""
        ALTER TABLE staging_olimpbase ADD COLUMN period DATE;
        UPDATE staging_olimpbase
        SET period = CAST(SUBSTR(yyyymm, 1, 4) || '-' || GREATEST(SUBSTR(yyyymm, 5, 2)::INTEGER, 1) || '-01' AS DATE);
    """)
    conn.close()
    
    
def find_id_collisions():
    conn = duckdb.connect("fide_elo.duckdb")
    mpi_logging.log_setup("find_id_collisions_olimpbase", format="%(message)s")
    
    collisions = conn.sql("""
        SELECT 
            id, 
            array_agg(DISTINCT standard_name) AS names
        FROM staging_olimpbase
        WHERE id IS NOT NULL AND period >= '1990-07-01'
        GROUP BY id
        HAVING count(DISTINCT standard_name) > 1;
    """).fetchall()
    
    logging.info("id;names")
    for collision in collisions:
        logging.info(f"{collision[0]};{';'.join(collision[1])}")
    
    conn.close()


def fix_id_collisions():
    conn = duckdb.connect()
    
    new_names = conn.read_csv(os.path.join("logs", "find_id_collisions_olimpbase.log"))
    new_names.show()
    
    conn.close()


if __name__ == "__main__":
    ...
