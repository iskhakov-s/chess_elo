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
                    WHEN 'hg' THEN 5
                    ELSE 0
                END AS title,
                CASE title
                    WHEN 'wg' THEN 1
                    WHEN 'wm' THEN 2
                    WHEN 'wf' THEN 3
                    WHEN 'wc' THEN 4
                    WHEN 'gh' THEN 5
                    WHEN 'wh' THEN 5
                    ELSE 0
                END AS wtitle,
                IF(flag LIKE '%i%', 1, 0) AS inactive
            FROM {};
    """,
    4: """
        INSERT INTO player_staging_union (
            id, period, name, fed, sex, title, wtitle,
            otit_ia, otit_fa, otit_na, otit_io, otit_ao,
            otit_di, otit_ni, otit_fi, otit_ft, otit_fst,
            otit_li, otit_lsi, otit_sli, inactive)
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
            IF (lower(otitle) LIKE '%ia%', 1, 0) AS otit_ia,
            IF (lower(otitle) LIKE '%fa%', 1, 0) AS otit_fa,
            IF (lower(otitle) LIKE '%na%', 1, 0) AS otit_na,
            IF (lower(otitle) LIKE '%io%', 1, 0) AS otit_io,
            IF (lower(otitle) LIKE '%ao%', 1, 0) AS otit_ao,
            IF (lower(otitle) LIKE '%di%', 1, 0) AS otit_di,
            IF (lower(otitle) LIKE '%ni%', 1, 0) AS otit_ni,
            IF (lower(otitle) LIKE '%fi%', 1, 0) AS otit_fi,
            IF (lower(otitle) LIKE '%ft%', 1, 0) AS otit_ft,
            IF (lower(otitle) LIKE '%fst%', 1, 0) AS otit_fst,
            IF (lower(otitle) LIKE '%li%', 1, 0) AS otit_li,
            IF (lower(otitle) LIKE '%lsi%', 1, 0) AS otit_lsi,
            IF (lower(otitle) LIKE '%sli%', 1, 0) AS otit_sli,
            IF(flag LIKE '%i%', 1, 0) AS inactive
        FROM {};
    """,
    5: """
        INSERT INTO player_staging_union (
            id, period, name, fed, sex, title, wtitle,
            otit_ia, otit_fa, otit_na, otit_io, otit_ao,
            otit_di, otit_ni, otit_fi, otit_ft, otit_fst,
            otit_li, otit_lsi, otit_sli, foa, inactive)
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
            IF (lower(otitle) LIKE '%ia%', 1, 0) AS otit_ia,
            IF (lower(otitle) LIKE '%fa%', 1, 0) AS otit_fa,
            IF (lower(otitle) LIKE '%na%', 1, 0) AS otit_na,
            IF (lower(otitle) LIKE '%io%', 1, 0) AS otit_io,
            IF (lower(otitle) LIKE '%ao%', 1, 0) AS otit_ao,
            IF (lower(otitle) LIKE '%di%', 1, 0) AS otit_di,
            IF (lower(otitle) LIKE '%ni%', 1, 0) AS otit_ni,
            IF (lower(otitle) LIKE '%fi%', 1, 0) AS otit_fi,
            IF (lower(otitle) LIKE '%ft%', 1, 0) AS otit_ft,
            IF (lower(otitle) LIKE '%fst%', 1, 0) AS otit_fst,
            IF (lower(otitle) LIKE '%li%', 1, 0) AS otit_li,
            IF (lower(otitle) LIKE '%lsi%', 1, 0) AS otit_lsi,
            IF (lower(otitle) LIKE '%sli%', 1, 0) AS otit_sli,
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
    log_setup("transform_2012_2026")
    
    conn = duckdb.connect("fide_elo.duckdb")
    type_dict = helper.get_type_dict(month_names)
    for month_data in month_names:
        insert_string = INSERT_INTO_STRINGS[type_dict[(month_data["year4"], month_data["month"])]]
        insert_string = insert_string.format(month_data['year4'], month_data['month_digits'], month_data['table_name'])
        try:
            conn.sql(insert_string)
            logging.info(f"{month_data['year']}-{month_data['month']}: Successful insertion")
        except duckdb.Error as e:
            logging.error(f"{month_data['year']}-{month_data['month']}: Error inserting into player_staging_union: {e}")
            continue
    conn.commit()


if __name__ == "__main__":
    transform(helper.get_period_range(start_year=2012, start_month="sep", end_year=2026, end_month="dec"))
