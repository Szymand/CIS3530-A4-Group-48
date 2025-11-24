from werkzeug.security import generate_password_hash
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg.connect(
    dbname="company_portal_db",
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

cur = conn.cursor()

username = "admin"
password = "test123"   
    

password_hash = generate_password_hash(password)

cur.execute("""
    INSERT INTO app_user (username, password_hash, role)
    VALUES (%s, %s, %s)
    ON CONFLICT (username) DO NOTHING;
""", (username, password_hash, "admin"))

conn.commit()
cur.close()
conn.close()

print("User created:", username)
