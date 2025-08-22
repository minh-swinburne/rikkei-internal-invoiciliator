@echo off
chcp 65001>nul
echo ====================================================
echo    Clean Build Directories
echo ====================================================
echo.

REM Activate virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo 🧹 Cleaning build directories...
python build.py clean

echo ✅ Build directories cleaned!
echo You can now run a fresh build.

pause
