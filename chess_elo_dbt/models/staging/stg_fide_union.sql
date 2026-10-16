{% set month_numbers = {
    'jan': 1,
    'feb': 2,
    'mar': 3,
    'apr': 4,
    'may': 5,
    'jun': 6,
    'jul': 7,
    'aug': 8,
    'sep': 9,
    'oct': 10,
    'nov': 11,
    'dec': 12
} %}
{% set type_3_periods = ['staging_01_jul', 'staging_01_oct', 'staging_02_apr'] %}
{% set fide_sources = graph.sources.values() | selectattr('source_name', 'equalto', 'fide_elo') | list %}

with fide_union as (
{% for source_node in fide_sources %}
    {% set table_name = source_node.name %}
    {% set year = table_name.split('_')[1] | int %}
    {% set month = month_numbers[table_name.split('_')[2]] %}
    {% if table_name == 'staging_01_jan' %}
        {% set table_type = 1 %}
    {% elif table_name in type_3_periods %}
        {% set table_type = 3 %}
    {% elif year < 12 or (year == 12 and month < 9) %}
        {% set table_type = 2 %}
    {% elif year < 16 or (year == 16 and month < 9) %}
        {% set table_type = 4 %}
    {% else %}
        {% set table_type = 5 %}
    {% endif %}

    select
        cast(id as uinteger) as id,
        cast('{{ 2000 + year }}-{{ '%02d' | format(month) }}-01' as date) as period,
        cast(trim(name) as varchar(255)) as name,
        cast(trim(fed) as char(3)) as fed,
        {% if table_type in [1, 2] %}
        cast(if(trim(flag) like '%w%', 1, 0) as utinyint) as sex,
        {% else %}
        cast(if(trim(sex) = 'F', 1, 0) as utinyint) as sex,
        {% endif %}
        cast(elo as smallint) as elo,
        cast(games as smallint) as games,
        {% if table_type >= 4 %}
        cast(k as utinyint) as k,
        cast(trim(birthday) as varchar(30)) as birthday,
        {% else %}
        cast(null as utinyint) as k,
        {% if table_type in [2, 3] %}
        cast(trim(birthday) as varchar(30)) as birthday,
        {% else %}
        cast(null as varchar) as birthday,
        {% endif %}
        {% endif %}
        cast(case trim(title)
            when {% if table_type <= 3 %}'g'{% else %}'GM'{% endif %} then 1
            when {% if table_type <= 3 %}'gm'{% else %}'IM'{% endif %} then 2
            when {% if table_type <= 3 %}'m'{% else %}'FM'{% endif %} then 3
            when {% if table_type <= 3 %}'f'{% else %}'CM'{% endif %} then 4
            when {% if table_type <= 3 %}'c'{% else %}'HM'{% endif %} then 5
            {% if table_type <= 3 %}
            when 'h' then 5
            when 'hg' then 5
            when 'gh' then 5
            when 'wh' then 5
            {% else %}
            when 'WH' then 5
            {% endif %}
            else 0
        end as utinyint) as title,
        {% if table_type <= 3 %}
        cast(case trim(title)
            when 'wg' then 1
            when 'wm' then 2
            when 'wf' then 3
            when 'wc' then 4
            else 0
        end as utinyint) as wtitle,
        {% else %}
        cast(case trim(wtitle)
            when 'WGM' then 1
            when 'WIM' then 2
            when 'WF' then 3
            when 'WFM' then 3
            when 'WC' then 4
            when 'WCM' then 4
            else 0
        end as utinyint) as wtitle,
        {% endif %}
        {% if table_type == 5 %}
        cast(case trim(foa)
            when 'AGM' then 1
            when 'AIM' then 2
            when 'AFM' then 3
            when 'ACM' then 4
            else 0
        end as utinyint) as foa,
        {% else %}
        cast(null as utinyint) as foa,
        {% endif %}
        {% if table_type >= 4 %}
        cast(if(lower(trim(otitle)) like '%ia%', 1, 0) as boolean) as otit_ia,
        cast(if(lower(trim(otitle)) like '%fa%', 1, 0) as boolean) as otit_fa,
        cast(if(lower(trim(otitle)) like '%na%', 1, 0) as boolean) as otit_na,
        cast(if(lower(trim(otitle)) like '%io%', 1, 0) as boolean) as otit_io,
        cast(if(lower(trim(otitle)) like '%ao%', 1, 0) as boolean) as otit_ao,
        cast(if(lower(trim(otitle)) like '%di%', 1, 0) as boolean) as otit_di,
        cast(if(lower(trim(otitle)) like '%ni%', 1, 0) as boolean) as otit_ni,
        cast(if(lower(trim(otitle)) like '%fi%', 1, 0) as boolean) as otit_fi,
        cast(if(lower(trim(otitle)) like '%ft%', 1, 0) as boolean) as otit_ft,
        cast(if(lower(trim(otitle)) like '%fst%', 1, 0) as boolean) as otit_fst,
        cast(if(lower(trim(otitle)) like '%li%', 1, 0) as boolean) as otit_li,
        cast(if(lower(trim(otitle)) like '%lsi%', 1, 0) as boolean) as otit_lsi,
        cast(if(lower(trim(otitle)) like '%sli%', 1, 0) as boolean) as otit_sli,
        {% else %}
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
        {% endif %}
        cast(if(trim(flag) like '%i%', 1, 0) as boolean) as inactive
    from {{ source('fide_elo', table_name) }}
    {% if not loop.last %}
    union all
    {% endif %}
{% endfor %}
)

select *
from fide_union
where name <> 'Name'
