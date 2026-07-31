# Task Management System

A small internal tool for admins/managers to log in, assign tasks to employees, and
track completion status. Built with Flask + MySQL.

> **A note on this README's structure:** the standard template for this series of
> projects includes sections like *Dataset Link* and *Model Architecture*, which apply
> to machine learning projects. This is a CRUD web application — there is no dataset
> and no trained model — so those sections are replaced below with the closest
> honest equivalent (*Database Schema* instead of *Dataset*, *System Architecture*
> instead of *Model Architecture*). Nothing here is padded out to force a fit.

## Objective

Give a small team a single place to:
- Restrict access to authenticated admin/manager accounts only (no public signup).
- Assign one of a fixed set of task titles to an employee.
- Track and visualize how many tasks are completed vs. pending.

## Libraries Used

| Library | Purpose |
|---|---|
| Flask 3.0.3 | Web framework / routing / templating |
| mysql-connector-python 9.0.0 | MySQL database driver |
| python-dotenv 1.0.1 | Loads `.env` config into environment variables |
| Werkzeug 3.0.3 | Password hashing (`generate_password_hash` / `check_password_hash`) |
| pytest 8.3.2 | Test suite |

## Database Schema

Three tables, defined in `database.sql`:

- **`login`** — `id, username, password (hashed), role (admin/manager)`
- **`employee`** — `id, employee_name, email, department`
- **`task`** — `id, employee_id (FK → employee.id), title, completed, created_at`

```
login                employee                 task
-----                --------                 ----
id  PK                id  PK                  id  PK
username              employee_name           employee_id  FK -> employee.id
password (hash)       email                   title
role                   department              completed
                                                created_at
```

## Methodology

1. **Auth**: `/` renders the login form and, on POST, looks up the user by
   username, then checks the submitted password against the stored hash with
   `check_password_hash`. Only `admin` and `manager` roles are allowed through.
2. **Session**: on success, `user_id`, `username`, and `role` are stored in the
   Flask session (signed with `app.secret_key`); every `/tasks` request checks
   `is_logged_in()` before doing anything else.
3. **Task assignment**: `/tasks` (GET) loads the employee list and task list from
   MySQL and computes total/completed/pending counts for the dashboard. `/tasks`
   (POST) validates the submitted employee id, task title, and completed flag,
   inserts a row into `task`, then **redirects** back to `/tasks` (Post/Redirect/Get)
   so refreshing the page doesn't resubmit the form.
4. **Logout**: clears the session and redirects to login.

## System Architecture

```
Browser (login.html / tasks.html + style.css + script.js)
        |
        v
Flask app (app.py / main.py)
   - / (GET, POST)      -> login
   - /tasks (GET, POST) -> dashboard + task assignment
   - /logout (GET)      -> clear session
        |
        v
MySQL (task_management_system)
   login | employee | task
```

Config is environment-driven (`.env`, loaded via python-dotenv) with local-dev
fallbacks, so the same code runs locally or in a real deployment without edits.

## Bugs Found & Fixed

| # | Issue | Fix |
|---|---|---|
| 1 | Passwords stored and compared in **plain text** in the `login` table/query. | Switched to `werkzeug.security` hashes; login now uses `check_password_hash`. Seed data in `database.sql` stores hashes, not plaintext. |
| 2 | Hardcoded fallback `app.secret_key` ("task-management-secret-key-2026") committed to source — usable to forge session cookies if `FLASK_SECRET_KEY` isn't set. | Falls back to a random key generated per process (`os.urandom(32)`) instead of a fixed string. |
| 3 | README claimed `debug=False, use_reloader=False`, but `app.py` actually had `debug=True, use_reloader=True` — docs contradicted code, and debug mode should never run in production (it exposes the Werkzeug debugger/RCE risk). | Both are now driven by a `FLASK_DEBUG` env var, defaulting to `False`, so behavior matches the docs. |
| 4 | `int(employee_id)` was called with no `try/except`. A non-numeric value crashed the request with an uncaught `ValueError` (HTTP 500) instead of the intended validation message. | Validated with `.isdigit()` before conversion; invalid input now shows the normal "All fields required" message. |
| 5 | Raw database exceptions (`f"Database error: {exc}"`) were rendered straight to the browser, which can leak internal details (host, schema, driver internals). | Exceptions are logged server-side (`app.logger.exception`); the user sees a generic, safe message. |
| 6 | Successful task assignment re-rendered the same page instead of redirecting, so refreshing the browser resubmitted the form and created duplicate tasks. | Applied the Post/Redirect/Get pattern: a successful insert redirects to `/tasks`. |
| 7 | `templates/`, `static/` and any test files were referenced by `app.py` (`render_template`, `url_for('static', ...)`) but not present in the uploaded project — the app could not actually run. | Built `login.html`, `tasks.html`, `style.css`, `script.js`, and a pytest suite. |
| 8 | No `.env.example`, so anyone cloning the repo had no template for required environment variables. | Added `.env.example`. |

**Not fixed, called out as a known limitation:** there's no CSRF protection on the
forms and no rate-limiting on the login endpoint. For an internal tool behind a
trusted network that's a reasonable trade-off; for anything internet-facing, add
`flask-wtf`'s CSRF protection and a login rate limiter (e.g. `flask-limiter`)
before deploying.

## Results

- All 12 tests in `tests/test_samples.py` pass (mocked DB, no live MySQL needed to
  run them): login success/failure, hashed-password verification, role
  restriction, DB-error handling, session-based route protection, the
  non-numeric-input regression, and the redirect-after-insert regression.
- Manually verified end-to-end against a local MySQL instance seeded from
  `database.sql`: login with both demo accounts, task assignment, dashboard
  counts updating, logout clearing the session.

## Conclusion

The core design (parameterized SQL, role-gated session auth, foreign-key-linked
schema) was already sound and free of SQL injection risk. The real problems were
plaintext password storage, a hardcoded secret key, a docs/code mismatch on debug
mode, an unhandled crash path, and a missing `templates/`/`static/` layer that the
app depended on but didn't ship with. All of those are fixed above; the app now
runs end-to-end and is covered by an automated test suite.

---

## Setup

1. **Create the database:**
   ```sql
   SOURCE database.sql;
   ```
   or import `database.sql` via phpMyAdmin / MySQL Workbench.

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # edit .env with your MySQL credentials and a random FLASK_SECRET_KEY
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the project** (any one of):
   ```bash
   python main.py       # direct launch file
   ./start.sh           # Linux/macOS: creates venv, installs deps, runs
   start.bat            # Windows: creates venv, installs deps, runs
   ```


5. **Run tests:**
   ```bash
   pytest tests/test_samples.py -v
   ```

## Demo Login

- `admin` / `admin123`
- `manager` / `manager123`

(Both are stored as hashes in `database.sql` — see `login` table.)

## Pages

- Login: `/`
- Task dashboard: `/tasks`

## Project Structure

```
task_management/
├── app.py                 # Flask app, routes, DB logic
├── main.py                # Direct launch entry point
├── start.sh / start.bat   # One-command cross-platform launch scripts
├── database.sql           # Schema + seed data (hashed passwords)
├── requirements.txt
├── .env.example
├── .gitignore
├── .gitattributes
├── templates/
│   ├── login.html
│   └── tasks.html
├── static/
│   ├── css/style.css
│   └── js/script.js
└── tests/
    └── test_samples.py
```
