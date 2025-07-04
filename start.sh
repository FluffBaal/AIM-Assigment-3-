#!/bin/bash

echo "Starting RAG Chat Application..."

# Start backend server in background
echo "Starting backend server..."
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend server
echo "Starting frontend server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🚀 Application is running!"
echo "Backend API: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait