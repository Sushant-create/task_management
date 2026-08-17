#!/usr/bin/env bash
# Direct launch script (Linux/macOS).
# Creates a venv on first run, installs dependencies, then starts the app.
set -e

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo "Starting Task Management System on http://127.0.0.1:5000 ..."
python main.py
