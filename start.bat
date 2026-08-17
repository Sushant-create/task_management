@echo off
REM Direct launch script (Windows).
REM Creates a venv on first run, installs dependencies, then starts the app.

cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo Starting Task Management System on http://127.0.0.1:5000 ...
python main.py
