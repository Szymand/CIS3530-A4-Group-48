from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.db import get_db_connection
from psycopg import errors

employee_management_bp = Blueprint("employee_management", __name__, url_prefix="/employees")

# A5: Employee List
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
        
        return render_template("employee_management/employee_list.html", employees=employees)
    
    except Exception as e:
        flash(f"Error loading employees: {str(e)}", "error")
        return render_template("employee_management/employee_list.html", employees=[])

# A5: Add Employee Form
@employee_management_bp.route("/add", methods=["GET"])
def add_employee_form():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
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

# A5: Add Employee Submission
@employee_management_bp.route("/add", methods=["POST"])
def add_employee():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    ssn = request.form.get("ssn", "").strip()
    fname = request.form.get("fname", "").strip()
    minit = request.form.get("minit", "").strip()
    lname = request.form.get("lname", "").strip()
    address = request.form.get("address", "").strip()
    salary = request.form.get("salary", "").strip()
    dno = request.form.get("dno", "").strip()
    
    # Validation
    if not all([ssn, fname, lname, address, salary, dno]):
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
            INSERT INTO employee (ssn, fname, minit, lname, address, salary, dno)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (ssn, fname, minit, lname, address, salary, dno))
        
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

# A5: Edit Employee Form
@employee_management_bp.route("/edit/<ssn>", methods=["GET"])
def edit_employee_form(ssn):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
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

# A5: Edit Employee Submission
@employee_management_bp.route("/edit/<ssn>", methods=["POST"])
def edit_employee(ssn):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
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

# A5: Delete Employee
@employee_management_bp.route("/delete/<ssn>", methods=["POST"])
def delete_employee(ssn):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
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
