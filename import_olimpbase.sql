CREATE TABLE staging_olimpbase (
    name VARCHAR(255) NOT NULL,
    standard_name VARCHAR(255) NOT NULL,
    yyyymm VARCHAR(6),
    id INTEGER,
    birthday VARCHAR(255),
    title VARCHAR(7),
    fed CHAR(3),
    elo INTEGER,
    elo_change INTEGER, -- not needed
    games INTEGER,
    flag VARCHAR(255),
    comments VARCHAR(255),
    fed2 CHAR(3)
);

ALTER TABLE staging_olimpbase
    ADD COLUMN year SMALLINT,
    ADD COLUMN month TINYINT;

UPDATE staging_olimpbase
SET year = CAST(SUBSTR(yyyymm, 1, 4) AS SMALLINT);

UPDATE staging_olimpbase
SET month = CAST(SUBSTR(yyyymm, 5) AS TINYINT);