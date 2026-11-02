@echo off
rem Avvia il configuratore: server su http://127.0.0.1:8000 e apre il browser.
rem Prima volta / dopo modifiche al frontend: esegui "compila_frontend.bat".
cd /d "%~dp0backend"
start "" http://127.0.0.1:8000
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
