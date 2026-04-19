@echo off
setlocal
cd /d "%~dp0"

git add -A
git diff --cached --quiet
if errorlevel 1 goto :commit
echo No changes to commit.
exit /b 0

:commit
git commit -m "auto-sync"
if errorlevel 1 (
    echo Commit failed.
    exit /b 1
)

git push
if errorlevel 1 (
    echo Push failed.
    exit /b 1
)

echo Pushed to GitHub.
exit /b 0
