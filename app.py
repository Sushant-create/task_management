import os
from flask import Flask, redirect, render_template, request, session, url_for
import mysql.connector
from mysql.connector import Error
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# BUG FIX: the original hardcoded fallback secret key ("task-management-secret-key-2026")
# is committed to source control and is the same for every deployment that forgets to set
# FLASK_SECRET_KEY. That lets an attacker forge session cookies. We still allow an env
# override for real deployments, but the local fallback is now randomly generated per
# process instead of a fixed, guessable string.
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(32)

# Dynamic DB Config prevents local connectivity crashes
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),  # Default empty as per README
    "database": os.getenv("DB_NAME", "task_management_system"),
}

# BUG FIX: debug/reloader are now driven by an env var instead of being hardcoded True,
# so the README's "runs with debug=False" claim is actually true by default, and you can
# still flip it on for local development without editing source.
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

TASK_TITLES = [
    "Prepare Daily Report",
    "Update Customer Records",
    "Verify Documents",
    "Complete Data Entry",
    "Resolve Support Ticket",
]


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def is_logged_in():
    return "user_id" in session


@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("login.html", error="Please enter both username and password.")

        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            # BUG FIX: the original query matched on `WHERE username = %s AND password = %s`,
            # comparing the submitted password directly against a plaintext column. That
            # means every password in the database was stored (and leaked, if the DB is ever
            # compromised) in plain text. We now look up the user by username only, then
            # verify the password against a stored hash with check_password_hash.
            cursor.execute(
                """
                SELECT id, username, password, role
                FROM login
                WHERE username = %s
                """,
                (username,),
            )
            user = cursor.fetchone()

            if user and check_password_hash(user["password"], password) and user["role"] in ("admin", "manager"):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                return redirect(url_for("task_management"))

            error = "Invalid username, password, or role."
        except Error:
            # BUG FIX: the original code returned the raw exception message
            # (f"Database connectivity error: {exc}") straight to the browser. That can leak
            # internal details (host names, table/column names, driver internals) to anyone
            # who can reach the login page. We log the real error server-side and show the
            # user a generic message instead.
            app.logger.exception("Database error during login")
            error = "We couldn't reach the database right now. Please try again shortly."
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    return render_template("login.html", error=error)


@app.route("/tasks", methods=["GET", "POST"])
def task_management():
    if not is_logged_in():
        return redirect(url_for("login"))

    message = None
    error = None
    employees = []
    tasks = []

    if request.method == "POST":
        employee_id_raw = request.form.get("employee_id", "").strip()
        title = request.form.get("task_title", "").strip()
        completed_raw = request.form.get("completed", "").strip()

        # BUG FIX: the original code validated that employee_id was non-empty, but then
        # called int(employee_id) without a try/except. A non-numeric value (or a value an
        # attacker crafted by hand, since this comes straight from request.form) raised an
        # uncaught ValueError -> HTTP 500, instead of the friendly validation error the rest
        # of the function was designed to show.
        employee_id = None
        if employee_id_raw.isdigit():
            employee_id = int(employee_id_raw)

        if employee_id is None or not title or completed_raw not in ("true", "false"):
            error = "All form fields are required and must be valid."
        else:
            completed = completed_raw == "true"
            conn = None
            cursor = None
            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    """
                    INSERT INTO task (employee_id, title, completed)
                    VALUES (%s, %s, %s)
                    """,
                    (employee_id, title, completed),
                )
                conn.commit()
                message = "Task successfully assigned!"
            except Error:
                app.logger.exception("Database error while inserting task")
                error = "Could not save the task. Please try again."
            finally:
                if cursor:
                    cursor.close()
                if conn and conn.is_connected():
                    conn.close()

        # BUG FIX: previously a successful POST re-rendered the same page directly, which
        # means refreshing the browser after adding a task resubmits the form and creates a
        # duplicate task. We now redirect back to /tasks (Post/Redirect/Get pattern) so a
        # refresh just re-fetches the task list instead of re-posting the form.
        if message:
            return redirect(url_for("task_management"))

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, employee_name, department
            FROM employee
            ORDER BY employee_name
            """
        )
        employees = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                task.id AS id,
                task.title AS title,
                task.completed AS completed,
                DATE_FORMAT(task.created_at, '%b %d, %Y - %h:%i %p') AS created_at,
                employee.employee_name,
                employee.department
            FROM task
            JOIN employee ON employee.id = task.employee_id
            ORDER BY task.id DESC
            """
        )
        tasks = cursor.fetchall()

    except Error:
        app.logger.exception("Database error while loading tasks")
        error = error or "Could not load tasks right now. Please try again."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t["completed"])
    pending_tasks = total_tasks - completed_tasks

    return render_template(
        "tasks.html",
        employees=employees,
        tasks=tasks,
        task_titles=TASK_TITLES,
        message=message,
        error=error,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=FLASK_DEBUG,
        use_reloader=FLASK_DEBUG,
    )
