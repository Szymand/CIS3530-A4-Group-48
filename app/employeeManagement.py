from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.db import get_db_connection
from psycopg import errors

employee_management_bp = Blueprint("employee_management", __name__, url_prefix="/employees")

# A5: Employee List (viewable by any logged-in user)
@employee_management_bp.route("/manage")
def manage_employees():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                ssn, fname, minit, lname, 
                address, salary, dno
            FROM employee 
            ORDER BY lname, fname
        """)
        employees = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template("employee_list.html", employees=employees)
    
    except Exception as e:
        flash(f"Error loading employees: {str(e)}", "error")
        return render_template("employee_list.html", employees=[])

# A5: Add Employee Form (admin only)
@employee_management_bp.route("/add", methods=["GET"])
def add_employee_form():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("role") != "admin":
        flash("You do not have permission to add employees.", "error")
        return redirect(url_for("employee_management.manage_employees"))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get departments for dropdown
        cur.execute("SELECT dnumber, dname FROM department ORDER BY dname")
        departments = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template("add_employee.html", departments=departments)
    
    except Exception as e:
        flash(f"Error loading form: {str(e)}", "error")
        return redirect(url_for("employee_management.manage_employees"))

# A5: Add Employee Submission (admin only)
@employee_management_bp.route("/add", methods=["POST"])
def add_employee():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("role") != "admin":
        flash("You do not have permission to add employees.", "error")
        return redirect(url_for("employee_management.manage_employees"))
    
    ssn = request.form.get("ssn", "").strip()
    fname = request.form.get("fname", "").strip()
    minit = request.form.get("minit", "").strip()
    lname = request.form.get("lname", "").strip()
    address = request.form.get("address", "").strip()
    salary = request.form.get("salary", "").strip()
    dno = request.form.get("dno", "").strip()
    sex = request.form.get("sex", "").strip()
    super_ssn = request.form.get("super_ssn", "").strip()
    birthdate = request.form.get("birthdate", "").strip()
    empdate = request.form.get("empdate", "").strip()
    
    # Validation
    if not all([ssn, fname, minit, lname, address, salary, dno, sex]):
        flash("All fields are required", "error")
        return redirect(url_for("employee_management.add_employee_form"))
    
    try:
        salary = float(salary)
        if salary <= 0:
            flash("Salary must be positive", "error")
            return redirect(url_for("employee_management.add_employee_form"))
    except ValueError:
        flash("Salary must be a valid number", "error")
        return redirect(url_for("employee_management.add_employee_form"))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert new employee
        cur.execute("""
            INSERT INTO employee (ssn, fname, minit, lname, address, salary, dno, sex, super_ssn, bdate, empdate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (ssn, fname, minit, lname, address, salary, dno, sex, super_ssn, birthdate, empdate))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash("Employee added successfully", "success")
        return redirect(url_for("employee_management.manage_employees"))
    
    except errors.UniqueViolation:
        flash("Error: SSN must be unique", "error")
        return redirect(url_for("employee_management.add_employee_form"))
    except errors.ForeignKeyViolation:
        flash("Error: Invalid department number", "error")
        return redirect(url_for("employee_management.add_employee_form"))
    except Exception as e:
        flash(f"Error adding employee: {str(e)}", "error")
        return redirect(url_for("employee_management.add_employee_form"))

# A5: Edit Employee Form (admin only)
@employee_management_bp.route("/edit/<ssn>", methods=["GET"])
def edit_employee_form(ssn):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("role") != "admin":
        flash("You do not have permission to edit employees.", "error")
        return redirect(url_for("employee_management.manage_employees"))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get employee data
        cur.execute("""
            SELECT ssn, fname, minit, lname, address, salary, dno
            FROM employee WHERE ssn = %s
        """, (ssn,))
        employee = cur.fetchone()
        
        if not employee:
            flash("Employee not found", "error")
            return redirect(url_for("employee_management.manage_employees"))
        
        # Get departments for dropdown
        cur.execute("SELECT dnumber, dname FROM department ORDER BY dname")
        departments = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template("edit_employee.html", 
                             employee=employee, departments=departments)
    
    except Exception as e:
        flash(f"Error loading employee: {str(e)}", "error")
        return redirect(url_for("employee_management.manage_employees"))

# A5: Edit Employee Submission (admin only)
@employee_management_bp.route("/edit/<ssn>", methods=["POST"])
def edit_employee(ssn):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("role") != "admin":
        flash("You do not have permission to edit employees.", "error")
        return redirect(url_for("employee_management.manage_employees"))
    
    address = request.form.get("address", "").strip()
    salary = request.form.get("salary", "").strip()
    dno = request.form.get("dno", "").strip()
    
    # Validation
    if not all([address, salary, dno]):
        flash("All fields are required", "error")
        return redirect(url_for("employee_management.edit_employee_form", ssn=ssn))
    
    try:
        salary = float(salary)
        if salary <= 0:
            flash("Salary must be positive", "error")
            return redirect(url_for("employee_management.edit_employee_form", ssn=ssn))
    except ValueError:
        flash("Salary must be a valid number", "error")
        return redirect(url_for("employee_management.edit_employee_form", ssn=ssn))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update employee (SSN is immutable per requirements)
        cur.execute("""
            UPDATE employee 
            SET address = %s, salary = %s, dno = %s
            WHERE ssn = %s
        """, (address, salary, dno, ssn))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash("Employee updated successfully", "success")
        return redirect(url_for("employee_management.manage_employees"))
    
    except errors.ForeignKeyViolation:
        flash("Error: Invalid department number", "error")
        return redirect(url_for("employee_management.edit_employee_form", ssn=ssn))
    except Exception as e:
        flash(f"Error updating employee: {str(e)}", "error")
        return redirect(url_for("employee_management.edit_employee_form", ssn=ssn))

# A5: Delete Employee (admin only)
@employee_management_bp.route("/delete/<ssn>", methods=["POST"])
def delete_employee(ssn):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("role") != "admin":
        flash("You do not have permission to delete employees.", "error")
        return redirect(url_for("employee_management.manage_employees"))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Try to delete employee
        cur.execute("DELETE FROM employee WHERE ssn = %s", (ssn,))
        conn.commit()
        cur.close()
        conn.close()
        
        flash("Employee deleted successfully", "success")
    
    except errors.ForeignKeyViolation:
        flash("Cannot delete employee: They are still assigned to projects, have dependents listed, or are a manager/supervisor.", "error")
    except Exception as e:
        flash(f"Error deleting employee: {str(e)}", "error")
    
    return redirect(url_for("employee_management.manage_employees"))
