@echo off
setlocal EnableDelayedExpansion

REM Launch script for Python GoldenGate MCP Server (Windows / cmd.exe)
REM Usage: run_goldengate_mcp_server_windows.bat

pushd "%~dp0"
set "ENV_FILE=oracle-goldengate-mcp-server.env"
if not exist "logs" mkdir "logs"
for /f %%T in ('powershell -NoProfile -Command "(Get-Date).ToString('yyyyMMdd_HHmmss')"') do set "RUN_TS=%%T"
set "LOG_FILE=%CD%\logs\run_goldengate_mcp_server_windows_!RUN_TS!.log"

rem Keep only the 10 most recent Windows launcher logs
powershell -NoProfile -Command "Get-ChildItem -Path '%CD%\logs' -Filter 'run_goldengate_mcp_server_windows_*.log' | Sort-Object LastWriteTime -Descending | Select-Object -Skip 10 | Remove-Item -Force -ErrorAction SilentlyContinue" >nul 2>&1

call :log INFO "Log file: !LOG_FILE!"

if exist "%ENV_FILE%" (
  call :log INFO "Loading environment file: %CD%\%ENV_FILE%"
  for /f "usebackq tokens=* delims=" %%i in ("%ENV_FILE%") do (
    set "line=%%i"
    if not "!line!"=="" if not "!line:~0,1!"=="#" set "!line!"
  )
 ) else (
  call :log ERROR "Environment file not found: %CD%\%ENV_FILE%"
  call :log ERROR "Aborting startup. Create the env file from oracle-goldengate-mcp-server.env.empty and set required values."
  popd
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  call :run_and_log "python -m venv .venv"
)

set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
  call :log ERROR "Virtual environment Python not found: %VENV_PYTHON%"
  popd
  exit /b 1
)

call :ensure_supported_python
if errorlevel 1 (
  popd
  exit /b 1
)

set "HAS_VENV_PIP=0"
call :ensure_venv_pip
if not errorlevel 1 (
  set "HAS_VENV_PIP=1"
)

"%VENV_PYTHON%" -c "import oracle.oracle_goldengate_mcp_server.server" >nul 2>&1
if errorlevel 1 (
  if "%HAS_VENV_PIP%"=="1" (
    call :log INFO "Package import check failed, running pip install -e ."
    call :run_and_log ""%VENV_PYTHON%" -m pip install -e ."
    if errorlevel 1 (
      call :log ERROR "pip install failed"
      popd
      exit /b 1
    )
  ) else (
    where uv >nul 2>&1
    if errorlevel 1 (
      call :log WARN "pip is unavailable in virtual environment and uv is not installed."
      call :log WARN "Continuing without dependency auto-install; server startup may fail if dependencies are missing."
      goto :after_dependency_install
    )
    call :log WARN "pip unavailable; using uv to install project dependencies into the virtual environment"
    call :run_and_log "uv pip install --python \"%VENV_PYTHON%\" -e ."
    if errorlevel 1 (
      call :log WARN "uv pip install failed; continuing without dependency auto-install"
    )
  )
) else (
  call :log INFO "Package import check passed, skipping pip install"
)

:after_dependency_install

set "MCP_TRANSPORT=stdio"
set "PYTHONUNBUFFERED=1"
set "GG_MCP_LOG_FILE=!LOG_FILE!"
call :log INFO "Starting GoldenGate MCP server (transport=stdio)"
"%VENV_PYTHON%" -m oracle.oracle_goldengate_mcp_server.server 2> "%TEMP%\gg_mcp_server_err_!RUN_TS!.tmp"
set "RC=%ERRORLEVEL%"
if exist "%TEMP%\gg_mcp_server_err_!RUN_TS!.tmp" (
  for /f "usebackq delims=" %%L in ("%TEMP%\gg_mcp_server_err_!RUN_TS!.tmp") do call :log ERROR "%%L"
  del /q "%TEMP%\gg_mcp_server_err_!RUN_TS!.tmp" >nul 2>&1
)
popd
exit /b %RC%

