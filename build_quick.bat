@echo off
chcp 65001>nul
echo ====================================================
echo    Quick Build (Executable Only)
echo ====================================================
echo.

REM Activate virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo 🔨 Building executable only...
python build.py build

if %ERRORLEVEL% == 0 (
    echo ✅ Executable built successfully!
    echo 📁 Check the 'dist' folder for InvoiceReconciliator.exe
) else (
    echo ❌ Build failed!
)

pause
