with player_stats as (
    select
        standard_name,
        max(period) as latest_period,
        arg_max(id, period) filter (
            where id is not null
              and period >= date '1990-07-01'
        ) as latest_id
    from {{ ref('stg_olimpbase') }}
    group by standard_name
),

assignments as (
    select
        player_stats.*,
        row_number() over (order by standard_name) as fake_id_number,
        exists (
            select 1
            from {{ ref('stg_olimpbase') }} collisions
            where collisions.id = player_stats.latest_id
              and collisions.period > player_stats.latest_period
        ) as has_collision
    from player_stats
),

new_ids as (
    select
        standard_name,
        case
            when latest_period < date '1990-07-01'
              or latest_id is null
              or has_collision
            then cast(4000000000 + fake_id_number as uinteger)
            else cast(latest_id as uinteger)
        end as id2
    from assignments
)

select
    source.*,
    new_ids.id2
from {{ ref('stg_olimpbase') }} source
left join new_ids
    using (standard_name)