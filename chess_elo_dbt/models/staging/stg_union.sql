with olimpbase as (
    select
        id2 as id,
        period,
        name,
        fed,
        cast(null as utinyint) as sex,
        elo,
        games,
        cast(null as utinyint) as k,
        birthday,
        case lower(trim(title))
            when 'g' then 1
            when 'm' then 2
            when 'f' then 3
            when 'h' then 5
            when 'wh' then 5
            else 0
        end as title,
        case lower(trim(title))
            when 'wg' then 1
            when 'wm' then 2
            when 'wf' then 3
            else 0
        end as wtitle,
        cast(null as utinyint) as foa,
        cast(null as boolean) as otit_ia,
        cast(null as boolean) as otit_fa,
        cast(null as boolean) as otit_na,
        cast(null as boolean) as otit_io,
        cast(null as boolean) as otit_ao,
        cast(null as boolean) as otit_di,
        cast(null as boolean) as otit_ni,
        cast(null as boolean) as otit_fi,
        cast(null as boolean) as otit_ft,
        cast(null as boolean) as otit_fst,
        cast(null as boolean) as otit_li,
        cast(null as boolean) as otit_lsi,
        cast(null as boolean) as otit_sli,
        cast(null as boolean) as inactive
    from {{ ref('stg_olimpbase_new_ids') }}
),

fide as (
    select
        id,
        period,
        name,
        fed,
        sex,
        elo,
        games,
        k,
        birthday,
        title,
        wtitle,
        foa,
        otit_ia,
        otit_fa,
        otit_na,
        otit_io,
        otit_ao,
        otit_di,
        otit_ni,
        otit_fi,
        otit_ft,
        otit_fst,
        otit_li,
        otit_lsi,
        otit_sli,
        inactive
    from {{ ref('stg_fide_union') }}
)

select * from fide
union all
select * from olimpbase
