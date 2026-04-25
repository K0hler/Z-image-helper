@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [setup] Creating virtual environment...
    py -3.12 -m venv .venv
    if errorlevel 1 goto :error

    echo [setup] Installing dependencies...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto :error
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

echo [run] Starting Streamlit app...
".venv\Scripts\python.exe" -m streamlit run app.py
goto :eof

:error
echo.
echo [error] Project startup failed.
exit /b 1
