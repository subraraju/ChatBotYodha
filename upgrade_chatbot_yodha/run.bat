@echo off
echo === ChatBot Yodha v2 — Quick Start ===
echo.
echo Starting PostgreSQL + Backend + Frontend via Docker Compose...
echo.

if not exist .env (
    echo [!] .env not found — copying from .env.example
    copy .env.example .env
    echo [!] Please edit .env with your credentials, then re-run.
    pause
    exit /b 1
)

docker compose up --build
