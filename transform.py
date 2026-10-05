import logging
import helper
import duckdb
from string import Template

from mpi_logging import log_setup


INSERT_INTO_STRINGS = {
    1: Template("""
        INSERT INTO player_staging_union (id, period, name, fed, sex, elo, games$bday1, title, wtitle, inactive)
            SELECT 
                id, 
                '$year-$month-01' AS period, 
                trim(name) AS name,
                trim(fed) AS fed,
                IF(trim(flag) LIKE '%w%', 1, 0) AS sex,
                elo as elo,
                games as games,
                $bday2
                CASE trim(title)
                    WHEN 'g' THEN 1
                    WHEN 'gm' THEN 1
                    WHEN 'm' THEN 2
                    WHEN 'f' THEN 3
                    WHEN 'c' THEN 4
                    WHEN 'h' THEN 5
                    WHEN 'hg' THEN 5
                    WHEN 'gh' THEN 5
                    WHEN 'wh' THEN 5
                    ELSE 0
                END AS title,
                CASE trim(title)
                    WHEN 'wg' THEN 1
                    WHEN 'wm' THEN 2
                    WHEN 'wf' THEN 3
                    WHEN 'wc' THEN 4
                    ELSE 0
                END AS wtitle,
                IF(trim(flag) LIKE '%i%', 1, 0) AS inactive
            FROM $table_name;
    """),
    4: Template("""
        INSERT INTO player_staging_union (
            id, period, name, fed, sex, elo, games, k, birthday, title, wtitle,
            otit_ia, otit_fa, otit_na, otit_io, otit_ao,
            otit_di, otit_ni, otit_fi, otit_ft, otit_fst,
            otit_li, otit_lsi, otit_sli$foa1, inactive)
        SELECT 
            id, 
            '$year-$month-01' AS period, 
            trim(name) AS name,
            trim(fed) AS fed,
            IF(trim(sex) = 'F', 1, 0) AS sex,
            elo as elo,
            games as games,
            k as k,
            trim(birthday) AS birthday,
            CASE trim(title)
                WHEN 'GM' THEN 1
                WHEN 'IM' THEN 2
                WHEN 'FM' THEN 3
                WHEN 'CM' THEN 4
                WHEN 'HM' THEN 5
                WHEN 'WH' THEN 5
                ELSE 0
            END AS title,
            CASE trim(wtitle)
                WHEN 'WGM' THEN 1
                WHEN 'WIM' THEN 2
                WHEN 'WF' THEN 3
                WHEN 'WFM' THEN 3
                WHEN 'WC' THEN 4
                WHEN 'WCM' THEN 4
                ELSE 0
            END AS wtitle,
            IF (lower(trim(otitle)) LIKE '%ia%', 1, 0) AS otit_ia,
            IF (lower(trim(otitle)) LIKE '%fa%', 1, 0) AS otit_fa,
            IF (lower(trim(otitle)) LIKE '%na%', 1, 0) AS otit_na,
            IF (lower(trim(otitle)) LIKE '%io%', 1, 0) AS otit_io,
            IF (lower(trim(otitle)) LIKE '%ao%', 1, 0) AS otit_ao,
            IF (lower(trim(otitle)) LIKE '%di%', 1, 0) AS otit_di,
            IF (lower(trim(otitle)) LIKE '%ni%', 1, 0) AS otit_ni,
            IF (lower(trim(otitle)) LIKE '%fi%', 1, 0) AS otit_fi,
            IF (lower(trim(otitle)) LIKE '%ft%', 1, 0) AS otit_ft,
            IF (lower(trim(otitle)) LIKE '%fst%', 1, 0) AS otit_fst,
            IF (lower(trim(otitle)) LIKE '%li%', 1, 0) AS otit_li,
            IF (lower(trim(otitle)) LIKE '%lsi%', 1, 0) AS otit_lsi,
            IF (lower(trim(otitle)) LIKE '%sli%', 1, 0) AS otit_sli,
            $foa2
            IF(trim(flag) LIKE '%i%', 1, 0) AS inactive
        FROM $table_name;
    """)
}
INSERT_INTO_STRINGS[2] = Template(INSERT_INTO_STRINGS[1].safe_substitute(bday1=", birthday", bday2="trim(birthday) AS birthday,"))
INSERT_INTO_STRINGS[3] = INSERT_INTO_STRINGS[2]
INSERT_INTO_STRINGS[5] = Template(INSERT_INTO_STRINGS[4].safe_substitute(foa1=", foa", 
    foa2="""CASE trim(foa)
                WHEN 'AGM' THEN 1
                WHEN 'AIM' THEN 2
                WHEN 'AFM' THEN 3
                WHEN 'ACM' THEN 4
                ELSE 0
            END AS foa,"""))
