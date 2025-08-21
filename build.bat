@echo off
echo Building Invoice Reconciliation Tool Executable...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run the build script
python build_executable.py

echo.
echo Build process completed!
echo Check the 'dist' folder for the executable.
pause
