from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.db import get_db_connection
from psycopg import errors
import openpyxl

managers_bp = Blueprint("managers", __name__, url_prefix="/managers")

# A6: Managers Overview
@managers_bp.route("/overview")
def managers_overview():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Query for department overview with manager info and stats
        cur.execute("""
            SELECT 
                d.dname AS department_name,
                d.dnumber AS department_number,
                COALESCE(e.fname || ' ' || e.minit || '. ' || e.lname, 'N/A') AS manager_name,
                COUNT(emp.ssn) AS employee_count,
                COALESCE(SUM(w.hours), 0) AS total_hours
            FROM department d
            LEFT JOIN employee e ON d.mgr_ssn = e.ssn
            LEFT JOIN employee emp ON d.dnumber = emp.dno
            LEFT JOIN works_on w ON emp.ssn = w.essn
            GROUP BY d.dnumber, d.dname, e.fname, e.minit, e.lname
            ORDER BY d.dname
        """)
        departments = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template("managers.html", departments=departments)
    
    except Exception as e:
        return render_template("managers.html", departments=[])


# Excel Import Bonus Feature (test)
@managers_bp.route("/import", methods=["GET"])
def import_departments_form():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    return "Import form would go here - route is working!"

