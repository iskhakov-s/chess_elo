import os
import mysql.connector
from mysql.connector.connection import MySQLConnection

from helper import initiate_conn

OLIMPBASE_PATH = os.path.join("olimpbase_records", "elo1967-2001", "all.csv")

def import_csv(conn: MySQLConnection):
    cursor = conn.cursor()
    cursor.execute(f"LOAD DATA LOCAL INFILE %s INTO TABLE staging_olimpbase CHARACTER SET latin1 FIELDS TERMINATED BY ';';", (OLIMPBASE_PATH,))
    conn.commit()
    
def main():
    conn = initiate_conn()
    import_csv(conn)
    conn.close() 
    
if __name__ == "__main__":
    main()