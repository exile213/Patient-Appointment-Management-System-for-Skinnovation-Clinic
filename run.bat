@echo off
echo ========================================
echo   Starting Skinovation Clinic Server
echo ========================================
echo.

REM Navigate to the correct directory
cd /d "%~dp0"
if not exist "manage.py" (
    echo [ERROR] manage.py not found!
    echo Please make sure you're running this script from the project root folder.
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo [INFO] Virtual environment not found. Using system Python.
    echo If you want to use a virtual environment, run setup.bat first.
)

REM Check if database exists
if not exist db.sqlite3 (
    echo Database not found. Running migrations...
    python manage.py migrate
)

echo Starting development server...
echo.
echo Server will be available at: http://127.0.0.1:8000
echo Admin panel: http://127.0.0.1:8000/admin
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver

pause

