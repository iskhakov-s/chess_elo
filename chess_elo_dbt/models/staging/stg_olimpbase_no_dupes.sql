with periods as (
    select
        standard_name,
        period,
        lag(period) over (
            partition by standard_name
            order by period
        ) as previous_period
    from {{ ref('stg_olimpbase') }}
    group by standard_name, period
),

source_rows as (
    select
        source.*,
        periods.previous_period,
        row_number() over () as source_row_id
    from {{ ref('stg_olimpbase') }} source
    inner join periods
        using (standard_name, period)
),

rows_with_difference as (
    select
        current_row.*,
        case
            when current_row.previous_period is null then null
            else cast(current_row.fed is distinct from previous_row.fed as integer)
                + cast(current_row.elo is distinct from previous_row.elo as integer)
                + cast(current_row.name is distinct from previous_row.name as integer)
        end as difference_count
    from source_rows current_row
    left join source_rows previous_row
        on current_row.standard_name = previous_row.standard_name
        and current_row.previous_period = previous_row.period
),

scored_rows as (
    select
        *,
        min(difference_count) over (
            partition by source_row_id
        ) as minimum_difference_count
    from rows_with_difference
),

ranked_rows as (
    select
        *,
        row_number() over (
            partition by standard_name, period
            order by minimum_difference_count asc nulls last, random()
        ) as row_number
    from scored_rows
)

select
    * exclude (
        previous_period,
        source_row_id,
        difference_count,
        minimum_difference_count,
        row_number
    )
from ranked_rows
where row_number = 1