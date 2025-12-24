@echo off
cd /d C:\Users\tydaw\ai_assistant
C:\Users\tydaw\ai_assistant\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
