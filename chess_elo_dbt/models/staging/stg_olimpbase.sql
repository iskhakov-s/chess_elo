{{ config(static_analysis = 'off') }}

with raw_olimpbase as (
    select *
    from read_csv(
        '../olimpbase_records/elo1967-2001/all2.csv',
        header = false,
        sep = ';',
        columns = {
            'temp1': 'varchar',
            'name': 'varchar',
            'standard_name': 'varchar',
            'yyyymm': 'varchar',
            'id': 'varchar',
            'birthday': 'varchar',
            'title': 'varchar',
            'fed': 'varchar',
            'elo': 'varchar',
            'elo_change': 'varchar',
            'games': 'varchar',
            'flag': 'varchar',
            'comments': 'varchar',
            'fed2': 'varchar',
            'temp2': 'varchar'
        }
    )
),

name_changes as (
    select
        try_cast(id as integer) as id,
        standard_name,
        new_standard_name
    from {{ ref('olimpbase_name_changes') }}
)

select
    name,
    coalesce(name_changes.new_standard_name, raw_olimpbase.standard_name) as standard_name,
    try_cast(id as integer) as id,
    birthday,
    title,
    fed,
    try_cast(elo as integer) as elo,
    try_cast(elo_change as integer) as elo_change,
    try_cast(games as integer) as games,
    flag,
    comments,
    fed2,
    cast(
        substr(yyyymm, 1, 4) || '-' ||
        greatest(cast(substr(yyyymm, 5, 2) as integer), 1) || '-01'
        as date
    ) as period
from raw_olimpbase
left join name_changes
    on try_cast(raw_olimpbase.id as integer) = name_changes.id
    and raw_olimpbase.standard_name = name_changes.standard_name
