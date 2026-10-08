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


# def assign_ids():
#     conn = duckdb.connect("fide_elo.duckdb")
#     conn.sql("""
#         CREATE OR REPLACE TABLE staging_olimpbase2 AS
#         WITH source_rows AS (
#             SELECT
#                 ROW_NUMBER() OVER () AS source_row,
#                 *
#             FROM staging_olimpbase
#         ),
#         scored_month_rows AS (
#             SELECT
#                 current_row.*,
#                 (
#                     SELECT MIN(
#                         CASE WHEN current_row.fed IS DISTINCT FROM prior_row.fed
#                              THEN 1 ELSE 0 END
#                         + CASE WHEN current_row.elo IS DISTINCT FROM prior_row.elo
#                                THEN 1 ELSE 0 END
#                         + CASE WHEN current_row.name IS DISTINCT FROM prior_row.name
#                                THEN 1 ELSE 0 END
#                     )
#                     FROM source_rows AS prior_row
#                     WHERE prior_row.standard_name = current_row.standard_name
#                       AND prior_row.year = current_row.year - 1
#                       AND prior_row.month = current_row.month
#                 ) AS prior_difference
#             FROM source_rows AS current_row
#         ),
#         selected_month_rows AS (
#             SELECT * EXCLUDE (month_rank, prior_difference)
#             FROM (
#                 SELECT
#                     scored_month_rows.*,
#                     ROW_NUMBER() OVER (
#                         PARTITION BY standard_name, year, month
#                         ORDER BY
#                             prior_difference IS NULL,
#                             prior_difference,
#                             RANDOM()
#                     ) AS month_rank
#                 FROM scored_month_rows
#             )
#             WHERE month_rank = 1
#         ),
#         latest_player_rows AS (
#             SELECT * EXCLUDE (latest_rank)
#             FROM (
#                 SELECT
#                     selected_month_rows.*,
#                     ROW_NUMBER() OVER (
#                         PARTITION BY standard_name
#                         ORDER BY year DESC, month DESC
#                     ) AS latest_rank
#                 FROM selected_month_rows
#             )
#             WHERE latest_rank = 1
#         ),
#         player_id_candidates AS (
#             SELECT
#                 latest_player_rows.standard_name,
#                 latest_player_rows.year,
#                 latest_player_rows.month,
#                 latest_player_rows.id,
#                 CASE
#                     WHEN latest_player_rows.year > 1990
#                          OR (latest_player_rows.year = 1990 AND latest_player_rows.month >= 7)
#                     THEN EXISTS (
#                         SELECT 1
#                         FROM source_rows AS later_row
#                         WHERE later_row.standard_name <> latest_player_rows.standard_name
#                           AND later_row.id = latest_player_rows.id
#                           AND (later_row.year > latest_player_rows.year
#                                OR (later_row.year = latest_player_rows.year
#                                    AND later_row.month > latest_player_rows.month))
#                     )
#                     ELSE TRUE
#                 END AS needs_fake_id
#             FROM latest_player_rows
#         ),
#         player_ids AS (
#             SELECT
#                 standard_name,
#                 CASE
#                     WHEN needs_fake_id OR id IS NULL
#                     THEN 999000000000 + ROW_NUMBER() OVER (ORDER BY standard_name)
#                     ELSE CAST(id AS BIGINT)
#                 END AS id2
#             FROM player_id_candidates
#         )
#         SELECT
#             source.name,
#             source.standard_name,
#             source.yyyymm,
#             source.id,
#             source.birthday,
#             source.title,
#             source.fed,
#             source.elo,
#             source.games,
#             source.flag,
#             source.year,
#             source.month,
#             player_ids.id2
#         FROM source_rows AS source
#         JOIN player_ids USING (standard_name)
#     """)
#     conn.close()
    
    
def assign_ids():
    conn = duckdb.connect("fide_elo.duckdb")
    mpi_logging.log_setup("assign_ids_olimpbase")
    
    id_count = 0
    fake_id_count = 0
    def _assign_id(conn: duckdb.DuckDBPyConnection, std_name: str, new_id: int, is_fake_id: bool = False):
        nonlocal id_count, fake_id_count
        if is_fake_id:
            new_id += 999000000000
            logging.info(f"Assigning fake ID {new_id} to player {std_name}")
            fake_id_count += 1
        id_count += 1
        # conn.sql("UPDATE staging_olimpbase SET id = ? WHERE standard_name = ? AND period = (SELECT MAX(period) FROM staging_olimpbase WHERE standard_name = ?);", params=(new_id, std_name, std_name))
    
    # conn.sql("ALTER TABLE staging_olimpbase ADD COLUMN id2 INTEGER;")
    std_names = conn.sql("SELECT distinct standard_name FROM staging_olimpbase;").fetchall()
    std_names = [row[0] for row in std_names]
    for std_name in std_names:
        cursor = conn.sql("SELECT id, period,  FROM staging_olimpbase WHERE standard_name = ? ORDER BY period;", params=(std_name, ))
        latest_period = cursor.max("period").fetchone()[0]
        if latest_period < date(1990, 7, 1):
            logging.info(f"Player {std_name} does not have modern FIDE ID, oldest record {latest_period} is before July 1990")
            _assign_id(conn, std_name, std_names.index(std_name), is_fake_id=True)
            continue
        
        latest_id = cursor.filter("id IS NOT NULL").filter("period >= '1990-07-01'").aggregate("ARGMAX(id, period)").fetchone()[0]
        if latest_id is None:
            logging.info(f"Player {std_name} does not have a modern FIDE ID")
            _assign_id(conn, std_name, std_names.index(std_name), is_fake_id=True)
            continue
        
        cursor2 = conn.sql("SELECT standard_name FROM staging_olimpbase WHERE id = ? and period > ?;", params=(latest_id, latest_period))
        if (colliding_name:=cursor2.fetchone()) is not None:
            logging.info(f"Player {std_name}'s most recent FIDE ID collides with player {colliding_name[0]}")
            _assign_id(conn, std_name, std_names.index(std_name), is_fake_id=True)
            continue
        
        _assign_id(conn, std_name, latest_id)

    
    logging.info(f"Total fake IDs assigned: {fake_id_count}")
    logging.info(f"Total IDs assigned: {id_count}")
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
    conn = duckdb.connect("fide_elo.duckdb")
    
    new_names = conn.read_csv(os.path.join("logs", "find_id_collisions_olimpbase.log"))
    new_names.show()
    
    
    
    conn.close()

    
def find_id_collisions_olimpbase_to_modern():
    conn = duckdb.connect("fide_elo.duckdb")
    mpi_logging.log_setup("find_id_collisions_olimpbase_to_modern", format="%(message)s")
    
    collisions = conn.sql("""
        SELECT DISTINCT ON (standard_name) standard_name, name, id, period
        FROM staging_olimpbase
        WHERE id IS NOT NULL AND period >= '1990-07-01'
        ORDER BY standard_name, period DESC;
    """).fetchall()
    
    for collision in collisions:
        logging.info(collision)
    
    conn.close()


if __name__ == "__main__":
    fix_id_collisions()