INSERT_INTO_STRINGS[1] = Template(INSERT_INTO_STRINGS[1].safe_substitute(bday1="", bday2=""))
INSERT_INTO_STRINGS[4] = Template(INSERT_INTO_STRINGS[4].safe_substitute(foa1="", foa2=""))



CREATE_TABLE_STRING = """
    CREATE TABLE player_staging_union (
        id INTEGER NOT NULL,
        period DATE NOT NULL,
        name VARCHAR(255) NOT NULL,
        fed CHAR(3) NOT NULL,
        sex UTINYINT NOT NULL,
        elo SMALLINT NOT NULL,
        games SMALLINT NOT NULL,
        k UTINYINT,
        birthday VARCHAR(30),
        title UTINYINT NOT NULL DEFAULT 0, -- 0 = none, 1 = GM, 2 = IM, 3 = FM, 4 = CM, 5 = HGM/WHGM
        wtitle UTINYINT NOT NULL DEFAULT 0, -- 0 = none, 1 = WGM, 2 = WIM, 3 = WFM, 4 = WCM
        foa UTINYINT, -- 0 = none, 1 = AGM, 2 = AIM, 3 = AFM, 4 = ACM
        otit_ia BOOLEAN, -- arbiter titles
        otit_fa BOOLEAN,
        otit_na BOOLEAN,
        otit_io BOOLEAN, -- international organizer
        otit_ao BOOLEAN,
        otit_di BOOLEAN, -- trainer titles
        otit_ni BOOLEAN,
        otit_fi BOOLEAN,
        otit_ft BOOLEAN,
        otit_fst BOOLEAN,
        otit_li BOOLEAN, -- licensed instructors
        otit_lsi BOOLEAN,
        otit_sli BOOLEAN,
        inactive BOOLEAN NOT NULL,
        PRIMARY KEY (id, period)
    );
"""


def create_staging_table(conn: duckdb.DuckDBPyConnection, drop=False):
    if drop:
        conn.sql("DROP TABLE IF EXISTS player_staging_union")
        logging.info("Dropped existing player_staging_union table")
    conn.sql(CREATE_TABLE_STRING)
    logging.info("Created player_staging_union table")

    
def transform(month_names: list[dict[str, str]]):
    log_setup("transform")
    
    conn = duckdb.connect("fide_elo.duckdb")
    type_dict = helper.get_type_dict(month_names)
    
    create_staging_table(conn, drop=True)
    
    for month_data in month_names:
        insert_string = INSERT_INTO_STRINGS[type_dict[(month_data["year4"], month_data["month"])]]
        insert_string = insert_string.safe_substitute(year=month_data['year4'], month=month_data['month_digits'], table_name=month_data['table_name'])
        try:
            conn.sql(insert_string)
            logging.info(f"{month_data['year']}-{month_data['month']}: Successful insertion")
        except duckdb.Error as e:
            logging.error(f"{month_data['year']}-{month_data['month']}: Error inserting into player_staging_union: {e}")
            continue
    conn.commit()


if __name__ == "__main__":
    transform(helper.get_table_data())
    # for i in range(len(INSERT_INTO_STRINGS)):
    #     print(i+1)
    #     print(INSERT_INTO_STRINGS[i+1].template)
