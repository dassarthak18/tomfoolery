@echo off
setlocal

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    winget install --id Python.Python.3 --source winget
    timeout /t 30 >nul
)

python -m pip install --upgrade pip >nul 2>&1

python -m pip show pygame >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    python -m pip install pygame >nul 2>&1
)

python -m pip show screeninfo >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    python -m pip install screeninfo >nul 2>&1
)

python main.py

endlocal