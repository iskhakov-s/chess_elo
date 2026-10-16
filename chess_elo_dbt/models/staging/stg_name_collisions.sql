{{ config(static_analysis = 'off') }}
{% set min_substring_length = var('min_substring_length', 5) %}

with names_with_previous as (
    select
        id,
        name,
        period,
        lag(name) over (
            partition by id
            order by period
        ) as prev_name,
        lag(period) over (
            partition by id
            order by period
        ) as prev_period
    from {{ ref('stg_union') }}
),

name_metrics as (
    select
        id,
        name,
        period,
        prev_name,
        prev_period,
        coalesce(
            {{ min_substring_length }} > 0
            and length(lower(name)) >= {{ min_substring_length }}
            and length(lower(prev_name)) >= {{ min_substring_length }}
            and len(
                list_filter(
                    list_filter(
                        [
                            lower(name)[i:i + {{ min_substring_length }} - 1]
                            for i in range(1, length(lower(name)) - {{ min_substring_length }} + 2)
                        ],
                        x -> not (contains(x, ' ') or contains(x, ','))
                    ),
                    x -> contains(lower(prev_name), x)
                )
            ) > 0,
            false
        ) as partial_match,
        levenshtein(lower(name), lower(prev_name)) as distance
    from names_with_previous
    where prev_name is not null
)

select
    id,
    name,
    period,
    prev_name,
    prev_period,
    partial_match,
    distance,
    1 - (
        distance / greatest(length(name), length(prev_name))
    ) as similarity
from name_metrics
