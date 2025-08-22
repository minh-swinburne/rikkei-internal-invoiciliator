@echo off
chcp 65001>nul
echo ====================================================
echo    Check Build Dependencies
echo ====================================================
echo.

REM Activate virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please create one with: python -m venv .venv
    echo Then install dependencies with: uv pip install -r requirements.txt
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo 🔍 Checking build dependencies and assets...
python build.py check

if %ERRORLEVEL% == 0 (
    echo ✅ All dependencies and assets are ready for build!
    echo You can now run: build.bat
) else (
    echo ❌ Some dependencies or assets are missing!
    echo Please install missing packages or check asset files.
)

pause
