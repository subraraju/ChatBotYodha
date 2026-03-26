@echo off
cd /d E:\Mallikarjun_workspace\chatbot_yodha\ChatBotYodha\backend
E:\Mallikarjun_workspace\chatbot_yodha\ChatBotYodha\backend\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host localhost --port 8000
pause
