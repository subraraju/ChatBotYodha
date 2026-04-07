#!/bin/bash

# Start backend
cd backend
source venv/bin/activate  # Assuming WSL or bash environment with venv
python -m uvicorn app.main:app --reload --host localhost --port 8000 &
BACKEND_PID=$!

# Start frontend
cd ../frontend
npm install
npm run dev &
FRONTEND_PID=$!

# Wait for both
wait $BACKEND_PID
wait $FRONTEND_PID