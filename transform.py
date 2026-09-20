import logging
import helper
import duckdb

from mpi_logging import log_setup


INSERT_INTO_STRINGS = {
    1: """
        INSERT INTO player_staging_union (id, period, name, fed, sex, title, wtitle, inactive)
            SELECT 
                id, 
                '{}-{}-01' AS period, 
                name,
                fed,
                IF(flag LIKE '%w%', 1, 0) AS sex,
                CASE title
                    WHEN 'g' THEN 1
                    WHEN 'gm' THEN 1
                    WHEN 'm' THEN 2
                    WHEN 'f' THEN 3
                    WHEN 'c' THEN 4
                    WHEN 'h' THEN 5
                    ELSE 0
                END AS title,
                CASE title
                    WHEN 'wg' THEN 1
                    WHEN 'wm' THEN 2
                    WHEN 'wf' THEN 3
                    WHEN 'wc' THEN 4
                    WHEN 'wh' THEN 5
                    ELSE 0
                END AS wtitle,
                IF(flag LIKE '%i%', 1, 0) AS inactive
            FROM {};
    """,
    4: """
        INSERT INTO player_staging_union (id, period, name, fed, sex, title, wtitle, inactive)
        SELECT 
            id, 
            '{}-{}-01' AS period, 
            name,
            fed,
            IF(sex = 'F', 1, 0) AS sex,
            CASE title
                WHEN 'GM' THEN 1
                WHEN 'IM' THEN 2
                WHEN 'FM' THEN 3
                WHEN 'CM' THEN 4
                WHEN 'HM' THEN 5
                ELSE 0
            END AS title,
            CASE wtitle
                WHEN 'WGM' THEN 1
                WHEN 'WIM' THEN 2
                WHEN 'WF' THEN 3
                WHEN 'WFM' THEN 3
                WHEN 'WC' THEN 4
                WHEN 'WCM' THEN 4
                WHEN 'WH' THEN 5
                ELSE 0
            END AS wtitle,
            IF(flag LIKE '%i%', 1, 0) AS inactive
        FROM {};
    """,
    5: """
        INSERT INTO player_staging_union (id, period, name, fed, sex, title, wtitle, foa, inactive)
        SELECT 
            id, 
            '{}-{}-01' AS period, 
            name,
            fed,
            IF(sex = 'F', 1, 0) AS sex,
            CASE title
                WHEN 'GM' THEN 1
                WHEN 'IM' THEN 2
                WHEN 'FM' THEN 3
                WHEN 'CM' THEN 4
                WHEN 'HM' THEN 5
                ELSE 0
            END AS title,
            CASE wtitle
                WHEN 'WGM' THEN 1
                WHEN 'WIM' THEN 2
                WHEN 'WF' THEN 3
                WHEN 'WFM' THEN 3
                WHEN 'WC' THEN 4
                WHEN 'WCM' THEN 4
                WHEN 'WH' THEN 5
                ELSE 0
            END AS wtitle,
            CASE foa
                WHEN 'AGM' THEN 1
                WHEN 'AIM' THEN 2
                WHEN 'AFM' THEN 3
                WHEN 'ACM' THEN 4
                ELSE 0
            END AS foa,
            IF(flag LIKE '%i%', 1, 0) AS inactive
        FROM {};
    """
}
INSERT_INTO_STRINGS[2] = INSERT_INTO_STRINGS[1]
INSERT_INTO_STRINGS[3] = INSERT_INTO_STRINGS[1]

    
def transform(month_names: list[dict[str, str]]):
    # log_setup("transform", format="%(message)s")
    
    conn = duckdb.connect("fide_elo.duckdb")
    type_dict = helper.get_type_dict(month_names)
    for month_data in month_names:
        insert_string = INSERT_INTO_STRINGS[type_dict[(month_data["year4"], month_data["month"])]]
        conn.sql(insert_string.format(month_data['year4'], month_data['month_digits'], month_data['table_name']))
        # logging.info(f"{month_data['year']}-{month_data['month_digits']}: Inserted {cursor.rowcount} rows into player_staging_union")
    conn.commit()


if __name__ == "__main__":
    transform(get_period_range_kwargs={"start_year": 2012, "start_month": "nov", "end_year": 2012, "end_month": "dec"})
