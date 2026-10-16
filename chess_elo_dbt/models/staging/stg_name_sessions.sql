with union_periods_with_previous as (
    select
        id,
        period,
        min(name) as name,
        lag(period) over (
            partition by id
            order by period
        ) as previous_period
    from {{ ref('stg_union') }}
    group by id, period
),

union_periods as (
    select
        id,
        period,
        name,
        case
            when previous_period is null then 1
            when period <> cast(previous_period + interval '1 month' as date) then 1
            else 0
        end as starts_session
    from union_periods_with_previous
),

collision_periods as (
    select distinct
        id,
        period
    from {{ ref('stg_name_collisions') }}
    where partial_match = false
      and similarity < 0.5
),

session_events as (
    select
        union_periods.id,
        union_periods.period,
        union_periods.name,
        case
            when union_periods.starts_session = 1 then 1
            when collision_periods.id is not null then 1
            else 0
        end as starts_session
    from union_periods
    left join collision_periods
        on union_periods.id = collision_periods.id
        and union_periods.period = collision_periods.period
),

session_groups as (
    select
        id,
        period,
        name,
        sum(starts_session) over (
            partition by id
            order by period
            rows between unbounded preceding and current row
        ) as session_number
    from session_events
)

select
    id,
    min(period) as start_date,
    max(period) as end_date,
    arg_min(name, period) as start_name,
    arg_max(name, period) as end_name
from session_groups
group by id, session_number
