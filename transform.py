import helper
import mpi_logging


def transform_type_1_2_3():
    conn = helper.initiate_conn(get_warnings=True)
    with conn.cursor() as cursor:
        table_data = helper.get_period_range(
            start_year=2001,
            start_month="apr",
            end_year=2012,
            end_month="aug",
            table_data=helper.get_table_data(),
        )
        cursor.execute("""
            insert into player_staging_union (id, period, name, fed, sex, title, wtitle, inactive)
                select 
                    id, 
                    concat(year, '-', month, '-01') as period, 
                    name,
                    fed,
                    if(flag like "%w%", 1, 0) as sex,
                    case title
                        when "g" then 1
                        when "gm" then 1
                        when "m" then 2
                        when "f" then 3
                        when "c" then 4
                        when "h" then 5
                        else 0
                    end as title,
                    case title
                        when "wg" then 1
                        when "wm" then 2
                        when "wf" then 3
                        when "wc" then 4
                        when "wh" then 5
                        else 0
                    end as wtitle,
                    if(flag like "%i%", 1, 0) as inactive
                from staging_01_jan;
            );
        """)


def transform_type_4(month_names: list[dict[str, str]], rank):
    conn = helper.initiate_conn(get_warnings=True)
    with conn.cursor() as cursor:
        for month_data in month_names:
            cursor.execute(f"""
                insert into player_staging_union (id, period, name, fed, sex, title, wtitle, inactive)
                select 
                    id, 
                    concat("{month_data['year4']}", "-", "{month_data['month_digits']}", "-01") as period, 
                    name,
                    fed,
                    if(sex="F", 1, 0) as sex,
                    case title
                        when "GM" then 1
                        when "IM" then 2
                        when "FM" then 3
                        when "CM" then 4
                        when "HM" then 5
                        else 0
                    end as title,
                    case wtitle
                        when "WGM" then 1
                        when "WIM" then 2
                        when "WF" then 3
                        when "WFM" then 3
                        when "WC" then 4
                        when "WCM" then 4
                        when "WH" then 5
                        else 0
                    end as wtitle,
                    if(flag like "%i%", 1, 0) as inactive
                from {month_data['table_name']};
            """)
            if cursor.warnings:
                for warning in cursor.warnings:
                    mpi_logging.mpi_log(
                        rank,
                        f"{month_data['year']}-{month_data['month_digits']}: {warning}",
                    )
            mpi_logging.mpi_log(
                rank,
                f"{month_data['year']}-{month_data['month_digits']}: Inserted {cursor.rowcount} rows into player_staging_union",
            )
    conn.commit()
    conn.close()


def transform_type_5(month_names: list[dict[str, str]], rank):
    conn = helper.initiate_conn(get_warnings=True)
    with conn.cursor() as cursor:
        for month_data in month_names:
            cursor.execute(f"""
                insert into player_staging_union (id, period, name, fed, sex, title, wtitle, foa, inactive)
                select 
                    id, 
                    concat('{month_data['year4']}', '-', '{month_data['month_digits']}', '-01') as period, 
                    name,
                    fed,
                    if(sex="F", 1, 0) as sex,
                    case title
                        when "GM" then 1
                        when "IM" then 2
                        when "FM" then 3
                        when "CM" then 4
                        when "HM" then 5
                        else 0
                    end as title,
                    case wtitle
                        when "WGM" then 1
                        when "WIM" then 2
                        when "WF" then 3
                        when "WFM" then 3
                        when "WC" then 4
                        when "WCM" then 4
                        when "WH" then 5
                        else 0
                    end as wtitle,
                    case foa
                        when "AGM" then 1
                        when "AIM" then 2
                        when "AFM" then 3
                        when "ACM" then 4
                        when "AAF" then 5
                        else 0
                    end as foa,
                    if(flag like "%i%", 1, 0) as inactive
                from {month_data['table_name']};
            """)
            if cursor.warnings:
                for warning in cursor.warnings:
                    mpi_logging.mpi_log(
                        rank,
                        f"{month_data['year']}-{month_data['month_digits']}: {warning}",
                    )
            mpi_logging.mpi_log(
                rank,
                f"{month_data['year']}-{month_data['month_digits']}: Inserted {cursor.rowcount} rows into player_staging_union",
            )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    helper.mpi_main(transform_type_4, "transform_type_4", get_period_range_kwargs={"start_year": 2012, "start_month": "nov", "end_year": 2012, "end_month": "dec"})
