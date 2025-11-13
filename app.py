from flask import Flask, render_template
import psycopg

from dotenv import load_dotenv
import os

app = Flask(__name__)

# Load environment variables for database config credentials
load_dotenv()

# Same idea as the lab: DATABASE_CONFIG dict + get_db_connection()
# Slide "Connect from Python" and "DB setup" :contentReference[oaicite:2]{index=2}
DATABASE_CONFIG = {
    "dbname": "company_portal_db",   
    "user": "postgres",              
    "password": os.getenv("DB_PASSWORD"),
    "host": "localhost",
    "port": "5432",
}

def get_db_connection():
    conn = psycopg.connect(**DATABASE_CONFIG)
    return conn


@app.route("/")
def home():
    
    conn = get_db_connection()
    cur = conn.cursor()
    
  
    cur.execute("SELECT CURRENT_DATE;")
    current_date = cur.fetchone()[0]

    cur.close()
    conn.close()

    
    return render_template("index.html", current_date=current_date)


if __name__ == "__main__":
    app.run(debug=True)
