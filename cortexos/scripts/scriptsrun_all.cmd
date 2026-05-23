@echo off
setlocal enabledelayedexpansion

REM Move to project root
cd /d "%~dp0\.."

echo [1/5] docker compose up -d
docker compose up -d

echo [2/5] waiting for ClickHouse to be ready

set READY=0

for /L %%i in (1,1,30) do (
    curl -sf http://localhost:8123/ping >nul 2>&1

    if !errorlevel! == 0 (
        echo   ClickHouse ready
        set READY=1
        goto :after_wait
    )

    timeout /t 1 >nul
)

:after_wait

echo [3/5] ensure Ollama model
ollama pull llama3.2:1b

echo [4/5] python deps
python -m pip install -q -r requirements.txt

echo [5/5] seed data + schemas
python -m backend.ingest.seed

echo.
echo Now run these in separate terminals:
echo.
echo   uvicorn backend.main:app --reload --port 8000
echo   streamlit run frontend/app.py

pause