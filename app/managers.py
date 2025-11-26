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

# excel imports (bonus features)
@managers_bp.route("/import", methods=["GET"])
def import_departments_form():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    return render_template("import_departments.html")

@managers_bp.route("/import", methods=["POST"])
def import_departments():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('managers.import_departments_form'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('managers.import_departments_form'))
    
    if not file.filename.endswith('.xlsx'):
        flash('Only .xlsx files are allowed', 'error')
        return redirect(url_for('managers.import_departments_form'))
    
    try:
        
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        success_count = 0
        error_rows = []
        
        # Process each row 
        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):  # skip empty rows
                continue
                
            try:
                # Expected columns: dnumber, dname, mgr_ssn
                if len(row) < 3 or not all([row[0], row[1]]):  # dnumber and dname required
                    error_rows.append(f"Row {row_num}: Missing required fields")
                    continue
                
                dnumber, dname, mgr_ssn = row[0], row[1], row[2] if len(row) > 2 else None
                
                # Validate data types
                try:
                    dnumber = int(dnumber)
                except (ValueError, TypeError):
                    error_rows.append(f"Row {row_num}: Department number must be a number")
                    continue
                
                # Insert into department table
                cur.execute("""
                    INSERT INTO department (dnumber, dname, mgr_ssn)
                    VALUES (%s, %s, %s)
                """, (dnumber, dname, mgr_ssn))
                
                success_count += 1
                
            except errors.UniqueViolation:
                error_rows.append(f"Row {row_num}: Department number {dnumber} already exists")
                conn.rollback()
            except errors.ForeignKeyViolation:
                error_rows.append(f"Row {row_num}: Manager SSN {mgr_ssn} not found in employees")
                conn.rollback()
            except Exception as e:
                error_rows.append(f"Row {row_num}: {str(e)}")
                conn.rollback()
        
        if success_count > 0:
            conn.commit()
            flash(f'Successfully imported {success_count} departments', 'success')
        
        if error_rows:
            flash_errors = " | ".join(error_rows[:5])  # Show first 5 errors
            if len(error_rows) > 5:
                flash_errors += f" ... and {len(error_rows) - 5} more errors"
            flash(f'Import errors: {flash_errors}', 'error')
        
        cur.close()
        conn.close()
        
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
    
    return redirect(url_for('managers.import_departments_form'))
