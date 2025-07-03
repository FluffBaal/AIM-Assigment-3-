# Environment Setup Guide

This guide covers setting up the development environment for the RAG Chat Application.

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Git

## Backend Setup

### 1. Install UV (Python Package Manager)

UV is a fast Python package manager that replaces pip, pip-tools, pipx, poetry, pyenv, and virtualenv.

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone Repository

```bash
git clone https://github.com/FluffBaal/AIM-Assigment-3-.git
cd AIM-Assigment-3-
```

### 3. Set Up Python Environment

```bash
# UV automatically creates and manages virtual environments
cd backend
uv sync
```

### 4. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` if needed (optional - users provide API keys through UI):
```
# Optional: Set default OpenAI API key for development
OPENAI_API_KEY=your-key-here
```

### 5. Run Backend Development Server

```bash
uv run uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Run Frontend Development Server

```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## Development Workflow

### 1. Running Both Servers

You'll need two terminal windows:

**Terminal 1 - Backend:**
```bash
cd backend
uv run uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 2. API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Testing

**Backend Tests:**
```bash
cd backend
uv run pytest
```

**Frontend Tests:**
```bash
cd frontend
npm test
```

### 4. Linting and Formatting

**Backend:**
```bash
cd backend
uv run ruff check .
uv run ruff format .
uv run mypy .
```

**Frontend:**
```bash
cd frontend
npm run lint
npm run format
```

## Common Issues

### UV Installation Issues

If UV installation fails:
1. Ensure you have Python 3.11+ installed
2. Try using pip: `pip install uv`
3. Check [UV documentation](https://docs.astral.sh/uv/)

### Port Already in Use

If ports 8000 or 5173 are in use:

**Backend - use different port:**
```bash
uv run uvicorn app.main:app --reload --port 8001
```

**Frontend - update vite.config.ts:**
```typescript
server: {
  port: 5174,
  proxy: {
    '/api': {
      target: 'http://localhost:8001',
    }
  }
}
```

### Module Import Errors

If you get import errors:
1. Ensure you're in the correct directory
2. Verify UV has installed dependencies: `uv sync`
3. Check Python version: `python --version`

### CORS Errors in Development

The backend is configured to accept requests from:
- http://localhost:5173 (Vite default)
- http://localhost:3000 (alternate)

If using different ports, update `backend/app/core/config.py`.

## Environment Variables

### Backend Environment Variables

Create `backend/.env`:
```
# Optional - for development only
OPENAI_API_KEY=sk-...

# App Configuration
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000

# File Upload
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIR=uploads

# Vector Database
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=text-embedding-3-small

# Chat Configuration
CHAT_MODEL=gpt-4o-mini
MAX_TOKENS=2000
TEMPERATURE=0.7
```

### Frontend Environment Variables

Frontend uses Vite's environment variable system. Create `frontend/.env.local`:
```
# API endpoint (optional - defaults to proxy)
VITE_API_URL=http://localhost:8000
```

## VS Code Setup (Optional)

### Recommended Extensions

Create `.vscode/extensions.json`:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss"
  ]
}
```

### Workspace Settings

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.formatting.provider": "none",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  }
}
```

## Production Deployment

For production deployment to Vercel, see [DEPLOYMENT.md](./DEPLOYMENT.md).

## Getting Help

1. Check existing issues on GitHub
2. Review API documentation at `/docs`
3. Ensure all prerequisites are installed
4. Verify environment variables are set correctly