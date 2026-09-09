-- table definitions are here, imports are done in import_to_db.py
-- import_to_db.py is used for actual database import and creation
CREATE DATABASE IF NOT EXISTS elo_db;
USE elo_db;

-- type 1
-- Jan 01
CREATE TABLE staging_01_jan (
    temp VARCHAR(255),
    id INT PRIMARY KEY,
    name VARCHAR(255),
    title VARCHAR(7),
    fed CHAR(3),
    elo INT,
    games INT,
    flag VARCHAR(3)
);
LOAD DATA LOCAL INFILE 'fide_historical_ratings_formatted/JAN01.csv' INTO TABLE staging_01_jan FIELDS TERMINATED BY '*' IGNORE 1 ROWS;
DELETE FROM staging_01_jan WHERE id=0;

-- type 2
-- Apr 01, Jan 02, Jul02-aug12
CREATE TABLE staging_01_apr (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(7),
    fed CHAR(3) NOT NULL,
    elo INT NOT NULL,
    games INT NOT NULL,
    birthday VARCHAR(15),
    flag VARCHAR(3)
);

-- type 3
-- Jul 01, Oct 01, Apr 02
CREATE TABLE staging_01_apr (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(7),
    fed CHAR(3) NOT NULL,
    elo INT NOT NULL,
    games INT NOT NULL,
    birthday VARCHAR(15),
    sex CHAR(1),
    flag VARCHAR(3)
);


--type 4
-- Sep12-aug16
CREATE TABLE staging__ (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    fed CHAR(3),
    sex CHAR(1),
    title VARCHAR(7),
    wtitle VARCHAR(7),
    otitle VARCHAR(15),
    elo INT,
    games INT,
    k INT,
    birthday VARCHAR(5),
    flag VARCHAR(3)
);

--type 5
-- Sep 16-present
CREATE TABLE staging__ (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    fed CHAR(3) NOT NULL,
    sex CHAR(1),
    title VARCHAR(7),
    wtitle VARCHAR(7),
    otitle VARCHAR(15),
    foa VARCHAR(3),
    elo INT NOT NULL,
    games INT NOT NULL,
    k INT NOT NULL,
    birthday VARCHAR(5),
    flag VARCHAR(3)
);


CREATE TABLE players (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    fed CHAR(3) NOT NULL,
    elo INT NOT NULL,
    games INT NOT NULL,
    flag VARCHAR(3)
);

-- TODO: needs a diff primary key
-- this table exists to account for inconsistencies in the data, and to allow for a more complete player dataset
CREATE TABLE player_complete_data (
    id INT PRIMARY KEY,
    year INT NOT NULL,
    month INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    fed CHAR(3) NOT NULL,
    sex CHAR(1),
    birthday VARCHAR(10)
);
    

-- simplified data table
CREATE TABLE player_complete_data (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    fed CHAR(3) NOT NULL,
    sex CHAR(1)
);

CREATE TABLE elo (
    id INT PRIMARY KEY,
    year INT NOT NULL,
    month INT NOT NULL,
    elo INT NOT NULL,
    games INT NOT NULL,
    k INT,
    is_active CHAR(1) NOT NULL
);

CREATE TABLE titles (
    id INT PRIMARY KEY,
    year INT NOT NULL,
    month INT NOT NULL,
    title VARCHAR(7),
    wtitle VARCHAR(7),
    otitle VARCHAR(15),
    foa VARCHAR(3)
);
    