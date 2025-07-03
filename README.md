# RAG Chat Application

A modern web application that allows users to upload PDF documents and chat with them using RAG (Retrieval-Augmented Generation) technology powered by OpenAI's GPT-4o-mini.

## Features

- 📄 PDF upload and processing
- 💬 Interactive chat interface
- 🔍 RAG-based document retrieval
- 📊 Source citation with metadata
- 🔐 User-provided API key security
- 🚀 Fast and responsive UI

## Tech Stack

- **Backend**: FastAPI, Python 3.11
- **Frontend**: React, TypeScript, Vite
- **AI/ML**: OpenAI API, aimakerspace library
- **Deployment**: Vercel
- **Package Management**: UV (Python), npm (JavaScript)

## Prerequisites

- Python 3.11+
- Node.js 18+
- UV package manager
- OpenAI API key

## Installation

### Backend Setup

1. Install UV:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install dependencies:
```bash
uv sync
```

3. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your configuration
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Development

### Running the Backend

```bash
uv run uvicorn backend.app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Running the Frontend

```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:5173`

## API Documentation

When the backend is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Project Structure

```
.
├── backend/
│   ├── aimakerspace/     # RAG library
│   └── app/              # FastAPI application
├── frontend/             # React application
├── api/                  # Vercel serverless functions
├── uploads/              # PDF upload directory (gitignored)
├── pyproject.toml        # Python dependencies
├── vercel.json           # Vercel configuration
└── README.md
```

## Deployment

This application is configured for deployment on Vercel. See `DEPLOYMENT.md` for detailed instructions.

## Contributing

Please see `MERGE.md` for contribution guidelines and PR process.

## License

This project is private and proprietary.