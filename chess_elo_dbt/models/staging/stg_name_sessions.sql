with union_periods as (
    select
        id,
        period,
        row_number() over (
            partition by id
            order by period
        ) as period_number
    from {{ ref('stg_union') }}
    group by id, period
),

collision_periods as (
    select distinct
        id,
        period
    from {{ ref('stg_name_collision') }}
    where partial_match = false
      and similarity < 0.5
),

session_events as (
    select
        union_periods.id,
        union_periods.period,
        case
            when union_periods.period_number = 1 then 1
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
    max(period) as end_date
from session_groups
group by id, session_number
