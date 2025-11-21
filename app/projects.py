from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.db import get_db_connection
from psycopg import errors

projects_bp = Blueprint("projects", __name__,url_prefix="/projects")

# A3 -- All Projects
@projects_bp.route("/all", methods=["GET", "POST"])
def sort_projects():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    whitelisted_methods=["headcount", "total_hours", "project_number"]
    whitelisted_directions=["ASC", "DESC"]
    
    method = "project_number"
    direction = "ASC"
    if request.method == "POST": # On sorting options applied 
        
        method = request.form.get("method", "")
        direction = request.form.get("direction", "")
        # Validate inputs against whitelisted options before querying  
        if method not in whitelisted_methods:
            method = "headcount"
        if direction not in whitelisted_directions:
            direction = "ASC"

    cur.execute(
        f"""
        SELECT
            p.pnumber AS project_number, 
            p.pname AS project_name, 
            d.dname AS owning_department, 
            COUNT(w.essn) AS headcount,
            COALESCE(SUM(w.hours), 0) AS total_hours  
        FROM project p
        JOIN department d ON p.dnum = d.dnumber
        LEFT JOIN works_on w ON p.pnumber = w.pno
        GROUP BY p.pnumber, d.dnumber
        ORDER BY {method} {direction};
        """
    )
    project_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("projects.html", projects=project_list)

# A4 -- Project Details    
@projects_bp.route("/<pnumber>", methods=["GET", "POST"])
def project_detail(pnumber):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    conn = get_db_connection()
    cur = conn.cursor()
    # Select all employees on the project and their hours
    cur.execute(
        """
        SELECT 
            e.fname as first_name, 
            e.minit as middle_initial,
            e.lname as last_name, 
            w.hours as hours
        FROM employee e
        JOIN works_on w ON e.ssn = w.essn
        WHERE w.pno = %s
        ORDER BY e.fname;
        """,
        (pnumber,)
    )
    project_details = cur.fetchall()
    
    # Select all employees in the database
    cur.execute(
        """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY e.fname) AS rownum,
            e.fname AS first_name, 
            e.minit AS middle_initial,
            e.lname AS last_name
        FROM employee e;

        """
    )
    all_employees = cur.fetchall()
    
    # A4 Part 2: Employee Upsert Form submission
    if request.method == "POST":
        employee_n = int(request.form.get("employee", "")) # using index in case two employees have the same full name
        hours = request.form.get("hours", "")
        
        cur.execute(
            """
            SELECT ssn
            FROM employee
            ORDER BY fname
            """
        )
        employee_ssns = cur.fetchall()
        target_ssn = employee_ssns[employee_n-1][0] #get the ssn of the employee we want
        #add the employee to the works_on for that pnumber, or update their hours 
        try:
            cur.execute(
                """
                INSERT INTO works_on (essn, pno, hours)
                VALUES (%s, %s, %s)
                ON CONFLICT (essn, pno)
                DO UPDATE SET hours = works_on.hours + EXCLUDED.hours;
                """,
                (target_ssn, pnumber, hours)
            )
            conn.commit()
        except errors.NumericValueOutOfRange:
            conn.rollback()
            print("\033[1;91mError: Cannot add more hours to employee (max hours is 999.9)\033[0m")
            flash("Cannot add more hours to employee (max hours is 999.9 per employee)", "error")
        cur.close()
        conn.close()
        return redirect(url_for("projects.project_detail", pnumber=pnumber))    
    cur.close()
    conn.close()
    return render_template("project_detail.html", details=project_details, pnumber=pnumber, employees=all_employees)