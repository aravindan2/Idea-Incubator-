@echo off
setlocal enabledelayedexpansion

REM Move to project root
cd /d "%~dp0\.."

echo [0/6] create venv if missing
if not exist .venv (
    py -3.12 -m venv .venv
)

echo [1/6] activate venv
call .venv\Scripts\activate.bat

echo [2/6] upgrade pip tools
python -m pip install --upgrade pip setuptools wheel

echo [3/6] docker compose up -d
docker compose up -d

echo [4/6] waiting for ClickHouse to be ready

for /L %%i in (1,1,30) do (
    curl -sf http://localhost:8123/ping >nul 2>&1

    if !errorlevel! == 0 (
        echo   ClickHouse ready
        goto :after_wait
    )

    timeout /t 1 >nul
)

:after_wait

echo [5/6] ensure Ollama model
ollama pull llama3.2:1b

echo [6/6] python deps
pip install -r requirements.txt

echo [7/7] seed data + schemas
python -m backend.ingest.seed

echo.
echo ==========================================
echo CortexOS setup complete
echo ==========================================
echo.
echo Run these in separate terminals:
echo.
echo   call .venv\Scripts\activate.bat
echo   uvicorn backend.main:app --reload --port 8000
echo.
echo   call .venv\Scripts\activate.bat
echo   streamlit run frontend/app.py
echo.

pause