:ensure_venv_pip
"%VENV_PYTHON%" -m pip --version >nul 2>&1
if not errorlevel 1 (
  call :run_and_log ""%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel"
  if errorlevel 1 (
    call :log WARN "pip exists but tooling upgrade failed; continuing with current pip"
  )
  exit /b 0
)

call :log WARN "pip is missing in virtual environment; attempting bootstrap via ensurepip"
"%VENV_PYTHON%" -m ensurepip --upgrade >nul 2>&1
if errorlevel 1 (
  call :log WARN "Could not bootstrap pip in virtual environment via ensurepip."
  call :log WARN "Attempting virtual environment repair to restore pip availability"

  if exist ".venv" rmdir /s /q ".venv"
  call :run_and_log "python -m venv .venv"

  if not exist "%VENV_PYTHON%" (
    where py >nul 2>&1
    if not errorlevel 1 (
      call :run_and_log "py -3 -m venv .venv"
    )
  )

  if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -m pip --version >nul 2>&1
    if not errorlevel 1 (
      call :log INFO "pip restored after recreating virtual environment"
      exit /b 0
    )
  )

  call :log WARN "Virtual environment repair did not restore pip."
  call :log WARN "Will continue without pip and attempt uv fallback if dependency installation is required."
  exit /b 1
)

call :run_and_log ""%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel"
if errorlevel 1 (
  call :log ERROR "pip bootstrap succeeded but tooling upgrade failed"
  exit /b 1
)
exit /b 0

:ensure_supported_python
"%VENV_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
  exit /b 0
)

for /f %%V in ('"%VENV_PYTHON%" -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"') do set "CURRENT_PY_VER=%%V"
call :log WARN "Virtual environment uses unsupported Python %CURRENT_PY_VER%; project requires >=3.10"
if exist ".venv" rmdir /s /q ".venv"

call :try_create_supported_venv py -3.12 -m venv .venv
if not errorlevel 1 goto :supported_python_ok
call :try_create_supported_venv py -3.11 -m venv .venv
if not errorlevel 1 goto :supported_python_ok
call :try_create_supported_venv py -3.10 -m venv .venv
if not errorlevel 1 goto :supported_python_ok
call :try_create_supported_venv python -m venv .venv
if not errorlevel 1 goto :supported_python_ok

call :log ERROR "Could not find a supported Python interpreter (>=3.10)."
call :log ERROR "Install Python 3.10+ and rerun this launcher."
exit /b 1

:supported_python_ok
for /f %%V in ('"%VENV_PYTHON%" -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"') do set "FIXED_PY_VER=%%V"
call :log INFO "Recreated virtual environment with supported Python %FIXED_PY_VER%"
exit /b 0

:try_create_supported_venv
setlocal
set "CREATE_CMD=%*"
cmd /d /c %CREATE_CMD% >nul 2>&1
if errorlevel 1 (
  endlocal & exit /b 1
)
set "NEW_VENV_PY=%CD%\.venv\Scripts\python.exe"
if not exist "%NEW_VENV_PY%" (
  endlocal & exit /b 1
)
"%NEW_VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
  if exist ".venv" rmdir /s /q ".venv"
  endlocal & exit /b 1
)
endlocal & set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe" & exit /b 0

:run_and_log
setlocal
set "TMPFILE=%TEMP%\gg_mcp_run_%RANDOM%_%RANDOM%.tmp"
cmd /d /c %~1 > "%TMPFILE%" 2>&1
set "CMD_RC=%ERRORLEVEL%"
if exist "%TMPFILE%" (
  for /f "usebackq delims=" %%L in ("%TMPFILE%") do call :log INFO "%%L"
  del /q "%TMPFILE%" >nul 2>&1
)
endlocal & exit /b %CMD_RC%

:log
setlocal EnableDelayedExpansion
set "LOG_LEVEL=%~1"
set "LOG_MSG=%~2"
powershell -NoProfile -Command "$ts=(Get-Date).ToString('yyyy-MM-dd HH:mm:ss'); Add-Content -Path $env:LOG_FILE -Value \"[$ts] [$env:LOG_LEVEL] $env:LOG_MSG\""
endlocal
exit /b 0
