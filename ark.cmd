@echo off
setlocal

set "MINI_ARK_HOME=%~dp0"
set "MINI_ARK_PY=C:\Users\Junior\AppData\Local\Python\pythoncore-3.14-64\python.exe"

if exist "%MINI_ARK_PY%" (
  "%MINI_ARK_PY%" "%MINI_ARK_HOME%ark.py" %*
  exit /b %ERRORLEVEL%
)

if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
  "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" "%MINI_ARK_HOME%ark.py" %*
  exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%MINI_ARK_HOME%ark.py" %*
  exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if not errorlevel 1 (
  python "%MINI_ARK_HOME%ark.py" %*
  exit /b %ERRORLEVEL%
)

echo Mini ARK could not find Python.
echo Expected: C:\Users\Junior\AppData\Local\Python\pythoncore-3.14-64\python.exe
echo If Python moved, update C:\mini_ark\ark.cmd.
exit /b 1
