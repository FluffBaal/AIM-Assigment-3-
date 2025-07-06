#!/bin/bash

echo "Starting RAG Chat Application..."

# Check if backend is already running and kill it
EXISTING_BACKEND=$(lsof -ti:8000)
if [ ! -z "$EXISTING_BACKEND" ]; then
    echo "Found existing backend process(es) on port 8000: $EXISTING_BACKEND"
    echo "Stopping existing backend..."
    kill -9 $EXISTING_BACKEND 2>/dev/null
    sleep 2
fi

# Check if frontend is already running and kill it
EXISTING_FRONTEND=$(lsof -ti:5173)
if [ ! -z "$EXISTING_FRONTEND" ]; then
    echo "Found existing frontend process(es) on port 5173: $EXISTING_FRONTEND"
    echo "Stopping existing frontend..."
    kill -9 $EXISTING_FRONTEND 2>/dev/null
    sleep 2
fi

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