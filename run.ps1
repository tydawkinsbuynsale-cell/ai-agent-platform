# Stop on errors
$ErrorActionPreference = "Stop"

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Bootstrap
python bootstrap.py

# Start API
uvicorn app:app --host 0.0.0.0 --port 8000
