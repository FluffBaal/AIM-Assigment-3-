#!/bin/bash

# Development script for RAG Chat Application

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    print_error "UV is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Main menu
echo "RAG Chat Application Development Script"
echo "======================================"
echo "1. Install all dependencies"
echo "2. Run backend server"
echo "3. Run frontend dev server"
echo "4. Run both servers (recommended)"
echo "5. Run backend tests"
echo "6. Run linting"
echo "7. Create production build"
echo "8. Exit"

read -p "Select option (1-8): " choice

case $choice in
    1)
        print_status "Installing Python dependencies..."
        uv sync --extra dev
        
        print_status "Installing frontend dependencies..."
        cd frontend && npm install
        cd ..
        
        print_success "All dependencies installed!"
        ;;
    2)
        print_status "Starting backend server..."
        uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    3)
        print_status "Starting frontend dev server..."
        cd frontend && npm run dev
        ;;
    4)
        print_status "Starting both servers..."
        # Start backend in background
        uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        
        # Give backend time to start
        sleep 3
        
        # Start frontend
        cd frontend && npm run dev &
        FRONTEND_PID=$!
        
        print_success "Servers started!"
        print_status "Backend: http://localhost:8000"
        print_status "Frontend: http://localhost:5173"
        print_status "API Docs: http://localhost:8000/docs"
        
        # Wait for user to stop
        read -p "Press Enter to stop servers..."
        
        # Kill both processes
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
        print_success "Servers stopped"
        ;;
    5)
        print_status "Running backend tests..."
        uv run pytest backend/tests -v
        ;;
    6)
        print_status "Running Python linting..."
        uv run ruff check backend/
        
        print_status "Running Python type checking..."
        uv run mypy backend/
        
        print_status "Running frontend linting..."
        cd frontend && npm run lint
        ;;
    7)
        print_status "Creating production build..."
        cd frontend && npm run build
        print_success "Production build created in frontend/dist"
        ;;
    8)
        print_success "Goodbye!"
        exit 0
        ;;
    *)
        print_error "Invalid option. Please select 1-8."
        ;;
esac