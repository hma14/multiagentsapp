@echo off

echo Activating virtual environment...
call G:\MultiAgentsApp\backend\app\.venv\Scripts\activate

echo Starting Waitress server...
uvicorn main:app --host ep.lottotry.com --port 8000
pause
