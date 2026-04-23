@echo off
REM One-time setup: installs Python dependencies into the current interpreter.
REM Run this once after cloning, then use run.bat to launch the pipeline.

setlocal
cd /d "%~dp0"
chcp 65001 >nul

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 -m pip install -r requirements.txt
) else (
    python -m pip install -r requirements.txt
)

if not exist ".env" (
    echo OPENAI_API_KEY=> .env
    echo.
    echo Created a blank .env file. Open it and paste your key after OPENAI_API_KEY=.
)

echo.
echo ---------------------------------------------------------------------------
echo   Setup finished (exit code %ERRORLEVEL%).
echo   Next: make sure .env has your OPENAI_API_KEY, then run run.bat.
echo ---------------------------------------------------------------------------
pause >nul
endlocal
