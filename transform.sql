/*
staging table to simplify the process and unify the data for import into the player/profile
  because each year has its own standards for some reason
Unneeded columns:
 - birthday, only needed by the players table, not profile, because it shouldn't change over time
 - elo, games, k, these are only needed in the elo table
allow null for foa and other titles because they are not present for all time periods
*/
create table player_staging_union (
    id int not null,
    period date not null,
    name varchar(255) NOT NULL,
    fed char(3) not null,
    sex tinyint unsigned not null,
    title tinyint unsigned not null default 0, -- 0 = none, 1 = GM, 2 = IM, 3 = FM, 4 = CM, 5 = HGM
    wtitle tinyint unsigned not null default 0, -- 0 = none, 1 = WGM, 2 = WIM, 3 = WFM, 4 = WCM, 5 = WHGM
    foa tinyint unsigned, -- 0 = none, 1 = AGM, 2 = AIM, 3 = AFM, 4 = ACM, 5 = AAF 
    otit_ia boolean, -- arbiter titles
    otit_fa boolean,
    otit_na boolean,
    otit_io boolean, -- international organizer
    otit_ao boolean,
    otit_di boolean, -- trainer titles
    otit_ni boolean,
    otit_fi boolean,
    otit_ft boolean,
    otit_fst boolean, 
    otit_li boolean, -- licensed instructors
    otit_lsi boolean,
    otit_sli boolean,
    inactive boolean NOT NULL,
    primary key (id, period)
);

-- jan 01
insert into player_staging_union (id, period, name, fed, sex, title, wtitle, inactive)
select 
    id, 
    "2001-01-01" as period, 
    name,
    fed,
    if(flag like "%w%", 1, 0) as sex,
    case title
        when "g" then 1
        when "gm" then 1
        when "m" then 2
        when "f" then 3
        when "c" then 4
        when "h" then 5
        else 0
    end as title,
    case title
        when "wg" then 1
        when "wm" then 2
        when "wf" then 3
        when "wc" then 4
        when "wh" then 5
        else 0
    end as wtitle,
    if(flag like "%i%", 1, 0) as inactive
from staging_01_jan;


-- type 4
insert into player_staging_union (id, period, name, fed, sex, title, wtitle, foa, inactive)
select 
    id, 
    concat(year, '-', month, '-01') as period, 
    name,
    fed,
    if(sex="F", 1, 0) as sex,
    case title
        when "GM" then 1
        when "IM" then 2
        when "FM" then 3
        when "CM" then 4
        when "HM" then 5
        else 0
    end as title,
    case wtitle
        when "WGM" then 1
        when "WIM" then 2
        when "WF" then 3
        when "WFM" then 3
        when "WC" then 4
        when "WCM" then 4
        when "WH" then 5
        else 0
    end as wtitle,
    case foa
        when "AGM" then 1
        when "AIM" then 2
        when "AFM" then 3
        when "ACM" then 4
        when "AAF" then 5
        else 0
    end as foa,
    if(flag like "%i%", 1, 0) as inactive
from staging_01_jan;

-- don't use DATE because some birthdays may only have year
-- log error rows and skip instead of auto failing

-- players should auto update with new data
-- 20 bytes + NAME
create table players (
    id int not null,
    birthday date,
    is birthday_exact boolean,
    name VARCHAR(255) NOT NULL,
    fed CHAR(3) NOT NULL,
    sex CHAR(1) DEFAULT NULL,
    title tinyint unsigned not null, -- 0 = none, 1 = GM, 2 = IM, 3 = FM, 4 = CM, 5 = HGM
    wtitle tinyint unsigned not null, -- 0 = none, 1 = WGM, 2 = WIM, 3 = WFM, 4 = WCM, 5 = WHGM
    foa tinyint unsigned not null -- 0 = none, 1 = AFM, 2 = AIM, 3 = ACM, 4 = AGM, 5 = AAF 
    primary key id
);

-- 20+62 bytes
CREATE TABLE player_profiles (
    profile_id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT NOT NULL,
    effective_date DATE NOT NULL,
    end_date DATE NOT NULL, -- exclusive, using sentinel date 9999-12-31 for current?
    name VARCHAR(255) NOT NULL,
    fed CHAR(3) NOT NULL,
    sex CHAR(1) DEFAULT NULL,
    title tinyint unsigned not null, -- 0 = none, 1 = GM, 2 = IM, 3 = FM, 4 = CM, 5 = HGM
    wtitle tinyint unsigned not null, -- 0 = none, 1 = WGM, 2 = WIM, 3 = WFM, 4 = WCM, 5 = WHGM
    PRIMARY KEY (profile_id),
    FOREIGN KEY (player_id) REFERENCES players(id)
);

create table other_title_profiles (
    player_id int not null,
    effective_date date not null,
    foa tinyint unsigned, -- 0 = none, 1 = AFM, 2 = AIM, 3 = ACM, 4 = AGM
    otit_ia boolean, -- arbiter titles
    otit_fa boolean,
    otit_na boolean,
    otit_io boolean, -- international organizer
    otit_ao boolean,
    otit_di boolean, -- trainer titles
    otit_ni boolean,
    otit_fi boolean,
    otit_ft boolean,
    otit_fst boolean, 
    otit_li boolean, -- licensed instructors
    otit_lsi boolean,
    otit_sli boolean,
    primary key (player_id, effective_date),
    foreign key (player_id) references players(id)
);

-- 13 bytes
create table periodic_elo (
    period_id int auto_increment primary key,
    player_id int not null,
    period DATE not null,
    elo smallint NOT null check(elo between 0 and 5000),
    games smallint NOT NULL,
    k tinyint unsigned,
    inactive boolean not null,
    foreign key (player_id) references players(id)
);

-- make sure to remove k when needed
-- since player_id is a fkey, players must be loaded first
insert into periodic_elo (player_id, period, elo, games, k, inactive)
select id, concat(year, '-', month, '-01'), elo, games, k, inactive
from staging_;

-- load players table with jan01
insert into players (id, name, fed, sex, title)