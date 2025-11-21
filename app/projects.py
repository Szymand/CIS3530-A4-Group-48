from flask import Blueprint, render_template, request
from app.db import get_db_connection

projects_bp = Blueprint("projects", __name__)

@projects_bp.route("/projects", methods=["GET", "POST"])
def sort_projects():
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    whitelisted_methods=["headcount", "total_hours"]
    whitelisted_directions=["ASC", "DESC"]
    
    method = "headcount"
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
    
    
    
    
