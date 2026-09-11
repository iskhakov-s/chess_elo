create table staging_olimpbase (
    name varchar(255) NOT NULL,
    standard_name varchar(255) NOT NULL,
    yyyymm,
    id int,
    birthday varchar(255),
    title varchar(7),
    fed char(3),
    elo int,
    elo_change int, -- not needed
    games int,
    flag varchar(255),
    comments varchar(255),
    fed2 char(3)
);

alter table staging_olimpbase 
add column year smallint, 
add column month tinyint;

update staging_olimpbase
set year=SUBSTR(yyyymm, 1, 4);

update staging_olimpbase
set month=SUBSTR(yyyymm, 5);