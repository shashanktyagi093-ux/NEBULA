@echo off
cd /d "%~dp0"
echo Starting NEBULA on http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000
python -m uvicorn app:app --host 127.0.0.1 --port 8000
