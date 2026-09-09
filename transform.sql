-- sep16-present
create table staging_union (
	id int not null,
	year smallint not null check(year between 1800 and 2200),
	month tinyint not null check(month between 1 and 12),
	name varchar(255) NOT NULL,
	fed char(3) NOT NULL,
	sex char(1) DEFAULT NULL,
	title varchar(7) DEFAULT NULL,
	wtitle varchar(7) DEFAULT NULL,
	otitle varchar(15) DEFAULT NULL,
	foa varchar(3) DEFAULT NULL,
	elo smallint NOT null check(elo between 0 and 5000),
	games smallint NOT NULL,
	k tinyint unsigned NOT NULL,
	birthday smallint DEFAULT NULL,
	flag varchar(2) DEFAULT NULL,
	primary key (id, year, month)
);

insert into staging_union
select
    id,
    2026 as year,
    1 as month,
    trim(name) as name,
    title,
    foa
from staging_temp;



create table periodic_metadata (
	id int not null,
	year smallint not null check(year between 1800 and 2200),
	month tinyint not null check(month between 1 and 12),
	elo smallint NOT null check(elo between 0 and 5000),
	games smallint NOT NULL,
	k tinyint unsigned,
	inactive boolean not null,
	primary key (id, year, month)
);


create table periodic_data (
    id int not null,
	year smallint not null check(year between 1800 and 2200),
	month tinyint not null check(month between 1 and 12),
	name varchar(255) NOT NULL,
	fed char(3) NOT NULL,
	sex char(1) DEFAULT NULL,
	title varchar(7) DEFAULT NULL,
	wtitle varchar(7) DEFAULT NULL,
	otitle varchar(15) DEFAULT NULL,
	foa varchar(3) DEFAULT NULL,
	elo smallint NOT null check(elo between 0 and 5000),
	games smallint NOT NULL,
	k tinyint unsigned NOT NULL,
    active boolean not null,
	primary key (id, year, month)
);





-- don't use DATE because some birthdays may only have year
-- log error rows and skip instead of auto failing

-- players should auto update with new data
-- 20+257 bytes
create table players (
    id int not null,
    birthyear smallint check(year between 1800 and 2200),
    birthmonth tinyint check(month between 1 and 12),
    birthday tinyint check(day between 1 and 31),
    name VARCHAR(255) NOT NULL,
    fed CHAR(3) NOT NULL,
    sex CHAR(1) DEFAULT NULL,
    title tinyint unsigned not null, -- 0 = none, 1 = GM, 2 = IM, 3 = FM, 4 = WGM, 5 = WIM, 6 = WFM
    foa tinyint unsigned not null, -- 0 = none, 1 = AFM, 2 = AIM, 3 = ACM, 4 = AGM, 5 = AAF 
    otit_ia boolean not null,
    otit_fa boolean not null,
    otit_na boolean not null,
    otit_io boolean not null,
    otit_ft boolean not null,
    otit_fst boolean not null
    primary key id
);

-- no wtit, its redundant
-- foa and otit are nullable because they are not present until 2016/2012 respectively
-- 20+62 bytes
CREATE TABLE player_profiles (
    profile_id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT NOT NULL,
    effective_date DATE NOT NULL,
    name VARCHAR(255) NOT NULL,
    fed CHAR(3) NOT NULL,
    sex CHAR(1) DEFAULT NULL,
    title tinyint unsigned not null, -- 0 = none, 1 = GM, 2 = IM, 3 = FM, 4 = WGM, 5 = WIM, 6 = WFM
    foa tinyint unsigned, -- 0 = none, 1 = AFM, 2 = AIM, 3 = ACM, 4 = AGM, 5 = AAF 
    otit_ia boolean,
    otit_fa boolean,
    otit_na boolean,
    otit_io boolean,
    otit_ft boolean,
    otit_fst boolean,
    PRIMARY KEY (profile_id),
    FOREIGN KEY (player_id) REFERENCES players(id)
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