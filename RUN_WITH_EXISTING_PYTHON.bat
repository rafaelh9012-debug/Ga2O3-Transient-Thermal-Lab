@echo off
setlocal
cd /d "%~dp0"
title Ga2O3 Transient Thermal Lab - RafaelDaSquidman
echo ================================================================
echo  Ga2O3 Transient Thermal Lab ^| RafaelDaSquidman
echo  Use existing Python - no Python installer - no custom EXE
echo ================================================================
echo.
py -3 -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp0START_APP.py"
  goto finished
)
python -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if not errorlevel 1 (
  python "%~dp0START_APP.py"
  goto finished
)
python3 -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if not errorlevel 1 (
  python3 "%~dp0START_APP.py"
  goto finished
)
echo No usable Python 3.11+ was found on your command-line PATH.
echo If you use Spyder or Anaconda, open START_APP.py in that IDE and click Run.
echo This launcher will never attempt to install Python.
:finished
echo.
echo Launcher finished. Press any key to close.
pause >nul
endlocal
