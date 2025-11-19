from flask import Blueprint, session, redirect, url_for, render_template
from app.db import get_db_connection

employees_bp = Blueprint("employees", __name__)

@employees_bp.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    return render_template("home_employees.html")
