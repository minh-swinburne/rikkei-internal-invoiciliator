@echo off
chcp 65001>nul
echo ====================================================
echo    Invoice Reconciliator Build Script
echo ====================================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please create one with: python -m venv .venv
    echo Then install dependencies with: uv pip install -r requirements.txt
    pause
    exit /b 1
)

echo 🔄 Activating virtual environment...
call .venv\Scripts\activate.bat

echo 🚀 Starting complete build process...
echo.

REM Run the comprehensive build script
python build.py all

echo.
echo ====================================================
if %ERRORLEVEL% == 0 (
    echo ✅ BUILD COMPLETED SUCCESSFULLY!
    echo.
    echo 📁 Check the 'dist' folder for your installer package.
    echo 📄 Distribution files:
    dir dist\*.zip /b 2>nul
    echo.
    echo 🎉 Your Invoice Reconciliator is ready for distribution!
) else (
    echo ❌ BUILD FAILED!
    echo Check the output above for error details.
)
echo ====================================================
pause
