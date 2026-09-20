/*
staging table to simplify the process and unify the data for import into the player/profile
  because each year has its own standards for some reason
Unneeded columns:
 - birthday, only needed by the players table, not profile, because it shouldn't change over time
 - elo, games, k, these are only needed in the elo table
allow null for foa and other titles because they are not present for all time periods
*/
CREATE TABLE player_staging_union (
    id INTEGER NOT NULL,
    period DATE NOT NULL,
    name VARCHAR(255) NOT NULL,
    fed CHAR(3) NOT NULL,
    sex UTINYINT NOT NULL,
    title UTINYINT NOT NULL DEFAULT 0, -- 0 = none, 1 = GM, 2 = IM, 3 = FM, 4 = CM, 5 = HGM
    wtitle UTINYINT NOT NULL DEFAULT 0, -- 0 = none, 1 = WGM, 2 = WIM, 3 = WFM, 4 = WCM, 5 = WHGM
    foa UTINYINT, -- 0 = none, 1 = AGM, 2 = AIM, 3 = AFM, 4 = ACM, 5 = AAF
    otit_ia BOOLEAN, -- arbiter titles
    otit_fa BOOLEAN,
    otit_na BOOLEAN,
    otit_io BOOLEAN, -- international organizer
    otit_ao BOOLEAN,
    otit_di BOOLEAN, -- trainer titles
    otit_ni BOOLEAN,
    otit_fi BOOLEAN,
    otit_ft BOOLEAN,
    otit_fst BOOLEAN,
    otit_li BOOLEAN, -- licensed instructors
    otit_lsi BOOLEAN,
    otit_sli BOOLEAN,
    inactive BOOLEAN NOT NULL,
    PRIMARY KEY (id, period)
);

-- jan 01
INSERT INTO player_staging_union (id, period, name, fed, sex, title, wtitle, inactive)
SELECT
    id,
    DATE '2001-01-01' AS period,
    name,
    fed,
    IF(flag LIKE '%w%', 1, 0) AS sex,
    CASE title
        WHEN 'g' THEN 1
        WHEN 'gm' THEN 1
        WHEN 'm' THEN 2
        WHEN 'f' THEN 3
        WHEN 'c' THEN 4
        WHEN 'h' THEN 5
        ELSE 0
    END AS title,
    CASE title
        WHEN 'wg' THEN 1
        WHEN 'wm' THEN 2
        WHEN 'wf' THEN 3
        WHEN 'wc' THEN 4
        WHEN 'wh' THEN 5
        ELSE 0
    END AS wtitle,
    IF(flag LIKE '%i%', 1, 0) AS inactive
FROM staging_01_jan;

-- type 4
INSERT INTO player_staging_union (id, period, name, fed, sex, title, wtitle, foa, inactive)
SELECT
    id,
    CAST(CONCAT(year, '-', month, '-01') AS DATE) AS period,
    name,
    fed,
    IF(sex = 'F', 1, 0) AS sex,
    CASE title
        WHEN 'GM' THEN 1
        WHEN 'IM' THEN 2
        WHEN 'FM' THEN 3
        WHEN 'CM' THEN 4
        WHEN 'HM' THEN 5
        ELSE 0
    END AS title,
    CASE wtitle
        WHEN 'WGM' THEN 1
        WHEN 'WIM' THEN 2
        WHEN 'WF' THEN 3
        WHEN 'WFM' THEN 3
        WHEN 'WC' THEN 4
        WHEN 'WCM' THEN 4
        WHEN 'WH' THEN 5
        ELSE 0
    END AS wtitle,
    CASE foa
        WHEN 'AGM' THEN 1
        WHEN 'AIM' THEN 2
        WHEN 'AFM' THEN 3
        WHEN 'ACM' THEN 4
        WHEN 'AAF' THEN 5
        ELSE 0
    END AS foa,
    IF(flag LIKE '%i%', 1, 0) AS inactive
FROM staging_01_jan;

-- don't use DATE because some birthdays may only have year
-- log error rows and skip instead of auto failing

-- players should auto update with new data
-- 20 bytes + NAME
CREATE TABLE players (
    id INTEGER NOT NULL,
    birthday DATE,
    birthday_exact BOOLEAN,
    name VARCHAR(255) NOT NULL,
    fed CHAR(3) NOT NULL,
    sex CHAR(1) DEFAULT NULL,
    title UTINYINT NOT NULL, -- 0 = none, 1 = GM, 2 = IM, 3 = FM, 4 = CM, 5 = HGM
    wtitle UTINYINT NOT NULL, -- 0 = none, 1 = WGM, 2 = WIM, 3 = WFM, 4 = WCM, 5 = WHGM
    foa UTINYINT NOT NULL, -- 0 = none, 1 = AFM, 2 = AIM, 3 = ACM, 4 = AGM, 5 = AAF
    PRIMARY KEY (id)
);

-- 20+62 bytes
CREATE TABLE player_profiles (
    profile_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    player_id INTEGER NOT NULL,
    effective_date DATE NOT NULL,
    end_date DATE NOT NULL, -- exclusive, using sentinel date 9999-12-31 for current?
    name VARCHAR(255) NOT NULL,
    fed CHAR(3) NOT NULL,
    sex CHAR(1) DEFAULT NULL,
    title UTINYINT NOT NULL, -- 0 = none, 1 = GM, 2 = IM, 3 = FM, 4 = CM, 5 = HGM
    wtitle UTINYINT NOT NULL, -- 0 = none, 1 = WGM, 2 = WIM, 3 = WFM, 4 = WCM, 5 = WHGM
    FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE TABLE other_title_profiles (
    player_id INTEGER NOT NULL,
    effective_date DATE NOT NULL,
    foa UTINYINT, -- 0 = none, 1 = AFM, 2 = AIM, 3 = ACM, 4 = AGM
    otit_ia BOOLEAN, -- arbiter titles
    otit_fa BOOLEAN,
    otit_na BOOLEAN,
    otit_io BOOLEAN, -- international organizer
    otit_ao BOOLEAN,
    otit_di BOOLEAN, -- trainer titles
    otit_ni BOOLEAN,
    otit_fi BOOLEAN,
    otit_ft BOOLEAN,
    otit_fst BOOLEAN,
    otit_li BOOLEAN, -- licensed instructors
    otit_lsi BOOLEAN,
    otit_sli BOOLEAN,
    PRIMARY KEY (player_id, effective_date),
    FOREIGN KEY (player_id) REFERENCES players(id)
);

-- 13 bytes
CREATE TABLE periodic_elo (
    period_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    player_id INTEGER NOT NULL,
    period DATE NOT NULL,
    elo SMALLINT NOT NULL CHECK (elo BETWEEN 0 AND 5000),
    games SMALLINT NOT NULL,
    k UTINYINT,
    inactive BOOLEAN NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(id)
);

-- make sure to remove k when needed
-- since player_id is a fkey, players must be loaded first
INSERT INTO periodic_elo (player_id, period, elo, games, k, inactive)
SELECT id, CAST(CONCAT(year, '-', month, '-01') AS DATE), elo, games, k, inactive
FROM staging_;

-- load players table with jan01
INSERT INTO players (id, name, fed, sex, title)