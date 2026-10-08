{{ config(static_analysis = 'off') }}

with raw_olimpbase as (
    select *
    from read_csv(
        'olimpbase_records/elo1967-2001/all2.csv',
        header = false,
        sep = ';',
        columns = {
            'temp1': 'varchar',
            'name': 'varchar',
            'standard_name': 'varchar',
            'yyyymm': 'varchar',
            'id': 'integer',
            'birthday': 'varchar',
            'title': 'varchar',
            'fed': 'varchar',
            'elo': 'integer',
            'elo_change': 'integer',
            'games': 'integer',
            'flag': 'varchar',
            'comments': 'varchar',
            'fed2': 'varchar',
            'temp2': 'varchar'
        }
    )
)

select
    name,
    standard_name,
    id,
    birthday,
    title,
    fed,
    elo,
    elo_change,
    games,
    flag,
    comments,
    fed2,
    cast(
        substr(yyyymm, 1, 4) || '-' ||
        greatest(cast(substr(yyyymm, 5, 2) as integer), 1) || '-01'
        as date
    ) as period
from raw_olimpbase
