"""
Direct launch file for the Task Management System.

Usage:
    python main.py

This simply imports the configured Flask app from app.py and runs it, so you
have one obvious entry point at the repo root regardless of how app.py itself
is structured.
"""
from app import app, FLASK_DEBUG

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=FLASK_DEBUG,
        use_reloader=FLASK_DEBUG,
    )
