@echo off
REM Future Weavers PoC launcher.
REM Double-click this file (or run it from Explorer) to start the pipeline.
REM Window stays open after the run so you can read the last output.

setlocal
cd /d "%~dp0"

REM Switch the console to UTF-8 so em-dashes, curly quotes, etc. render.
chcp 65001 >nul

REM Prefer `py -3` (the Python launcher that ships with Windows), fall back to `python`.
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 poc.py
) else (
    python poc.py
)

echo.
echo ---------------------------------------------------------------------------
echo   Run finished (exit code %ERRORLEVEL%). Press any key to close this window.
echo ---------------------------------------------------------------------------
pause >nul
endlocal
