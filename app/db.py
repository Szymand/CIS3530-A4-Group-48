import psycopg

DATABASE_CONFIG = {
    "dbname": "company_portal_db",
    "user": "postgres",
    "password": "04292004",  
    "host": "localhost",
    "port": 5432,
}

def get_db_connection():
    return psycopg.connect(**DATABASE_CONFIG)